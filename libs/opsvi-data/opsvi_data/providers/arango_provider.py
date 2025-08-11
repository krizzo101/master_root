"""
ArangoDB Provider for OPSVI Data Services

Comprehensive ArangoDB integration for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official ArangoDB Python driver:
- https://python-arango.readthedocs.io/
- https://www.arangodb.com/docs/stable/

Implements all core endpoints and features:
- Direct AQL execution
- Batch operations and transactions
- Graph operations and analytics
- Index management
- Collection management
- Advanced analytics helpers

Version: Referenced as of July 2024
"""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from arango import ArangoClient, ArangoError
except ImportError:
    raise ImportError(
        "python-arango is required. Install with `pip install python-arango`."
    )

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class ArangoDBError(ComponentError):
    """Custom exception for ArangoDB operations."""

    pass


class ArangoDBConfig:
    """Configuration for ArangoDB provider."""

    def __init__(
        self,
        host: Optional[str] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ):
        self.host = host or os.getenv("ARANGO_URL", "http://127.0.0.1:8529")
        self.database = database or os.getenv("ARANGO_DB", "_system")
        self.username = username or os.getenv("ARANGO_USERNAME", "root")
        self.password = password or os.getenv("ARANGO_PASSWORD", "change_me")

        # Additional configuration
        for key, value in kwargs.items():
            setattr(self, key, value)


class ArangoDBProvider(BaseComponent):
    """
    Comprehensive ArangoDB provider for OPSVI ecosystem.

    Provides full database capabilities:
    - Direct AQL execution
    - Batch operations
    - Graph operations
    - Index management
    - Collection management
    - Advanced analytics helpers
    """

    def __init__(self, config: ArangoDBConfig, **kwargs: Any) -> None:
        """Initialize ArangoDB provider.

        Args:
            config: ArangoDB configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__("arangodb", config.__dict__)
        self.config = config
        self.client: Optional[ArangoClient] = None
        self.db = None

        logger.debug(f"ArangoDBProvider initialized with host: {config.host}")

    async def _initialize_impl(self) -> None:
        """Initialize ArangoDB connection."""
        try:
            self.client = ArangoClient(hosts=self.config.host)
            self.db = self.client.db(
                self.config.database,
                username=self.config.username,
                password=self.config.password,
            )

            # Validate connection
            self._validate_connection()
            logger.info(
                f"ArangoDB connected: {self.config.host}/{self.config.database}"
            )

        except Exception as e:
            logger.error(f"ArangoDB initialization failed: {e}")
            raise ArangoDBError(f"Failed to initialize ArangoDB: {e}")

    async def _shutdown_impl(self) -> None:
        """Shutdown ArangoDB connection."""
        try:
            if self.client:
                # ArangoDB client doesn't have explicit close method
                self.client = None
                self.db = None
            logger.info("ArangoDB connection closed")
        except Exception as e:
            logger.error(f"ArangoDB shutdown error: {e}")

    async def _health_check_impl(self) -> bool:
        """Check ArangoDB health."""
        try:
            if not self.db:
                return False
            collections = self.db.collections()
            return len(collections) >= 0  # Just check if we can access
        except Exception as e:
            logger.error(f"ArangoDB health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self._initialize_impl()

    def _validate_connection(self) -> bool:
        """Validate database connection."""
        try:
            collections = self.db.collections()
            logger.info(f"Connected to database with {len(collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            raise ArangoDBError(f"Cannot connect to ArangoDB: {e}")

    # ==================== DIRECT AQL OPERATIONS ====================

    def execute_aql(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        full_count: bool = False,
        profile: bool = False,
    ) -> Dict[str, Any]:
        """Execute raw AQL query with full control."""
        try:
            bind_vars = bind_vars or {}

            cursor = self.db.aql.execute(
                query,
                bind_vars=bind_vars,
                batch_size=batch_size,
                full_count=full_count,
                profile=profile,
            )

            results = list(cursor)

            response = {
                "success": True,
                "results": results,
                "count": len(results),
                "cached": getattr(cursor, "cached", False),
                "profile": getattr(cursor, "profile", None) if profile else None,
            }

            if full_count:
                response["full_count"] = getattr(cursor, "full_count", None)

            return response

        except ArangoError as e:
            logger.error(f"AQL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0,
            }

    # ==================== BATCH OPERATIONS ====================

    def batch_insert(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        overwrite: bool = False,
        return_new: bool = False,
        sync: bool = False,
        silent: bool = False,
    ) -> Dict[str, Any]:
        """Insert multiple documents in batch."""
        try:
            result = self.db.collection(collection).insert_many(
                documents,
                overwrite=overwrite,
                return_new=return_new,
                sync=sync,
                silent=silent,
            )

            return {
                "success": True,
                "inserted": len(result),
                "ignored": len([r for r in result if r.get("error")]),
                "results": result,
            }

        except ArangoError as e:
            logger.error(f"Batch insert failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "inserted": 0,
                "ignored": 0,
                "results": [],
            }

    # ==================== COLLECTION MANAGEMENT ====================

    def create_collection(
        self, name: str, edge: bool = False, schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new collection."""
        try:
            result = self.db.create_collection(
                name,
                edge=edge,
                schema=schema,
            )

            return {
                "success": True,
                "collection": result,
                "name": name,
                "type": "edge" if edge else "document",
            }

        except ArangoError as e:
            logger.error(f"Collection creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "name": name,
            }

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.db.collections()
            return [col["name"] for col in collections]
        except ArangoError as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            return self.db.has_collection(name)
        except ArangoError as e:
            logger.error(f"Collection existence check failed: {e}")
            return False

    # ==================== INDEX MANAGEMENT ====================

    def create_persistent_index(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        sparse: bool = False,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a persistent index."""
        try:
            result = self.db.collection(collection).add_persistent_index(
                fields=fields,
                unique=unique,
                sparse=sparse,
                name=name,
            )

            return {
                "success": True,
                "index": result,
                "collection": collection,
                "fields": fields,
            }

        except ArangoError as e:
            logger.error(f"Persistent index creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "collection": collection,
                "fields": fields,
            }

    # ==================== DOCUMENT OPERATIONS ====================

    def get_document(self, collection: str, key: str) -> Dict[str, Any]:
        """Get a document by key."""
        try:
            doc = self.db.collection(collection).get(key)
            return {
                "success": True,
                "document": doc,
            }
        except ArangoError as e:
            logger.error(f"Document retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "document": None,
            }

    def update_document(
        self, collection: str, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a document."""
        try:
            result = self.db.collection(collection).update(document)
            return {
                "success": True,
                "result": result,
            }
        except ArangoError as e:
            logger.error(f"Document update failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def delete_document(self, collection: str, key: str) -> Dict[str, Any]:
        """Delete a document by key."""
        try:
            result = self.db.collection(collection).delete(key)
            return {
                "success": True,
                "result": result,
            }
        except ArangoError as e:
            logger.error(f"Document deletion failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ==================== GRAPH OPERATIONS ====================

    def list_graphs(self) -> List[str]:
        """List all graphs."""
        try:
            graphs = self.db.graphs()
            return [graph["name"] for graph in graphs]
        except ArangoError as e:
            logger.error(f"Failed to list graphs: {e}")
            return []

    def create_graph(
        self,
        name: str,
        edge_definitions: List[Dict[str, Any]],
        orphan_collections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new graph."""
        try:
            result = self.db.create_graph(
                name,
                edge_definitions=edge_definitions,
                orphan_collections=orphan_collections or [],
            )

            return {
                "success": True,
                "graph": result,
                "name": name,
            }

        except ArangoError as e:
            logger.error(f"Graph creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "name": name,
            }

    # ==================== ANALYTICS HELPERS ====================

    def get_neighbors(
        self, graph_name: str, vertex_id: str, direction: str = "any"
    ) -> Dict[str, Any]:
        """Get neighbors of a vertex."""
        try:
            query = f"""
            FOR v, e, p IN 1..1 {direction} '{vertex_id}'
            GRAPH '{graph_name}'
            RETURN {{
                vertex: v,
                edge: e,
                path: p
            }}
            """

            result = self.execute_aql(query)

            return {
                "success": True,
                "neighbors": result["results"],
                "count": result["count"],
                "vertex_id": vertex_id,
                "direction": direction,
            }

        except Exception as e:
            logger.error(f"Get neighbors failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "neighbors": [],
                "count": 0,
            }

    def get_subgraph(
        self, graph_name: str, start_vertex: str, depth: int = 2, direction: str = "any"
    ) -> Dict[str, Any]:
        """Extract a subgraph from a starting vertex."""
        try:
            query = f"""
            FOR v, e, p IN 1..{depth} {direction} '{start_vertex}'
            GRAPH '{graph_name}'
            RETURN {{
                vertex: v,
                edge: e,
                path: p
            }}
            """

            result = self.execute_aql(query)

            return {
                "success": True,
                "subgraph": result["results"],
                "count": result["count"],
                "start_vertex": start_vertex,
                "depth": depth,
                "direction": direction,
            }

        except Exception as e:
            logger.error(f"Get subgraph failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "subgraph": [],
                "count": 0,
            }

    def shortest_path(
        self,
        graph_name: str,
        start_vertex: str,
        end_vertex: str,
        direction: str = "out",
    ) -> Dict[str, Any]:
        """Find shortest path between two vertices."""
        try:
            query = f"""
            FOR v, e, p IN SHORTEST_PATH '{start_vertex}' TO '{end_vertex}'
            GRAPH '{graph_name}'
            OPTIONS {{direction: '{direction}'}}
            RETURN {{
                vertex: v,
                edge: e,
                path: p,
                distance: LENGTH(p.edges)
            }}
            """

            result = self.execute_aql(query)

            return {
                "success": True,
                "path": result["results"],
                "distance": len(result["results"]) - 1 if result["results"] else 0,
                "start_vertex": start_vertex,
                "end_vertex": end_vertex,
                "direction": direction,
            }

        except Exception as e:
            logger.error(f"Shortest path failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "path": [],
                "distance": -1,
            }

    # ==================== DATABASE INFO ====================

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information."""
        try:
            info = self.db.properties()
            return {
                "success": True,
                "info": info,
            }
        except ArangoError as e:
            logger.error(f"Database info retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        try:
            # Test basic operations
            collections = self.list_collections()
            graphs = self.list_graphs()

            return {
                "success": True,
                "status": "healthy",
                "collections_count": len(collections),
                "graphs_count": len(graphs),
                "database": self.config.database,
                "host": self.config.host,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
            }
