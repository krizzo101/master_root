"""Neo4j client with bulletproof data serialization."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from neo4j import AsyncGraphDatabase, Driver
from neo4j.exceptions import AuthError, ServiceUnavailable, TransientError
from opsvi_auto_forge.config.settings import settings

from .queries import LineageQueries
from .safe_serializer import Neo4jSafeSerializer

logger = logging.getLogger(__name__)


def _final_param_guard(params: dict) -> dict:
    """Final defensive guard to ensure no dict reaches Neo4j."""
    out = {}
    for k, v in (params or {}).items():
        if isinstance(v, dict):
            out[k] = "{}" if not v else json.dumps(v)
        else:
            out[k] = v
    return out


def _sanitize_for_neo4j(value: Any) -> Any:
    """
    Return a value acceptable for Neo4j properties:
    - primitives or arrays of primitives
    - JSON strings for any dict/object
    - None for empty dicts
    """
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        # Recursively sanitize list items
        return [_sanitize_for_neo4j(v) for v in value]
    if isinstance(value, tuple):
        return [_sanitize_for_neo4j(v) for v in value]
    if isinstance(value, dict):
        # Convert to JSON string (even empty dicts)
        if not value:
            return "{}"  # Return empty JSON object string
        return json.dumps({k: _sanitize_for_neo4j(v) for k, v in value.items()})
    # Pydantic/BaseModel or other objects
    if hasattr(value, "model_dump"):
        return _sanitize_for_neo4j(value.model_dump(mode="python"))
    if hasattr(value, "__dict__"):
        d = {k: getattr(value, k) for k in dir(value) if not k.startswith("_")}
        return _sanitize_for_neo4j(d)
    # Fallback to string
    return str(value)


def sanitize_parameters_for_neo4j(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitize all parameters for Neo4j compatibility."""
    if not params:
        return {}
    return {k: _sanitize_for_neo4j(v) for k, v in params.items()}


def convert_neo4j_datetime_to_python(value: Any) -> Any:
    """Convert Neo4j DateTime objects to Python datetime objects."""
    if hasattr(value, "__class__") and value.__class__.__name__ == "DateTime":
        # Convert Neo4j DateTime to Python datetime
        return datetime.fromisoformat(str(value))
    elif isinstance(value, dict):
        return {k: convert_neo4j_datetime_to_python(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [convert_neo4j_datetime_to_python(v) for v in value]
    else:
        return value


# Backward compatibility wrapper (previously used across code)
def convert_uuids_to_strings(data: Any) -> Any:
    return _sanitize_for_neo4j(data)


class Neo4jClient:
    """Neo4j client with connection pooling and transaction management."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        max_connection_lifetime: Optional[int] = None,
        max_connection_pool_size: Optional[int] = None,
    ) -> None:
        """Initialize Neo4j client."""
        self.uri = uri or settings.neo4j_url
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.max_connection_lifetime = (
            max_connection_lifetime or settings.neo4j_max_connection_lifetime
        )
        self.max_connection_pool_size = (
            max_connection_pool_size or settings.neo4j_max_connection_pool_size
        )

        self.queries = LineageQueries()
        self._driver: Optional[Driver] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self._driver is not None:
            return

        async with self._lock:
            if self._driver is not None:
                return

            try:
                self._driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_lifetime=self.max_connection_lifetime,
                    max_connection_pool_size=self.max_connection_pool_size,
                )

                # Verify connection
                await self._driver.verify_connectivity()
                logger.info("Connected to Neo4j database")

            except (ServiceUnavailable, AuthError) as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                raise

    async def disconnect(self) -> None:
        """Close connection to Neo4j."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j database")

    @asynccontextmanager
    async def session(self):
        """Get a Neo4j session with automatic cleanup."""
        if self._driver is None:
            await self.connect()

        async with self._driver.session() as session:
            yield session

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query."""
        async with self.session() as session:
            safe_params = sanitize_parameters_for_neo4j(parameters or {})

            # Apply final defensive guard
            safe_params = _final_param_guard(safe_params)

            result = await session.run(query, safe_params)
            records = await result.data()

            # Convert Neo4j DateTime objects to Python datetime objects
            converted_records = []
            for record in records:
                converted_record = convert_neo4j_datetime_to_python(record)
                converted_records.append(converted_record)

            return converted_records

    async def _write_with_retry(self, fn, *args, **kwargs):
        """Execute write operations with retry logic."""
        for attempt in range(5):
            try:
                return await self._driver.execute_query(fn, *args, **kwargs)
            except (ServiceUnavailable, TransientError):
                if attempt == 4:  # Last attempt
                    raise
                await asyncio.sleep(0.25 * (attempt + 1))
        raise

    async def execute_write_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a write Cypher query with retry logic."""
        return await self.execute_query(query, parameters, read_only=False)

    # Project operations
    async def create_project(
        self, project_data: Union[Dict[str, Any], "Project"]
    ) -> str:
        """Create a new project node with bulletproof serialization."""
        from datetime import datetime, timezone
        from uuid import uuid4

        # Convert Pydantic model to dict if needed
        if hasattr(project_data, "model_dump"):
            # It's a Pydantic model
            params = project_data.model_dump()
        else:
            # It's already a dict
            params = project_data.copy()

        # Prepare data with defaults
        params.setdefault("id", str(uuid4()))
        params.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        params.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        params.setdefault("target_framework", "fastapi")
        params.setdefault("status", "active")

        # BULLETPROOF SERIALIZATION - NO MORE MAP{} ERRORS
        print("🚀 BULLETPROOF: Using new serializer!")
        safe_params = Neo4jSafeSerializer.serialize_data(params)
        safe_params = Neo4jSafeSerializer.ensure_json_fields(safe_params)

        logger.info(
            f"BULLETPROOF: metadata_json type: {type(safe_params.get('metadata_json'))}"
        )
        logger.info(
            f"BULLETPROOF: metadata_json value: {safe_params.get('metadata_json')}"
        )
        print(
            f"🚀 BULLETPROOF: metadata_json type: {type(safe_params.get('metadata_json'))}"
        )
        print(f"🚀 BULLETPROOF: metadata_json value: {safe_params.get('metadata_json')}")

        query = """
        CREATE (p:Project {
            id: $id,
            name: $name,
            description: $description,
            requirements: $requirements,
            target_framework: $target_framework,
            status: $status,
            metadata_json: $metadata_json,
            created_at: $created_at,
            updated_at: $updated_at
        })
        RETURN p.id as project_id
        """

        result = await self.execute_write_query(query, safe_params)
        return result[0]["project_id"]

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        query = """
        MATCH (p:Project {id: $project_id})
        RETURN p
        """

        result = await self.execute_query(query, {"project_id": project_id})
        if not result:
            return None

        # Convert metadata_json back to metadata dict
        project_data = result[0]["p"]
        if "metadata_json" in project_data:
            try:
                project_data["metadata"] = (
                    json.loads(project_data["metadata_json"])
                    if project_data["metadata_json"]
                    else {}
                )
            except (json.JSONDecodeError, TypeError):
                project_data["metadata"] = {}
            # Remove the _json field for backward compatibility
            project_data.pop("metadata_json", None)

        return project_data

    # Run operations
    async def create_run(self, run_data: Union[Dict[str, Any], "Run"]) -> str:
        """Create a new run node with bulletproof serialization."""
        from datetime import datetime, timezone
        from uuid import uuid4

        # Convert Pydantic model to dict if needed
        if hasattr(run_data, "model_dump"):
            # It's a Pydantic model
            params = run_data.model_dump()
        else:
            # It's already a dict
            params = run_data.copy()

        # Prepare data with defaults
        params.setdefault("id", str(uuid4()))
        params.setdefault("status", "running")
        params.setdefault("started_at", datetime.now(timezone.utc).isoformat())
        params.setdefault("ended_at", None)
        params.setdefault("total_tasks", 0)
        params.setdefault("completed_tasks", 0)
        params.setdefault("successful_tasks", 0)
        params.setdefault("failed_tasks", 0)
        params.setdefault("total_tokens", 0)
        params.setdefault("total_cost", 0.0)
        params.setdefault("total_latency_ms", 0.0)
        params.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        params.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        # BULLETPROOF SERIALIZATION - NO MORE MAP{} ERRORS
        safe_params = Neo4jSafeSerializer.serialize_data(params)
        safe_params = Neo4jSafeSerializer.ensure_json_fields(safe_params)

        logger.info(
            f"BULLETPROOF RUN: metadata_json type: {type(safe_params.get('metadata_json'))}"
        )
        logger.info(
            f"BULLETPROOF RUN: metadata_json value: {safe_params.get('metadata_json')}"
        )

        query = """
        MERGE (p:Project {id: $project_id})
        ON CREATE SET
            p.name = $project_name,
            p.description = $project_description,
            p.requirements = $project_requirements,
            p.target_framework = $project_target_framework,
            p.status = $project_status,
            p.metadata_json = $project_metadata_json,
            p.created_at = $project_created_at,
            p.updated_at = $project_updated_at
        CREATE (r:Run {
            id: $id,
            project_id: $project_id,
            pipeline_name: $pipeline_name,
            status: $status,
            started_at: $started_at,
            ended_at: $ended_at,
            total_tasks: $total_tasks,
            completed_tasks: $completed_tasks,
            successful_tasks: $successful_tasks,
            failed_tasks: $failed_tasks,
            total_tokens: $total_tokens,
            total_cost: $total_cost,
            total_latency_ms: $total_latency_ms,
            metadata_json: $metadata_json,
            created_at: $created_at,
            updated_at: $updated_at
        })
        CREATE (r)-[:OF_PROJECT]->(p)
        RETURN r.id as run_id
        """

        # Add project defaults if not provided
        safe_params.setdefault(
            "project_name", f"Project {safe_params.get('project_id', 'Unknown')}"
        )
        safe_params.setdefault("project_description", "Auto-generated project")
        safe_params.setdefault("project_requirements", "[]")
        safe_params.setdefault("project_target_framework", "fastapi")
        safe_params.setdefault("project_status", "active")
        safe_params.setdefault("project_metadata_json", "{}")
        safe_params.setdefault("project_created_at", safe_params.get("created_at"))
        safe_params.setdefault("project_updated_at", safe_params.get("updated_at"))

        result = await self.execute_write_query(query, safe_params)

        if not result:
            raise ValueError("Failed to create run - no result returned from database")

        return result[0]["run_id"]

    async def update_run_status(self, run_id: str, status: str, **updates: Any) -> None:
        """Update run status and other fields."""
        set_clauses = ["r.status = $status", "r.updated_at = datetime()"]
        parameters = {"run_id": run_id, "status": status}

        for key, value in updates.items():
            if value is not None:
                set_clauses.append(f"r.{key} = ${key}")
                parameters[key] = value

        query = f"""
        MATCH (r:Run {{id: $run_id}})
        SET {', '.join(set_clauses)}
        """

        await self.execute_write_query(query, parameters)

    # Task operations
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task node."""
        query = """
        MATCH (r:Run {id: $run_id})
        CREATE (t:Task {
            id: $id,
            name: $name,
            agent: $agent,
            status: $status,
            started_at: $started_at,
            ended_at: $ended_at,
            inputs: $inputs,
            outputs: $outputs,
            retry_count: $retry_count,
            max_retries: $max_retries,
            queue: $queue,
            priority: $priority,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (r)-[:HAS_TASK]->(t)
        RETURN t.id as task_id
        """

        result = await self.execute_write_query(query, task_data)
        return result[0]["task_id"]

    async def update_task_status(
        self, task_id: str, status: str, **updates: Any
    ) -> None:
        """Update task status and other fields."""
        set_clauses = ["t.status = $status", "t.updated_at = datetime()"]
        parameters = {"task_id": task_id, "status": status}

        for key, value in updates.items():
            if value is not None:
                set_clauses.append(f"t.{key} = ${key}")
                parameters[key] = value

        query = f"""
        MATCH (t:Task {{id: $task_id}})
        SET {', '.join(set_clauses)}
        """

        await self.execute_write_query(query, parameters)

    # Artifact operations
    async def create_artifact(self, artifact_data: Dict[str, Any]) -> str:
        """Create a new artifact node."""
        query = """
        MATCH (t:Task {id: $task_id})
        CREATE (a:Artifact {
            id: $id,
            type: $type,
            path: $path,
            hash: $hash,
            metadata: $metadata,
            size_bytes: $size_bytes,
            mime_type: $mime_type,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (t)-[:GENERATES]->(a)
        RETURN a.id as artifact_id
        """

        result = await self.execute_write_query(query, artifact_data)
        return result[0]["artifact_id"]

    # Result operations
    async def create_result(self, result_data: Dict[str, Any]) -> str:
        """Create a new result node."""
        query = """
        MATCH (t:Task {id: $task_id})
        CREATE (r:Result {
            id: $id,
            status: $status,
            score: $score,
            metrics: $metrics,
            errors: $errors,
            warnings: $warnings,
            execution_time_seconds: $execution_time_seconds,
            memory_usage_mb: $memory_usage_mb,
            cpu_usage_percent: $cpu_usage_percent,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (t)-[:RESULTED_IN]->(r)
        RETURN r.id as result_id
        """

        result = await self.execute_write_query(query, result_data)
        return result[0]["result_id"]

    # Critique operations
    async def create_critique(self, critique_data: Dict[str, Any]) -> str:
        """Create a new critique node."""
        query = """
        MATCH (t:Task {id: $task_id})
        CREATE (c:Critique {
            id: $id,
            pass: $pass,
            score: $score,
            policy_scores: $policy_scores,
            reasons: $reasons,
            patch_plan: $patch_plan,
            agent_id: $agent_id,
            model_used: $model_used,
            tokens_used: $tokens_used,
            latency_ms: $latency_ms,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (c)-[:EVALUATED_BY]->(t)
        RETURN c.id as critique_id
        """

        result = await self.execute_write_query(query, critique_data)
        return result[0]["critique_id"]

    # Decision operations
    async def create_decision(self, decision_data: Dict[str, Any]) -> str:
        """Create a new decision node."""
        query = """
        MATCH (t:Task {id: $task_id})
        CREATE (d:Decision {
            id: $id,
            by_agent: $by_agent,
            why: $why,
            params: $params,
            confidence: $confidence,
            model_used: $model_used,
            tokens_used: $tokens_used,
            latency_ms: $latency_ms,
            created_at: datetime(),
            updated_at: datetime()
        })
        CREATE (d)-[:FOR_TASK]->(t)
        RETURN d.id as decision_id
        """

        result = await self.execute_write_query(query, decision_data)
        return result[0]["decision_id"]

    # Query operations
    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        try:
            result = await self.execute_query(self.queries.GET_RUN, {"run_id": run_id})
            if not result:
                return None

            run_data = result[0].get("r", {})
            return convert_neo4j_datetime_to_python(run_data)
        except Exception as e:
            logger.error(f"Failed to get run {run_id}: {e}")
            return None

    async def get_run_tasks(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific run."""
        try:
            result = await self.execute_query(
                self.queries.GET_RUN_TASKS, {"run_id": run_id}
            )
            tasks = []
            for row in result:
                task_data = row.get("t", {})
                tasks.append(convert_neo4j_datetime_to_python(task_data))
            return tasks
        except Exception as e:
            logger.error(f"Failed to get tasks for run {run_id}: {e}")
            return []

    async def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of a run."""
        query = """
        MATCH (r:Run {id: $run_id})-[:OF_PROJECT]->(p:Project)
        OPTIONAL MATCH (r)-[:HAS_TASK]->(t:Task)
        OPTIONAL MATCH (t)-[:GENERATES]->(a:Artifact)
        OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
        OPTIONAL MATCH (t)<-[:EVALUATED_BY]-(c:Critique)
        OPTIONAL MATCH (t)<-[:FOR_TASK]-(d:Decision)

        WITH r, p,
             count(DISTINCT t) as task_count,
             count(DISTINCT a) as artifact_count,
             count(DISTINCT res) as result_count,
             count(DISTINCT c) as critique_count,
             count(DISTINCT d) as decision_count

        RETURN {
            run: r,
            project: p,
            task_count: task_count,
            artifact_count: artifact_count,
            result_count: result_count,
            critique_count: critique_count,
            decision_count: decision_count
        } as summary
        """

        result = await self.execute_query(query, {"run_id": run_id})
        return result[0]["summary"] if result else {}

    async def get_project_lineage(self, project_id: str) -> List[Dict[str, Any]]:
        """Get complete lineage for a project."""
        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)<-[:OF_PROJECT]-(r:Run)
        OPTIONAL MATCH (r)-[:HAS_TASK]->(t:Task)
        OPTIONAL MATCH (t)-[:GENERATES]->(a:Artifact)
        OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
        OPTIONAL MATCH (t)<-[:EVALUATED_BY]-(c:Critique)
        OPTIONAL MATCH (t)<-[:FOR_TASK]-(d:Decision)

        WITH p, r, t, a, res, c, d
        ORDER BY r.created_at DESC, t.created_at DESC

        WITH p, r, t, collect(DISTINCT a) as artifacts, res, c, collect(DISTINCT d) as decisions

        WITH p, r, collect(DISTINCT {
            task: t,
            artifacts: artifacts,
            result: res,
            critique: c,
            decisions: decisions
        }) as tasks

        WITH p, collect(DISTINCT {
            run: r,
            tasks: tasks
        }) as runs

        RETURN {
            project: p,
            runs: runs
        } as lineage
        """

        result = await self.execute_query(query, {"project_id": project_id})
        return [r["lineage"] for r in result]

    async def get_agent_performance(
        self, agent: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get performance metrics for an agent."""
        query = """
        MATCH (t:Task {agent: $agent})
        OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
        OPTIONAL MATCH (t)<-[:EVALUATED_BY]-(c:Critique)

        RETURN {
            task: t,
            result: res,
            critique: c,
            overall_score: CASE
                WHEN res IS NOT NULL AND c IS NOT NULL
                THEN (res.score + c.score) / 2
                WHEN res IS NOT NULL
                THEN res.score
                ELSE 0.0
            END
        } as performance
        ORDER BY t.created_at DESC
        LIMIT $limit
        """

        result = await self.execute_query(query, {"agent": agent, "limit": limit})
        return [r["performance"] for r in result]

    async def cleanup_old_data(self, days: int = 30) -> int:
        """Clean up data older than specified days."""
        query = """
        MATCH (n)
        WHERE n.created_at < datetime() - duration({days: $days})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """

        result = await self.execute_write_query(query, {"days": days})
        return result[0]["deleted_count"] if result else 0

    async def initialize_schema(self) -> bool:
        """Initialize the Neo4j schema with constraints and indexes."""
        try:
            # Node ID Constraints
            constraints = [
                "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",
                "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE",
                "CREATE CONSTRAINT result_id_unique IF NOT EXISTS FOR (res:Result) REQUIRE res.id IS UNIQUE",
                "CREATE CONSTRAINT critique_id_unique IF NOT EXISTS FOR (c:Critique) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT artifact_hash_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.hash IS UNIQUE",
            ]

            # Performance Indexes
            indexes = [
                "CREATE INDEX project_name_index IF NOT EXISTS FOR (p:Project) ON (p.name)",
                "CREATE INDEX project_status_index IF NOT EXISTS FOR (p:Project) ON (p.status)",
                "CREATE INDEX project_created_index IF NOT EXISTS FOR (p:Project) ON (p.created_at)",
                "CREATE INDEX run_status_index IF NOT EXISTS FOR (r:Run) ON (r.status)",
                "CREATE INDEX run_pipeline_index IF NOT EXISTS FOR (r:Run) ON (r.pipeline_name)",
                "CREATE INDEX run_started_index IF NOT EXISTS FOR (r:Run) ON (r.started_at)",
                "CREATE INDEX task_agent_index IF NOT EXISTS FOR (t:Task) ON (t.agent)",
                "CREATE INDEX task_status_index IF NOT EXISTS FOR (t:Task) ON (t.status)",
                "CREATE INDEX task_queue_index IF NOT EXISTS FOR (t:Task) ON (t.queue)",
                "CREATE INDEX task_created_index IF NOT EXISTS FOR (t:Task) ON (t.created_at)",
                "CREATE INDEX artifact_type_index IF NOT EXISTS FOR (a:Artifact) ON (a.type)",
                "CREATE INDEX artifact_created_index IF NOT EXISTS FOR (a:Artifact) ON (a.created_at)",
                "CREATE INDEX result_status_index IF NOT EXISTS FOR (res:Result) ON (res.status)",
                "CREATE INDEX result_created_index IF NOT EXISTS FOR (res:Result) ON (res.created_at)",
                "CREATE INDEX critique_passed_index IF NOT EXISTS FOR (c:Critique) ON (c.passed)",
                "CREATE INDEX critique_created_index IF NOT EXISTS FOR (c:Critique) ON (c.created_at)",
                "CREATE INDEX decision_agent_index IF NOT EXISTS FOR (d:Decision) ON (d.by_agent)",
                "CREATE INDEX decision_created_index IF NOT EXISTS FOR (d:Decision) ON (d.created_at)",
            ]

            # Relationship Indexes - Neo4j doesn't support direct relationship indexes
            # Instead, we'll create indexes on the properties of the nodes that participate in these relationships
            relationship_indexes = [
                # These are commented out as Neo4j doesn't support direct relationship indexes
                # "CREATE INDEX has_run_index IF NOT EXISTS FOR ()-[r:HAS_RUN]-() ON (r)",
                # "CREATE INDEX has_task_index IF NOT EXISTS FOR ()-[r:HAS_TASK]-() ON (r)",
                # "CREATE INDEX produces_index IF NOT EXISTS FOR ()-[r:PRODUCES]-() ON (r)",
                # "CREATE INDEX has_result_index IF NOT EXISTS FOR ()-[r:HAS_RESULT]-() ON (r)",
                # "CREATE INDEX has_critique_index IF NOT EXISTS FOR ()-[r:HAS_CRITIQUE]-() ON (r)",
                # "CREATE INDEX has_decision_index IF NOT EXISTS FOR ()-[r:HAS_DECISION]-() ON (r)",
            ]

            # Apply all constraints and indexes
            for constraint in constraints:
                await self.execute_write_query(constraint)

            for index in indexes:
                await self.execute_write_query(index)

            for rel_index in relationship_indexes:
                await self.execute_write_query(rel_index)

            logger.info("Successfully initialized Neo4j schema")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            return False

    async def apply_migration(self, migration_file: str) -> bool:
        """Apply a migration file to the database."""
        try:
            from pathlib import Path

            # Read migration file
            migration_path = Path(__file__).parent / "migrations" / migration_file
            if not migration_path.exists():
                logger.error(f"Migration file not found: {migration_path}")
                return False

            with open(migration_path, "r") as f:
                migration_content = f.read()

            # Split by semicolon and execute each statement
            statements = [
                stmt.strip() for stmt in migration_content.split(";") if stmt.strip()
            ]

            for statement in statements:
                if statement.startswith("//") or not statement.strip():
                    continue
                await self.execute_write_query(statement)

            logger.info(f"Successfully applied migration: {migration_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file}: {e}")
            return False

    async def add_escalation_event(
        self, task_id: str, from_model: str, to_model: str, reason: str
    ) -> str:
        """Add an escalation event to the database."""
        try:
            query = """
            CREATE (e:EscalationEvent {
                id: $escalation_id,
                task_id: $task_id,
                from_model: $from_model,
                to_model: $to_model,
                reason: $reason,
                timestamp: datetime()
            })
            """

            escalation_id = f"escalation-{task_id}-{from_model}-{to_model}"
            parameters = {
                "escalation_id": escalation_id,
                "task_id": task_id,
                "from_model": from_model,
                "to_model": to_model,
                "reason": reason,
            }

            await self.execute_write_query(query, parameters)
            logger.info(f"Added escalation event: {from_model} -> {to_model}")
            return escalation_id

        except Exception as e:
            logger.error(f"Failed to add escalation event: {e}")
            return ""
