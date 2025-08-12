"""
Core cognitive database interface that abstracts AQL complexity for agents.
Uses python-arango library with validated query templates.
"""

from datetime import datetime
import logging
from typing import Any, Dict, List

from arango import ArangoClient

# Configure logging
logger = logging.getLogger(__name__)


class CognitiveDatabase:
    """Agent-friendly interface to cognitive database operations"""

    def __init__(
        self,
        host: str = "http://127.0.0.1:8550",
        database: str = "_system",
        username: str = "root",
        password: str = "change_me",
    ):
        """Initialize database connection using existing patterns"""

        self.client = ArangoClient(hosts=host)
        self.db = self.client.db(database, username=username, password=password)
        self._validate_connection()

    def _validate_connection(self) -> bool:
        """Validate database connection and collections"""
        try:
            collections = self.db.collections()
            required_collections = [
                "agent_memory",
                "cognitive_concepts",
                "semantic_relationships",
            ]

            missing = [c for c in required_collections if not self.db.has_collection(c)]
            if missing:
                logger.warning(f"Missing collections: {missing}")

            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise ConnectionError(f"Cannot connect to cognitive database: {e}")

    def find_memories_about(
        self, topic: str, importance_threshold: float = 0.7, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find memories related to a specific topic"""

        if not isinstance(topic, str) or len(topic) < 2:
            raise ValueError("Topic must be string with 2+ characters")

        # Simplified query that works with existing data structure
        query = """
        FOR memory IN agent_memory
          FILTER CONTAINS(LOWER(memory.content), @topic) OR (memory.title != null AND CONTAINS(LOWER(memory.title), @topic))
          SORT memory.created DESC
          LIMIT @limit
          RETURN memory
        """

        bind_vars = {"topic": topic.lower(), "limit": int(limit)}

        return self._execute_query(query, bind_vars, "find_memories_about")

    def get_foundational_memories(
        self, min_quality: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Get high-quality foundational memories"""

        query = """
        FOR memory IN agent_memory
          FILTER memory.foundational == true
          FILTER memory.importance_score >= @min_quality OR memory.quality_score >= @min_quality
          SORT memory.importance_score DESC
          RETURN memory
        """

        bind_vars = {"min_quality": float(min_quality)}
        return self._execute_query(query, bind_vars, "get_foundational_memories")

    def get_concepts_by_domain(
        self, domain: str, min_quality: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get cognitive concepts filtered by domain"""

        query = """
        FOR concept IN cognitive_concepts
          FILTER concept.domain == @domain
          FILTER concept.quality_score >= @min_quality
          SORT concept.quality_score DESC
          RETURN concept
        """

        bind_vars = {"domain": domain, "min_quality": float(min_quality)}
        return self._execute_query(query, bind_vars, "get_concepts_by_domain")

    def get_memories_by_type(
        self, memory_type: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get memories filtered by type (operational, procedural, etc.)"""

        query = """
        FOR memory IN agent_memory
          FILTER memory.memory_type == @memory_type OR memory.type == @memory_type
          SORT memory.importance_score DESC
          LIMIT @limit
          RETURN memory
        """

        bind_vars = {"memory_type": memory_type, "limit": int(limit)}
        return self._execute_query(query, bind_vars, "get_memories_by_type")

    def get_startup_context(self) -> Dict[str, Any]:
        """Get essential startup context and foundational knowledge"""

        foundational = self.get_foundational_memories()
        operational_concepts = self.get_concepts_by_domain("operational")

        return {
            "foundational_memories": foundational[:10],  # Limit for performance
            "operational_concepts": operational_concepts[:5],
            "startup_timestamp": datetime.now().isoformat(),
        }

    def assess_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health assessment"""

        try:
            # Get collection counts
            collections_info = {}
            for collection_name in [
                "agent_memory",
                "cognitive_concepts",
                "semantic_relationships",
            ]:
                if self.db.has_collection(collection_name):
                    count = self.db.collection(collection_name).count()
                    collections_info[collection_name] = count
                else:
                    collections_info[collection_name] = 0

            return {
                "collections": collections_info,
                "health_score": self._calculate_health_score(collections_info),
                "assessment_timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Health assessment failed: {e}")
            return {"error": str(e), "health_score": 0.0}

    def _calculate_health_score(self, collections: Dict[str, int]) -> float:
        """Calculate overall system health score"""

        score = 0.0
        if collections.get("agent_memory", 0) > 50:
            score += 0.4
        if collections.get("cognitive_concepts", 0) > 10:
            score += 0.3
        if collections.get("semantic_relationships", 0) > 5:
            score += 0.3

        return score

    def _execute_query(
        self, query: str, bind_vars: Dict[str, Any], operation_name: str
    ) -> List[Dict[str, Any]]:
        """Execute AQL query with error handling and validation"""

        try:
            logger.debug(f"Executing {operation_name} with vars: {bind_vars}")

            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)

            logger.debug(f"{operation_name} returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Query execution failed for {operation_name}: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Bind vars: {bind_vars}")

            # Return meaningful error to agent
            return [
                {
                    "error": f"{operation_name} failed: {str(e)}",
                    "query_type": operation_name,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
