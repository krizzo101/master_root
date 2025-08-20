"""Neo4j client for graph logging and lineage tracking."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .queries import (
    CREATE_ARTIFACT,
    CREATE_CRITIQUE,
    CREATE_PROJECT,
    CREATE_RESULT,
    CREATE_RUN,
    CREATE_TASK,
    LINK_AGENT_PERFORMS_TASK,
    LINK_ARTIFACT_DERIVED_FROM,
    LINK_ARTIFACT_TASK,
    LINK_TASK_CRITIQUE,
    LINK_TASK_DEPENDENCY,
    LINK_TASK_RESULT,
    LINK_TASK_TO_PROJECT,
    LINK_TASK_TO_RUN,
)

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j client for graph operations."""

    def __init__(self, uri: str, username: str, password: str) -> None:
        """Initialize Neo4j client."""
        self.uri = uri
        self.username = username
        self.password = password
        self._driver = None

    def connect(self) -> None:
        """Connect to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j database")
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise

    def close(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Closed Neo4j connection")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _execute_query(
        self, query: str, parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query."""
        if not self._driver:
            raise RuntimeError("Neo4j client not connected")

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise

    def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a project node."""
        try:
            result = self._execute_query(CREATE_PROJECT, project_data)
            project_id = result[0]["project"]["id"]
            logger.info(f"Created project: {project_id}")
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise

    def create_run(self, run_data: Dict[str, Any]) -> str:
        """Create a run node."""
        try:
            result = self._execute_query(CREATE_RUN, run_data)
            run_id = result[0]["run"]["id"]
            logger.info(f"Created run: {run_id}")
            return run_id
        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            raise

    def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a task node."""
        try:
            result = self._execute_query(CREATE_TASK, task_data)
            task_id = result[0]["task"]["id"]
            logger.info(f"Created task: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    def create_artifact(self, artifact_data: Dict[str, Any]) -> str:
        """Create an artifact node."""
        try:
            result = self._execute_query(CREATE_ARTIFACT, artifact_data)
            artifact_id = result[0]["artifact"]["id"]
            logger.info(f"Created artifact: {artifact_id}")
            return artifact_id
        except Exception as e:
            logger.error(f"Failed to create artifact: {e}")
            raise

    def create_result(self, result_data: Dict[str, Any]) -> str:
        """Create a result node."""
        try:
            result = self._execute_query(CREATE_RESULT, result_data)
            result_id = result[0]["result"]["id"]
            logger.info(f"Created result: {result_id}")
            return result_id
        except Exception as e:
            logger.error(f"Failed to create result: {e}")
            raise

    def create_critique(self, critique_data: Dict[str, Any]) -> str:
        """Create a critique node."""
        try:
            result = self._execute_query(CREATE_CRITIQUE, critique_data)
            critique_id = result[0]["critique"]["id"]
            logger.info(f"Created critique: {critique_id}")
            return critique_id
        except Exception as e:
            logger.error(f"Failed to create critique: {e}")
            raise

    def link_task_to_run(self, task_id: str, run_id: str) -> None:
        """Link a task to its run."""
        try:
            self._execute_query(
                LINK_TASK_TO_RUN, {"task_id": task_id, "run_id": run_id}
            )
            logger.debug(f"Linked task {task_id} to run {run_id}")
        except Exception as e:
            logger.error(f"Failed to link task to run: {e}")
            raise

    def link_task_to_project(self, task_id: str, project_id: str) -> None:
        """Link a task to its project."""
        try:
            self._execute_query(
                LINK_TASK_TO_PROJECT, {"task_id": task_id, "project_id": project_id}
            )
            logger.debug(f"Linked task {task_id} to project {project_id}")
        except Exception as e:
            logger.error(f"Failed to link task to project: {e}")
            raise

    def link_task_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Link a task to its dependency."""
        try:
            self._execute_query(
                LINK_TASK_DEPENDENCY,
                {"task_id": task_id, "depends_on_id": depends_on_id},
            )
            logger.debug(f"Linked task {task_id} depends on {depends_on_id}")
        except Exception as e:
            logger.error(f"Failed to link task dependency: {e}")
            raise

    def link_task_result(self, task_id: str, result_id: str) -> None:
        """Link a task to its result."""
        try:
            self._execute_query(
                LINK_TASK_RESULT, {"task_id": task_id, "result_id": result_id}
            )
            logger.debug(f"Linked task {task_id} to result {result_id}")
        except Exception as e:
            logger.error(f"Failed to link task result: {e}")
            raise

    def link_task_critique(self, task_id: str, critique_id: str) -> None:
        """Link a task to its critique."""
        try:
            self._execute_query(
                LINK_TASK_CRITIQUE, {"task_id": task_id, "critique_id": critique_id}
            )
            logger.debug(f"Linked task {task_id} to critique {critique_id}")
        except Exception as e:
            logger.error(f"Failed to link task critique: {e}")
            raise

    def link_artifact_task(self, artifact_id: str, task_id: str) -> None:
        """Link an artifact to its task."""
        try:
            self._execute_query(
                LINK_ARTIFACT_TASK, {"artifact_id": artifact_id, "task_id": task_id}
            )
            logger.debug(f"Linked artifact {artifact_id} to task {task_id}")
        except Exception as e:
            logger.error(f"Failed to link artifact task: {e}")
            raise

    def link_artifact_derived_from(
        self, artifact_id: str, derived_from_id: str
    ) -> None:
        """Link an artifact to its source."""
        try:
            self._execute_query(
                LINK_ARTIFACT_DERIVED_FROM,
                {"artifact_id": artifact_id, "derived_from_id": derived_from_id},
            )
            logger.debug(
                f"Linked artifact {artifact_id} derived from {derived_from_id}"
            )
        except Exception as e:
            logger.error(f"Failed to link artifact derived from: {e}")
            raise

    def link_agent_performs_task(self, agent_name: str, task_id: str) -> None:
        """Link an agent to a task it performs."""
        try:
            self._execute_query(
                LINK_AGENT_PERFORMS_TASK, {"agent_name": agent_name, "task_id": task_id}
            )
            logger.debug(f"Linked agent {agent_name} performs task {task_id}")
        except Exception as e:
            logger.error(f"Failed to link agent performs task: {e}")
            raise

    def get_project_lineage(self, project_id: str) -> Dict[str, Any]:
        """Get the complete lineage for a project."""
        query = """
        MATCH (p:Project {id: $project_id})
        OPTIONAL MATCH (p)-[:HAS_RUN]->(r:Run)
        OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
        OPTIONAL MATCH (t)-[:RESULTED_IN]->(res:Result)
        OPTIONAL MATCH (t)-[:EMITTED]->(c:Critique)
        OPTIONAL MATCH (t)-[:PRODUCED]->(a:Artifact)
        OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
        OPTIONAL MATCH (agent:Agent)-[:PERFORMS]->(t)
        RETURN p, r, t, res, c, a, dep, agent
        ORDER BY t.created_at
        """

        try:
            result = self._execute_query(query, {"project_id": project_id})
            return self._process_lineage_result(result)
        except Exception as e:
            logger.error(f"Failed to get project lineage: {e}")
            raise

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get the current status of a run."""
        query = """
        MATCH (r:Run {id: $run_id})
        OPTIONAL MATCH (r)-[:CONTAINS_TASK]->(t:Task)
        RETURN r,
               count(t) as total_tasks,
               count(CASE WHEN t.status = 'success' THEN 1 END) as completed_tasks,
               count(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
               count(CASE WHEN t.status = 'running' THEN 1 END) as running_tasks
        """

        try:
            result = self._execute_query(query, {"run_id": run_id})
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Failed to get run status: {e}")
            raise

    def _process_lineage_result(self, result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process lineage query result into structured format."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated processing
        return {
            "project": result[0].get("p", {}) if result else {},
            "runs": list(set(r.get("r", {}) for r in result if r.get("r"))),
            "tasks": list(set(t.get("t", {}) for t in result if t.get("t"))),
            "results": list(set(r.get("res", {}) for r in result if r.get("res"))),
            "critiques": list(set(c.get("c", {}) for c in result if c.get("c"))),
            "artifacts": list(set(a.get("a", {}) for a in result if a.get("a"))),
        }


# Global client instance (will be configured by settings)
neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get the global Neo4j client instance."""
    global neo4j_client
    if neo4j_client is None:
        raise RuntimeError(
            "Neo4j client not initialized. Call init_neo4j_client() first."
        )
    return neo4j_client


def init_neo4j_client(uri: str, username: str, password: str) -> None:
    """Initialize the global Neo4j client."""
    global neo4j_client
    neo4j_client = Neo4jClient(uri, username, password)
    neo4j_client.connect()
    logger.info("Initialized Neo4j client")
