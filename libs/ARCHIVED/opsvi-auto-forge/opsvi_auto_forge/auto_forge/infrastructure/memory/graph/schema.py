"""Neo4j schema management for the autonomous software factory."""

import logging
from pathlib import Path
from typing import Any, Dict

from .client import Neo4jClient

logger = logging.getLogger(__name__)


async def create_constraints(client: Neo4jClient) -> None:
    """Create all constraints for the graph database."""
    constraints = [
        "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT run_id_unique IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT result_id_unique IF NOT EXISTS FOR (r:Result) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT critique_id_unique IF NOT EXISTS FOR (c:Critique) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT artifact_hash_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.hash IS UNIQUE",
    ]

    for constraint in constraints:
        try:
            await client.execute_write_query(constraint)
            logger.info(f"Created constraint: {constraint}")
        except Exception as e:
            logger.warning(f"Failed to create constraint {constraint}: {e}")


async def create_indexes(client: Neo4jClient) -> None:
    """Create all indexes for the graph database."""
    indexes = [
        # Project indexes
        "CREATE INDEX project_name_index IF NOT EXISTS FOR (p:Project) ON (p.name)",
        "CREATE INDEX project_status_index IF NOT EXISTS FOR (p:Project) ON (p.status)",
        "CREATE INDEX project_created_at_index IF NOT EXISTS FOR (p:Project) ON (p.created_at)",
        # Run indexes
        "CREATE INDEX run_project_id_index IF NOT EXISTS FOR (r:Run) ON (r.project_id)",
        "CREATE INDEX run_status_index IF NOT EXISTS FOR (r:Run) ON (r.status)",
        "CREATE INDEX run_started_at_index IF NOT EXISTS FOR (r:Run) ON (r.started_at)",
        "CREATE INDEX run_pipeline_name_index IF NOT EXISTS FOR (r:Run) ON (r.pipeline_name)",
        # Task indexes
        "CREATE INDEX task_run_id_index IF NOT EXISTS FOR (t:Task) ON (t.run_id)",
        "CREATE INDEX task_agent_index IF NOT EXISTS FOR (t:Task) ON (t.agent)",
        "CREATE INDEX task_status_index IF NOT EXISTS FOR (t:Task) ON (t.status)",
        "CREATE INDEX task_queue_index IF NOT EXISTS FOR (t:Task) ON (t.queue)",
        "CREATE INDEX task_priority_index IF NOT EXISTS FOR (t:Task) ON (t.priority)",
        "CREATE INDEX task_created_at_index IF NOT EXISTS FOR (t:Task) ON (t.created_at)",
        # Artifact indexes
        "CREATE INDEX artifact_task_id_index IF NOT EXISTS FOR (a:Artifact) ON (a.task_id)",
        "CREATE INDEX artifact_type_index IF NOT EXISTS FOR (a:Artifact) ON (a.type)",
        "CREATE INDEX artifact_path_index IF NOT EXISTS FOR (a:Artifact) ON (a.path)",
        # Result indexes
        "CREATE INDEX result_task_id_index IF NOT EXISTS FOR (r:Result) ON (r.task_id)",
        "CREATE INDEX result_status_index IF NOT EXISTS FOR (r:Result) ON (r.status)",
        "CREATE INDEX result_score_index IF NOT EXISTS FOR (r:Result) ON (r.score)",
        # Critique indexes
        "CREATE INDEX critique_task_id_index IF NOT EXISTS FOR (c:Critique) ON (c.task_id)",
        "CREATE INDEX critique_agent_id_index IF NOT EXISTS FOR (c:Critique) ON (c.agent_id)",
        "CREATE INDEX critique_score_index IF NOT EXISTS FOR (c:Critique) ON (c.score)",
        # Decision indexes
        "CREATE INDEX decision_task_id_index IF NOT EXISTS FOR (d:Decision) ON (d.task_id)",
        "CREATE INDEX decision_agent_index IF NOT EXISTS FOR (d:Decision) ON (d.by_agent)",
        "CREATE INDEX decision_confidence_index IF NOT EXISTS FOR (d:Decision) ON (d.confidence)",
        # Composite indexes
        "CREATE INDEX task_agent_status_index IF NOT EXISTS FOR (t:Task) ON (t.agent, t.status)",
        "CREATE INDEX task_run_status_index IF NOT EXISTS FOR (t:Task) ON (t.run_id, t.status)",
        "CREATE INDEX run_project_status_index IF NOT EXISTS FOR (r:Run) ON (r.project_id, r.status)",
        # Relationship type lookup index for Neo4j 5.x (only one allowed)
        "CREATE LOOKUP INDEX rel_type_lookup IF NOT EXISTS FOR ()-[r]-() ON EACH type(r)",
    ]

    for index in indexes:
        try:
            await client.execute_write_query(index)
            logger.info(f"Created index: {index}")
        except Exception as e:
            logger.warning(f"Failed to create index {index}: {e}")


async def create_fulltext_indexes(client: Neo4jClient) -> None:
    """Create fulltext search indexes (requires APOC plugin)."""
    # For Neo4j 5.x, use the built-in fulltext index syntax
    fulltext_indexes = [
        "CREATE FULLTEXT INDEX project_search IF NOT EXISTS FOR (n:Project) ON EACH [n.name, n.description, n.requirements]",
        "CREATE FULLTEXT INDEX task_search IF NOT EXISTS FOR (n:Task) ON EACH [n.name, n.inputs, n.outputs]",
        "CREATE FULLTEXT INDEX decision_search IF NOT EXISTS FOR (n:Decision) ON EACH [n.why, n.params]",
    ]

    for index in fulltext_indexes:
        try:
            await client.execute_write_query(index)
            logger.info(f"Created fulltext index: {index}")
        except Exception as e:
            logger.warning(f"Failed to create fulltext index {index}: {e}")


async def setup_schema(client: Neo4jClient) -> None:
    """Set up complete schema for the autonomous software factory."""
    logger.info("Setting up Neo4j schema...")

    try:
        # Create constraints first
        await create_constraints(client)

        # Create indexes
        await create_indexes(client)

        # Create fulltext indexes (optional, requires APOC)
        await create_fulltext_indexes(client)

        logger.info("Neo4j schema setup completed successfully")

    except Exception as e:
        logger.error(f"Failed to set up Neo4j schema: {e}")
        raise


async def load_schema_from_file(client: Neo4jClient, schema_file: str) -> None:
    """Load schema from a Cypher file."""
    schema_path = Path(schema_file)

    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_file}")
        return

    try:
        with open(schema_path, "r") as f:
            schema_content = f.read()

        # Split by semicolon and execute each statement
        statements = [
            stmt.strip() for stmt in schema_content.split(";") if stmt.strip()
        ]

        for statement in statements:
            if statement and not statement.startswith("--"):
                try:
                    await client.execute_write_query(statement)
                    logger.info(f"Executed schema statement: {statement[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to execute schema statement: {e}")

        logger.info(f"Loaded schema from file: {schema_file}")

    except Exception as e:
        logger.error(f"Failed to load schema from file {schema_file}: {e}")
        raise


async def verify_schema(client: Neo4jClient) -> Dict[str, Any]:
    """Verify that all required schema elements exist."""
    verification_queries = {
        "constraints": "SHOW CONSTRAINTS",
        "indexes": "SHOW INDEXES",
        "node_labels": "CALL db.labels() YIELD label RETURN collect(label) as labels",
        "relationship_types": "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types",
    }

    results = {}

    for name, query in verification_queries.items():
        try:
            result = await client.execute_query(query)
            results[name] = result
            logger.info(f"Verified {name}: {len(result)} items found")
        except Exception as e:
            logger.warning(f"Failed to verify {name}: {e}")
            results[name] = []

    return results
