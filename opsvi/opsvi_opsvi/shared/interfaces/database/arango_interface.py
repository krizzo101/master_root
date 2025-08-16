"""
Direct ArangoDB Interface - Full Database Capabilities
For scripts and applications that need comprehensive ArangoDB operations without abstraction.
Complements ConsolidatedArangoDB (for agents) with full AQL and advanced features.

Now includes advanced analytics helpers (neighbors, subgraph, shortest path) and async stubs for automation.

All analytics helpers return structured results (success, error, results, etc.) for programmatic automation.

Usage:
    # Get neighbors of a vertex
    db.get_neighbors('school', 'students/01', direction='out')

    # Extract a subgraph
    db.get_subgraph('school', 'students/01', depth=2)

    # Find shortest path
    db.shortest_path('school', 'students/01', 'lectures/CSC101')
"""

import logging
import os
from typing import Any, Dict, List, Optional

from arango import ArangoClient, ArangoError

logger = logging.getLogger(__name__)


class DirectArangoDB:
    """
    Direct ArangoDB interface providing full database capabilities:
    - Direct AQL execution
    - Batch operations
    - Graph operations
    - Index management
    - Collection management
    - Advanced analytics helpers: get_neighbors, get_subgraph, shortest_path
    - Async stubs for analytics (NotImplemented)
    """

    def __init__(
        self,
        host: str = None,
        database: str = None,
        username: str = None,
        password: str = None,
    ):
        """Initialize with configuration"""
        self.host = host or os.getenv("ARANGO_URL", "http://127.0.0.1:8550")
        self.database_name = database or os.getenv("ARANGO_DB", "_system")
        self.username = username or os.getenv("ARANGO_USERNAME", "root")
        self.password = password or os.getenv("ARANGO_PASSWORD", "change_me")

        # Initialize connection
        self.client = ArangoClient(hosts=self.host)
        self.db = self.client.db(
            self.database_name, username=self.username, password=self.password
        )

        # Validate connection
        self._validate_connection()
        logger.info(f"DirectArangoDB initialized: {self.host}/{self.database_name}")

    def _validate_connection(self) -> bool:
        """Validate database connection"""
        try:
            collections = self.db.collections()
            logger.info(f"Connected to database with {len(collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            raise ConnectionError(f"Cannot connect to ArangoDB: {e}")

    # ==================== DIRECT AQL OPERATIONS ====================

    def execute_aql(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        full_count: bool = False,
        profile: bool = False,
    ) -> Dict[str, Any]:
        """Execute raw AQL query with full control"""
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
            }

            if profile and hasattr(cursor, "profile"):
                response["profile"] = cursor.profile

            if full_count and hasattr(cursor, "count"):
                response["total_count"] = cursor.count()

            return response

        except ArangoError as e:
            logger.error(f"AQL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": getattr(e, "error_code", None),
                "query": query,
                "bind_vars": bind_vars,
            }
        except Exception as e:
            logger.error(f"AQL execution error: {e}")
            return {"success": False, "error": str(e), "query": query}

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
        """Bulk insert documents"""
        try:
            if not self.db.has_collection(collection):
                return {
                    "success": False,
                    "error": f"Collection '{collection}' does not exist",
                }

            coll = self.db.collection(collection)
            result = coll.insert_many(
                documents,
                overwrite=overwrite,
                return_new=return_new,
                sync=sync,
                silent=silent,
            )

            successful = [
                r for r in result if not isinstance(r, dict) or not r.get("error")
            ]
            errors = [r for r in result if isinstance(r, dict) and r.get("error")]

            return {
                "success": True,
                "inserted": len(successful),
                "errors": errors,
                "total_attempted": len(documents),
                "results": result if not silent else None,
            }

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== COLLECTION MANAGEMENT ====================

    def create_collection(
        self, name: str, edge: bool = False, schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create collection"""
        try:
            result = self.db.create_collection(name=name, edge=edge, schema=schema)

            return {"success": True, "collection": result.name}

        except Exception as e:
            logger.error(f"Collection creation failed: {e}")
            return {"success": False, "error": str(e)}

    def list_collections(self) -> List[str]:
        """List collection names"""
        try:
            collections = self.db.collections()
            return [c["name"] for c in collections]
        except Exception as e:
            logger.error(f"List collections failed: {e}")
            return []

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        return self.db.has_collection(name)

    # ==================== INDEX MANAGEMENT ====================

    def create_persistent_index(
        self,
        collection: str,
        fields: List[str],
        unique: bool = False,
        sparse: bool = False,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create persistent index"""
        try:
            if not self.db.has_collection(collection):
                return {
                    "success": False,
                    "error": f"Collection '{collection}' does not exist",
                }

            coll = self.db.collection(collection)
            result = coll.add_persistent_index(
                fields=fields, unique=unique, sparse=sparse, name=name
            )

            return {"success": True, "index": result}

        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== UTILITY METHODS ====================

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        try:
            return {
                "success": True,
                "database_info": {
                    "name": self.db.name,
                    "collections": self.list_collections(),
                    "graphs": [g["name"] for g in self.db.graphs()],
                },
            }
        except Exception as e:
            logger.error(f"Database info failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== DATABASE MANAGEMENT ====================

    def list_databases(self) -> List[str]:
        """List all databases on the server."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            return sys_db.databases()
        except Exception as e:
            logger.error(f"List databases failed: {e}")
            return []

    def create_database(
        self, name: str, users: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new database with optional users."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            sys_db.create_database(name=name, users=users or [])
            return {"success": True, "database": name}
        except Exception as e:
            logger.error(f"Create database failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_database(self, name: str) -> Dict[str, Any]:
        """Delete a database."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            sys_db.delete_database(name)
            return {"success": True, "database": name}
        except Exception as e:
            logger.error(f"Delete database failed: {e}")
            return {"success": False, "error": str(e)}

    def get_server_info(self) -> Dict[str, Any]:
        """Get server version, status, engine, details."""
        try:
            return {
                "success": True,
                "version": self.db.version(),
                "status": self.db.status(),
                "engine": self.db.engine(),
                "details": self.db.details(),
            }
        except Exception as e:
            logger.error(f"Get server info failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== USER & PERMISSION MANAGEMENT ====================

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            return sys_db.users()
        except Exception as e:
            logger.error(f"List users failed: {e}")
            return []

    def create_user(
        self,
        username: str,
        password: str,
        active: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new user."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            sys_db.create_user(
                username=username, password=password, active=active, extra=extra or {}
            )
            return {"success": True, "user": username}
        except Exception as e:
            logger.error(f"Create user failed: {e}")
            return {"success": False, "error": str(e)}

    def update_user(
        self,
        username: str,
        password: Optional[str] = None,
        active: Optional[bool] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update an existing user."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            sys_db.update_user(
                username=username, password=password, active=active, extra=extra
            )
            return {"success": True, "user": username}
        except Exception as e:
            logger.error(f"Update user failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_user(self, username: str) -> Dict[str, Any]:
        """Delete a user."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            sys_db.delete_user(username)
            return {"success": True, "user": username}
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            return {"success": False, "error": str(e)}

    def get_user_permissions(self, username: str) -> Dict[str, Any]:
        """Get all permissions for a user."""
        try:
            sys_db = self.client.db(
                "_system", username=self.username, password=self.password
            )
            return {"success": True, "permissions": sys_db.permissions(username)}
        except Exception as e:
            logger.error(f"Get user permissions failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== DOCUMENT OPERATIONS (EXTENDED) ====================

    def get_document(self, collection: str, key: str) -> Dict[str, Any]:
        """Get a document by key."""
        try:
            coll = self.db.collection(collection)
            doc = coll.get(key)
            return {"success": True, "document": doc}
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return {"success": False, "error": str(e)}

    def update_document(
        self, collection: str, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a document by key."""
        try:
            coll = self.db.collection(collection)
            result = coll.update(document)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Update document failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_document(self, collection: str, key: str) -> Dict[str, Any]:
        """Delete a document by key."""
        try:
            coll = self.db.collection(collection)
            coll.delete(key)
            return {"success": True, "key": key}
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            return {"success": False, "error": str(e)}

    def find_documents(
        self, collection: str, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        """Find documents by filter."""
        try:
            coll = self.db.collection(collection)
            docs = list(coll.find(filters, skip=skip, limit=limit))
            return {"success": True, "documents": docs}
        except Exception as e:
            logger.error(f"Find documents failed: {e}")
            return {"success": False, "error": str(e)}

    def get_random_document(self, collection: str) -> Dict[str, Any]:
        """Get a random document from a collection."""
        try:
            coll = self.db.collection(collection)
            doc = coll.random()
            return {"success": True, "document": doc}
        except Exception as e:
            logger.error(f"Get random document failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== INDEX MANAGEMENT (EXTENDED) ====================

    def create_fulltext_index(
        self, collection: str, fields: List[str]
    ) -> Dict[str, Any]:
        """Create a fulltext index."""
        try:
            coll = self.db.collection(collection)
            idx = coll.add_index({"type": "fulltext", "fields": fields})
            return {"success": True, "index": idx}
        except Exception as e:
            logger.error(f"Create fulltext index failed: {e}")
            return {"success": False, "error": str(e)}

    def create_geo_index(self, collection: str, fields: List[str]) -> Dict[str, Any]:
        """Create a geo index."""
        try:
            coll = self.db.collection(collection)
            idx = coll.add_index({"type": "geo", "fields": fields})
            return {"success": True, "index": idx}
        except Exception as e:
            logger.error(f"Create geo index failed: {e}")
            return {"success": False, "error": str(e)}

    def create_ttl_index(
        self, collection: str, fields: List[str], expire_after: int
    ) -> Dict[str, Any]:
        """Create a TTL index."""
        try:
            coll = self.db.collection(collection)
            idx = coll.add_index(
                {"type": "ttl", "fields": fields, "expireAfter": expire_after}
            )
            return {"success": True, "index": idx}
        except Exception as e:
            logger.error(f"Create TTL index failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_index(self, collection: str, index_id: str) -> Dict[str, Any]:
        """Delete an index by ID."""
        try:
            coll = self.db.collection(collection)
            coll.delete_index(index_id)
            return {"success": True, "index_id": index_id}
        except Exception as e:
            logger.error(f"Delete index failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== GRAPH OPERATIONS (BASIC) ====================

    def list_graphs(self) -> List[str]:
        """List all graphs in the database."""
        try:
            return [g["name"] for g in self.db.graphs()]
        except Exception as e:
            logger.error(f"List graphs failed: {e}")
            return []

    def create_graph(
        self,
        name: str,
        edge_definitions: List[Dict[str, Any]],
        orphan_collections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new graph."""
        try:
            graph = self.db.create_graph(
                name,
                edge_definitions=edge_definitions,
                orphan_collections=orphan_collections or [],
            )
            return {"success": True, "graph": graph.name}
        except Exception as e:
            logger.error(f"Create graph failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_graph(self, name: str) -> Dict[str, Any]:
        """Delete a graph."""
        try:
            self.db.delete_graph(name)
            return {"success": True, "graph": name}
        except Exception as e:
            logger.error(f"Delete graph failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== VIEW & SEARCH MANAGEMENT (BASIC) ====================

    def list_views(self) -> List[str]:
        """List all views in the database."""
        try:
            return [v["name"] for v in self.db.views()]
        except Exception as e:
            logger.error(f"List views failed: {e}")
            return []

    def create_arangosearch_view(
        self, name: str, properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an ArangoSearch view."""
        try:
            view = self.db.create_arangosearch_view(
                name=name, properties=properties or {}
            )
            return {"success": True, "view": view["name"]}
        except Exception as e:
            logger.error(f"Create ArangoSearch view failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_view(self, name: str) -> Dict[str, Any]:
        """Delete a view."""
        try:
            self.db.delete_view(name)
            return {"success": True, "view": name}
        except Exception as e:
            logger.error(f"Delete view failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== ANALYZER MANAGEMENT (BASIC) ====================

    def list_analyzers(self) -> List[str]:
        """List all analyzers in the database."""
        try:
            return [a["name"] for a in self.db.analyzers()]
        except Exception as e:
            logger.error(f"List analyzers failed: {e}")
            return []

    def create_analyzer(
        self,
        name: str,
        analyzer_type: str,
        properties: Dict[str, Any],
        features: List[str],
    ) -> Dict[str, Any]:
        """Create an analyzer."""
        try:
            self.db.create_analyzer(
                name=name,
                analyzer_type=analyzer_type,
                properties=properties,
                features=features,
            )
            return {"success": True, "analyzer": name}
        except Exception as e:
            logger.error(f"Create analyzer failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_analyzer(self, name: str) -> Dict[str, Any]:
        """Delete an analyzer."""
        try:
            self.db.delete_analyzer(name, ignore_missing=True)
            return {"success": True, "analyzer": name}
        except Exception as e:
            logger.error(f"Delete analyzer failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== PREGEL GRAPH ANALYTICS (HTTP API) ====================

    def run_pregel_job(
        self, algorithm: str, graph_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a Pregel job (e.g., PageRank, SSSP) via HTTP API."""
        import requests

        try:
            url = f"{self.host}/_db/{self.database_name}/_api/control_pregel"
            resp = requests.post(
                url,
                auth=(self.username, self.password),
                json={
                    "algorithm": algorithm,
                    "graphName": graph_name,
                    "params": params or {},
                },
            )
            resp.raise_for_status()
            job_id = resp.json().get("id")
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.error(f"Run Pregel job failed: {e}")
            return {"success": False, "error": str(e)}

    def get_pregel_status(self, job_id: str) -> Dict[str, Any]:
        """Get Pregel job status via HTTP API."""
        import requests

        try:
            url = f"{self.host}/_db/{self.database_name}/_api/control_pregel/{job_id}"
            resp = requests.get(url, auth=(self.username, self.password))
            resp.raise_for_status()
            return {"success": True, "status": resp.json()}
        except Exception as e:
            logger.error(f"Get Pregel status failed: {e}")
            return {"success": False, "error": str(e)}

    def cancel_pregel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a Pregel job via HTTP API."""
        import requests

        try:
            url = f"{self.host}/_db/{self.database_name}/_api/control_pregel/{job_id}"
            resp = requests.delete(url, auth=(self.username, self.password))
            resp.raise_for_status()
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.error(f"Cancel Pregel job failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== DOCUMENT ADVANCED OPERATIONS ====================

    def replace_document(
        self, collection: str, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replace a document by key."""
        try:
            coll = self.db.collection(collection)
            result = coll.replace(document)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Replace document failed: {e}")
            return {"success": False, "error": str(e)}

    def update_documents_match(
        self, collection: str, match: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update all documents matching filter."""
        try:
            coll = self.db.collection(collection)
            result = coll.update_match(match, updates)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Update documents by match failed: {e}")
            return {"success": False, "error": str(e)}

    def replace_documents_match(
        self, collection: str, match: Dict[str, Any], replacement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replace all documents matching filter."""
        try:
            coll = self.db.collection(collection)
            result = coll.replace_match(match, replacement)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Replace documents by match failed: {e}")
            return {"success": False, "error": str(e)}

    def delete_documents_match(
        self, collection: str, match: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete all documents matching filter."""
        try:
            coll = self.db.collection(collection)
            result = coll.delete_match(match)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Delete documents by match failed: {e}")
            return {"success": False, "error": str(e)}

    def import_bulk_documents(
        self, collection: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk import documents."""
        try:
            coll = self.db.collection(collection)
            result = coll.import_bulk(documents)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Bulk import failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== INDEX MANAGEMENT (ADVANCED) ====================

    def create_mdi_index(
        self, collection: str, fields: List[str], field_value_types: str = "double"
    ) -> Dict[str, Any]:
        """Create a multi-dimensional index (MDI)."""
        try:
            coll = self.db.collection(collection)
            idx = coll.add_index(
                {"type": "mdi", "fields": fields, "fieldValueTypes": field_value_types}
            )
            return {"success": True, "index": idx}
        except Exception as e:
            logger.error(f"Create MDI index failed: {e}")
            return {"success": False, "error": str(e)}

    def create_named_index(
        self,
        collection: str,
        fields: List[str],
        name: str,
        index_type: str = "persistent",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a named index of specified type."""
        try:
            coll = self.db.collection(collection)
            idx = coll.add_index(
                {"type": index_type, "fields": fields, "name": name, **kwargs}
            )
            return {"success": True, "index": idx}
        except Exception as e:
            logger.error(f"Create named index failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== GRAPH ADVANCED OPERATIONS ====================

    def create_vertex_collection(
        self, graph_name: str, collection_name: str
    ) -> Dict[str, Any]:
        """Create a vertex collection in a graph."""
        try:
            graph = self.db.graph(graph_name)
            vc = graph.create_vertex_collection(collection_name)
            return {"success": True, "vertex_collection": vc.name}
        except Exception as e:
            logger.error(f"Create vertex collection failed: {e}")
            return {"success": False, "error": str(e)}

    def create_edge_definition(
        self,
        graph_name: str,
        edge_collection: str,
        from_collections: List[str],
        to_collections: List[str],
    ) -> Dict[str, Any]:
        """Create an edge definition in a graph."""
        try:
            graph = self.db.graph(graph_name)
            ed = graph.create_edge_definition(
                edge_collection=edge_collection,
                from_vertex_collections=from_collections,
                to_vertex_collections=to_collections,
            )
            return {"success": True, "edge_definition": ed["edge_collection"]}
        except Exception as e:
            logger.error(f"Create edge definition failed: {e}")
            return {"success": False, "error": str(e)}

    def insert_vertex(
        self, graph_name: str, collection: str, document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a vertex into a graph."""
        try:
            graph = self.db.graph(graph_name)
            vc = graph.vertex_collection(collection)
            result = vc.insert(document)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Insert vertex failed: {e}")
            return {"success": False, "error": str(e)}

    def insert_edge(
        self, graph_name: str, edge_collection: str, edge: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert an edge into a graph."""
        try:
            graph = self.db.graph(graph_name)
            ec = graph.edge_collection(edge_collection)
            result = ec.insert(edge)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Insert edge failed: {e}")
            return {"success": False, "error": str(e)}

    def list_edges(
        self, graph_name: str, edge_collection: str, vertex: str, direction: str = "any"
    ) -> Dict[str, Any]:
        """List edges for a vertex in a given direction (in, out, any)."""
        try:
            graph = self.db.graph(graph_name)
            ec = graph.edge_collection(edge_collection)
            edges = ec.edges(vertex, direction=direction)
            return {"success": True, "edges": edges}
        except Exception as e:
            logger.error(f"List edges failed: {e}")
            return {"success": False, "error": str(e)}

    def traverse_graph(
        self, query: str, bind_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a graph traversal using AQL."""
        return self.execute_aql(query, bind_vars)

    # ==================== VIEW & SEARCH ADVANCED ====================

    def update_view(self, name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update view properties."""
        try:
            self.db.update_view(name=name, properties=properties)
            return {"success": True, "view": name}
        except Exception as e:
            logger.error(f"Update view failed: {e}")
            return {"success": False, "error": str(e)}

    def replace_view(self, name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Replace view properties."""
        try:
            self.db.replace_view(name=name, properties=properties)
            return {"success": True, "view": name}
        except Exception as e:
            logger.error(f"Replace view failed: {e}")
            return {"success": False, "error": str(e)}

    def rename_view(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a view."""
        try:
            self.db.rename_view(old_name, new_name)
            return {"success": True, "view": new_name}
        except Exception as e:
            logger.error(f"Rename view failed: {e}")
            return {"success": False, "error": str(e)}

    def get_view_properties(self, name: str) -> Dict[str, Any]:
        """Retrieve view properties."""
        try:
            view = self.db.view(name)
            return {"success": True, "properties": view}
        except Exception as e:
            logger.error(f"Get view properties failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== BATCH OPERATIONS ====================

    def begin_batch_execution(self, return_result: bool = True):
        """Begin batch execution context manager."""
        try:
            return self.db.begin_batch_execution(return_result=return_result)
        except Exception as e:
            logger.error(f"Begin batch execution failed: {e}")
            return None

    # ==================== TRANSACTION MANAGEMENT ====================

    def begin_transaction(self, read: str = None, write: str = None):
        """Begin a transaction (returns TransactionDatabase wrapper)."""
        try:
            return self.db.begin_transaction(read=read, write=write)
        except Exception as e:
            logger.error(f"Begin transaction failed: {e}")
            return None

    # ==================== REPLICATION & BACKUP (BASIC) ====================

    def get_replication_inventory(self) -> Dict[str, Any]:
        """Get replication inventory."""
        try:
            inventory = self.db.replication.inventory()
            return {"success": True, "inventory": inventory}
        except Exception as e:
            logger.error(f"Get replication inventory failed: {e}")
            return {"success": False, "error": str(e)}

    def create_backup(
        self,
        label: str,
        allow_inconsistent: bool = True,
        force: bool = False,
        timeout: int = 1000,
    ) -> Dict[str, Any]:
        """Create a backup (Enterprise only)."""
        try:
            backup = self.db.backup.create(
                label=label,
                allow_inconsistent=allow_inconsistent,
                force=force,
                timeout=timeout,
            )
            return {"success": True, "backup": backup}
        except Exception as e:
            logger.error(f"Create backup failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== FOXX MICROSERVICES (BASIC) ====================

    def list_foxx_services(self) -> Dict[str, Any]:
        """List all Foxx services."""
        try:
            foxx = self.db.foxx
            services = foxx.services()
            return {"success": True, "services": services}
        except Exception as e:
            logger.error(f"List Foxx services failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== TASK & JOB MANAGEMENT (BASIC) ====================

    def list_tasks(self) -> Dict[str, Any]:
        """List all tasks."""
        try:
            tasks = self.db.tasks()
            return {"success": True, "tasks": tasks}
        except Exception as e:
            logger.error(f"List tasks failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== CLUSTER & DEPLOYMENT (BASIC) ====================

    def get_cluster_inventory(self) -> Dict[str, Any]:
        """Get cluster inventory (if in cluster mode)."""
        try:
            inventory = self.db.replication.cluster_inventory()
            return {"success": True, "inventory": inventory}
        except Exception as e:
            logger.error(f"Get cluster inventory failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== OVERLOAD CONTROL ====================

    def begin_controlled_execution(self, max_queue_time_seconds: float = 7.5):
        """Begin controlled execution context."""
        try:
            return self.db.begin_controlled_execution(
                max_queue_time_seconds=max_queue_time_seconds
            )
        except Exception as e:
            logger.error(f"Begin controlled execution failed: {e}")
            return None

    # ==================== UTILITY / HEALTH ====================

    def health_check(self) -> Dict[str, Any]:
        """Basic health check: list collections and graphs."""
        try:
            collections = self.list_collections()
            graphs = self.list_graphs()
            return {"success": True, "collections": collections, "graphs": graphs}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== EXTENSION POINTS ====================
    # Add more methods for advanced batch ops, transactions, replication, Foxx, etc. as needed.

    # ==================== GRAPH ANALYTICS HELPERS ====================
    # Spec-compliant helpers based on official python-arango and ArangoDB docs (July 2024)

    def get_neighbors(
        self, graph_name: str, vertex_id: str, direction: str = "any"
    ) -> Dict[str, Any]:
        """
        Get neighbors of a vertex in a graph.
        Args:
            graph_name: Name of the graph.
            vertex_id: _id of the vertex (e.g., 'students/01').
            direction: 'in', 'out', or 'any'.
        Returns:
            Dict with success, neighbors, and error (if any).
        Example:
            >>> db.get_neighbors('school', 'students/01', direction='out')
            # Returns: {'success': True, 'neighbors': [...]} or {'success': False, 'error': ...}
        """
        try:
            query = f"""
            FOR v IN 1..1 {direction.upper()}BOUND @start_vertex GRAPH @graph_name
                RETURN v
            """
            bind_vars = {"start_vertex": vertex_id, "graph_name": graph_name}
            res = self.execute_aql(query, bind_vars)
            if res.get("success"):
                return {"success": True, "neighbors": res["results"]}
            return {"success": False, "error": res.get("error")}
        except Exception as e:
            logger.error(f"get_neighbors failed: {e}")
            return {"success": False, "error": str(e)}

    def get_subgraph(
        self, graph_name: str, start_vertex: str, depth: int = 2, direction: str = "any"
    ) -> Dict[str, Any]:
        """
        Extract a subgraph up to a given depth from a start vertex.
        Args:
            graph_name: Name of the graph.
            start_vertex: _id of the starting vertex.
            depth: Max traversal depth.
            direction: 'in', 'out', or 'any'.
        Returns:
            Dict with success, vertices, edges, and error (if any).
        Example:
            >>> db.get_subgraph('school', 'students/01', depth=2)
            # Returns: {'success': True, 'vertices': [...], 'edges': [...]} or {'success': False, 'error': ...}
        """
        try:
            query = f"""
            FOR v, e, p IN 1..{depth} {direction.upper()}BOUND @start_vertex GRAPH @graph_name
                RETURN {{vertex: v, edge: e, path: p}}
            """
            bind_vars = {"start_vertex": start_vertex, "graph_name": graph_name}
            res = self.execute_aql(query, bind_vars)
            if res.get("success"):
                vertices = [
                    item["vertex"] for item in res["results"] if "vertex" in item
                ]
                edges = [item["edge"] for item in res["results"] if "edge" in item]
                return {"success": True, "vertices": vertices, "edges": edges}
            return {"success": False, "error": res.get("error")}
        except Exception as e:
            logger.error(f"get_subgraph failed: {e}")
            return {"success": False, "error": str(e)}

    def shortest_path(
        self,
        graph_name: str,
        start_vertex: str,
        end_vertex: str,
        direction: str = "out",
    ) -> Dict[str, Any]:
        """
        Find the shortest path between two vertices in a graph.
        Args:
            graph_name: Name of the graph.
            start_vertex: _id of the start vertex.
            end_vertex: _id of the end vertex.
            direction: 'in', 'out', or 'any'.
        Returns:
            Dict with success, path, and error (if any).
        Example:
            >>> db.shortest_path('school', 'students/01', 'lectures/CSC101')
            # Returns: {'success': True, 'path': [...]} or {'success': False, 'error': ...}
        """
        try:
            query = """
            FOR v, e, p IN OUTBOUND SHORTEST_PATH @start_vertex TO @end_vertex GRAPH @graph_name
                RETURN {vertex: v, edge: e, path: p}
            """
            if direction == "in":
                query = query.replace("OUTBOUND", "INBOUND")
            elif direction == "any":
                query = query.replace("OUTBOUND", "ANY")
            bind_vars = {
                "start_vertex": start_vertex,
                "end_vertex": end_vertex,
                "graph_name": graph_name,
            }
            res = self.execute_aql(query, bind_vars)
            if res.get("success"):
                path = [item["vertex"] for item in res["results"] if "vertex" in item]
                return {"success": True, "path": path}
            return {"success": False, "error": res.get("error")}
        except Exception as e:
            logger.error(f"shortest_path failed: {e}")
            return {"success": False, "error": str(e)}

    # ==================== ASYNC GRAPH ANALYTICS (STUBS) ====================
    # True async support will be added if/when python-arango supports it. For high-throughput, use batch execution.

    async def aget_neighbors(self, *args, **kwargs):
        """Async get_neighbors (not implemented, python-arango does not support async as of July 2024).
        For high-throughput analytics, use batch execution context manager instead.
        """
        raise NotImplementedError(
            "Async graph analytics not supported by python-arango."
        )

    async def aget_subgraph(self, *args, **kwargs):
        """Async get_subgraph (not implemented, python-arango does not support async as of July 2024).
        For high-throughput analytics, use batch execution context manager instead.
        """
        raise NotImplementedError(
            "Async graph analytics not supported by python-arango."
        )

    async def ashortest_path(self, *args, **kwargs):
        """Async shortest_path (not implemented, python-arango does not support async as of July 2024).
        For high-throughput analytics, use batch execution context manager instead.
        """
        raise NotImplementedError(
            "Async graph analytics not supported by python-arango."
        )


# Quick manual tests for analytics helpers (not full unit tests)
if __name__ == "__main__":
    # Example manual test (requires running ArangoDB and a sample graph)
    db = DirectArangoDB()
    print("Neighbors:", db.get_neighbors("school", "students/01", direction="out"))
    print("Subgraph:", db.get_subgraph("school", "students/01", depth=2))
    print(
        "Shortest Path:", db.shortest_path("school", "students/01", "lectures/CSC101")
    )

# TODO: Add/extend unit tests for analytics helpers in test_arango_interface.py or similar.
