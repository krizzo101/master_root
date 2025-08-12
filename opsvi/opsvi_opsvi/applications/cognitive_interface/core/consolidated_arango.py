"""
Consolidated ArangoDB Interface - Core Implementation
Eliminates AQL complexity with agent-friendly parameter-based routing
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from arango import ArangoClient
from arango.exceptions import ArangoError

logger = logging.getLogger(__name__)


class ConsolidatedArangoDB:
    """
    Main database abstraction providing 3 consolidated tools:
    - arango_search: All search/query operations
    - arango_modify: All CRUD operations
    - arango_manage: All admin operations
    """

    def __init__(
        self,
        host: str = None,
        database: str = None,
        username: str = None,
        password: str = None,
    ):
        """Initialize with configuration from environment variables or defaults"""

        # Use environment variables if available, otherwise use defaults for Agent-IDE database
        self.host = host or os.getenv("ARANGO_URL", "http://127.0.0.1:8550")
        self.database_name = database or os.getenv("ARANGO_DB", "_system")
        self.username = username or os.getenv("ARANGO_USERNAME", "root")
        self.password = password or os.getenv("ARANGO_PASSWORD", "change_me")

        # Agent-IDE collection mapping
        self.AGENT_IDE_COLLECTIONS = {
            "rules",
            "modules",
            "tasks",
            "branches",
            "research_docs",
            "heuristics",
            "metrics",
            "ide_state",
            "user_prefs",
        }

        # Simplified search types for Agent-IDE (removed quality, related complexity)
        self.SEARCH_TYPES = {"content", "tags", "date_range", "type", "recent", "id"}

        # Agent-IDE graph name
        self.GRAPH_NAME = "projectGraph"

        # Initialize connection
        self.client = ArangoClient(hosts=self.host)
        self.db = self.client.db(
            self.database_name, username=self.username, password=self.password
        )

        # Validate connection
        self._validate_connection()
        logger.info(
            f"ConsolidatedArangoDB initialized: {self.host}/{self.database_name}"
        )

    def _validate_connection(self) -> bool:
        """Validate database connection and core collections"""
        try:
            collections = self.db.collections()
            logger.info(f"Connected to database with {len(collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            raise ConnectionError(f"Cannot connect to ArangoDB: {e}")

    # ==================== SEARCH OPERATIONS ====================

    def search(self, search_type: str, collection: str, **kwargs) -> dict[str, Any]:
        """
        Unified search interface with type-based routing

        search_types: content, tags, date_range, type, recent, id
        """
        try:
            logger.debug(f"Search: {search_type} in {collection} with {kwargs}")

            # Validate collection exists and is Agent-IDE collection
            if not self.db.has_collection(collection):
                return self._error_response(f"Collection '{collection}' does not exist")

            if collection not in self.AGENT_IDE_COLLECTIONS:
                logger.warning(
                    f"Collection '{collection}' not in Agent-IDE schema, proceeding anyway"
                )

            # Agent-IDE search engine routing (simplified)
            search_engines = {
                "content": self._search_content,
                "tags": self._search_tags,
                "date_range": self._search_date_range,
                "type": self._search_type,
                "recent": self._search_recent,
                "id": self._search_by_id,
            }

            # Validate search type for Agent-IDE
            if search_type not in self.SEARCH_TYPES:
                return self._error_response(
                    f"Search type '{search_type}' not supported in Agent-IDE. Available: {list(self.SEARCH_TYPES)}"
                )

            engine = search_engines.get(search_type)
            if not engine:
                return self._error_response(f"Unknown search_type: {search_type}")

            return engine(collection, **kwargs)

        except Exception as e:
            logger.error(f"Search operation failed: {e}")
            return self._error_response(f"Search failed: {str(e)}")

    def _search_content(
        self,
        collection: str,
        content: str,
        fields: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search for content across document fields"""

        if not content or len(content) < 2:
            return self._error_response("Content query must be at least 2 characters")

        # Build field filters
        if fields:
            field_conditions = " OR ".join(
                [f"CONTAINS(LOWER(doc.{field}), @content)" for field in fields]
            )
        else:
            # Agent-IDE default fields for content search
            field_conditions = """
                CONTAINS(LOWER(doc.content), @content) OR
                CONTAINS(LOWER(doc.title), @content) OR
                CONTAINS(LOWER(doc.description), @content) OR
                CONTAINS(LOWER(doc.name), @content) OR
                CONTAINS(LOWER(doc.pattern), @content)
            """

        query = f"""
        FOR doc IN {collection}
          FILTER {field_conditions}
          SORT doc.created DESC
          LIMIT @limit
          RETURN doc
        """

        bind_vars = {"content": content.lower(), "limit": limit}
        return self._execute_query(query, bind_vars, "content_search")

    def _search_tags(
        self, collection: str, tags: list[str], match_all: bool = False, limit: int = 20
    ) -> dict[str, Any]:
        """Search documents by tags with AND/OR logic"""

        if not tags:
            return self._error_response("Tags list cannot be empty")

        if match_all:
            # ALL tags must match (AND logic)
            tag_conditions = " AND ".join(
                [f"@tag{i} IN doc.tags" for i, _ in enumerate(tags)]
            )
            bind_vars = {f"tag{i}": tag for i, tag in enumerate(tags)}
        else:
            # ANY tag matches (OR logic)
            tag_conditions = "LENGTH(INTERSECTION(doc.tags, @tags)) > 0"
            bind_vars = {"tags": tags}

        bind_vars["limit"] = limit

        query = f"""
        FOR doc IN {collection}
          FILTER doc.tags != null AND {tag_conditions}
          SORT doc.created DESC
          LIMIT @limit
          RETURN doc
        """

        return self._execute_query(query, bind_vars, "tag_search")

    def _search_date_range(
        self,
        collection: str,
        start_date: str,
        end_date: str,
        date_field: str = "created",
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search documents within date range"""

        query = f"""
        FOR doc IN {collection}
          FILTER doc.{date_field} >= @start_date AND doc.{date_field} <= @end_date
          SORT doc.{date_field} DESC
          LIMIT @limit
          RETURN doc
        """

        bind_vars = {"start_date": start_date, "end_date": end_date, "limit": limit}

        return self._execute_query(query, bind_vars, "date_range_search")

    def _search_type(
        self, collection: str, document_type: str, limit: int = 30
    ) -> dict[str, Any]:
        """Search documents by type field"""

        query = f"""
        FOR doc IN {collection}
          FILTER doc.type == @doc_type OR doc.document_type == @doc_type
          SORT doc.created DESC
          LIMIT @limit
          RETURN doc
        """

        bind_vars = {"doc_type": document_type, "limit": limit}
        return self._execute_query(query, bind_vars, "type_search")

    def _search_recent(
        self, collection: str, limit: int = 20, hours: int = 24
    ) -> dict[str, Any]:
        """Get recent documents within time window"""

        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        query = f"""
        FOR doc IN {collection}
          FILTER doc.created >= @cutoff_time
          SORT doc.created DESC
          LIMIT @limit
          RETURN doc
        """

        bind_vars = {"cutoff_time": cutoff_time, "limit": limit}
        return self._execute_query(query, bind_vars, "recent_search")

    # Quality and related search methods removed - not needed for Agent-IDE schema
    # Agent-IDE uses simple confidence scores in documents and tags for relationships

    def _search_by_id(self, collection: str, document_id: str) -> dict[str, Any]:
        """Direct document lookup by ID"""

        query = f"""
        FOR doc IN {collection}
          FILTER doc._id == @doc_id OR doc._key == @doc_id
          RETURN doc
        """

        bind_vars = {"doc_id": document_id}
        return self._execute_query(query, bind_vars, "id_search")

    # ==================== MODIFY OPERATIONS ====================

    def modify(self, operation: str, collection: str, **kwargs) -> dict[str, Any]:
        """
        Unified modification interface with operation-based routing

        operations: insert, update, delete, upsert
        """
        try:
            logger.debug(f"Modify: {operation} in {collection} with {kwargs}")

            # Validate collection exists (except for insert which can create)
            if operation != "insert" and not self.db.has_collection(collection):
                return self._error_response(f"Collection '{collection}' does not exist")

            # Route to appropriate modify engine
            modify_engines = {
                "insert": self._modify_insert,
                "update": self._modify_update,
                "delete": self._modify_delete,
                "upsert": self._modify_upsert,
            }

            engine = modify_engines.get(operation)
            if not engine:
                return self._error_response(f"Unknown operation: {operation}")

            return engine(collection, **kwargs)

        except Exception as e:
            logger.error(f"Modify operation failed: {e}")
            return self._error_response(f"Modify failed: {str(e)}")

    def _modify_insert(
        self, collection: str, document: dict[str, Any], validate_schema: bool = True
    ) -> dict[str, Any]:
        """Insert new document with optional validation"""

        if not document:
            return self._error_response("Document cannot be empty")

        # Add timestamps
        if "created" not in document:
            document["created"] = datetime.now().isoformat()
        if "updated" not in document:
            document["updated"] = document["created"]

        try:
            # Ensure collection exists
            if not self.db.has_collection(collection):
                self.db.create_collection(collection)

            coll = self.db.collection(collection)
            result = coll.insert(document)

            return {
                "success": True,
                "operation": "insert",
                "collection": collection,
                "document_id": result["_id"],
                "document_key": result["_key"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Insert failed: {str(e)}")

    def _modify_update(
        self,
        collection: str,
        key: str | None = None,
        criteria: dict | None = None,
        updates: dict[str, Any] = None,
        upsert: bool = False,
    ) -> dict[str, Any]:
        """Update documents by key or criteria"""

        if not updates:
            return self._error_response("Updates dictionary cannot be empty")

        # Add update timestamp
        updates["updated"] = datetime.now().isoformat()

        try:
            coll = self.db.collection(collection)

            if key:
                # Update by document key
                result = coll.update(
                    {"_key": key}, updates, merge=True, return_new=True
                )
                return {
                    "success": True,
                    "operation": "update",
                    "collection": collection,
                    "updated_count": 1,
                    "document_id": result["_id"],
                    "timestamp": datetime.now().isoformat(),
                }

            elif criteria:
                # Update by criteria using AQL
                query = f"""
                FOR doc IN {collection}
                  FILTER {self._build_filter_conditions(criteria)}
                  UPDATE doc WITH @updates IN {collection}
                  RETURN NEW
                """

                bind_vars = {"updates": updates}
                bind_vars.update(criteria)

                results = self._execute_query(query, bind_vars, "criteria_update")
                return {
                    "success": True,
                    "operation": "update",
                    "collection": collection,
                    "updated_count": len(results.get("results", [])),
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                return self._error_response(
                    "Either 'key' or 'criteria' must be provided for update"
                )

        except Exception as e:
            return self._error_response(f"Update failed: {str(e)}")

    def _modify_delete(
        self,
        collection: str,
        key: str | None = None,
        criteria: dict | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Delete documents by key or criteria with confirmation"""

        if not confirm:
            return self._error_response(
                "Delete operations require confirm=True for safety"
            )

        try:
            coll = self.db.collection(collection)

            if key:
                # Delete by document key
                result = coll.delete({"_key": key})
                return {
                    "success": True,
                    "operation": "delete",
                    "collection": collection,
                    "deleted_count": 1,
                    "document_id": result["_id"],
                    "timestamp": datetime.now().isoformat(),
                }

            elif criteria:
                # Delete by criteria using AQL
                query = f"""
                FOR doc IN {collection}
                  FILTER {self._build_filter_conditions(criteria)}
                  REMOVE doc IN {collection}
                  RETURN OLD
                """

                bind_vars = dict(criteria)
                results = self._execute_query(query, bind_vars, "criteria_delete")

                return {
                    "success": True,
                    "operation": "delete",
                    "collection": collection,
                    "deleted_count": len(results.get("results", [])),
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                return self._error_response(
                    "Either 'key' or 'criteria' must be provided for delete"
                )

        except Exception as e:
            return self._error_response(f"Delete failed: {str(e)}")

    def _modify_upsert(
        self, collection: str, document: dict[str, Any], match_fields: list[str]
    ) -> dict[str, Any]:
        """Insert or update based on matching fields"""

        if not document or not match_fields:
            return self._error_response(
                "Document and match_fields are required for upsert"
            )

        # Build match criteria
        match_criteria = {
            field: document.get(field) for field in match_fields if field in document
        }
        if not match_criteria:
            return self._error_response(
                "Document must contain at least one match_field"
            )

        try:
            # Check if document exists
            existing = self._search_by_criteria(collection, match_criteria)

            if existing.get("results"):
                # Update existing document
                existing_key = existing["results"][0]["_key"]
                return self._modify_update(
                    collection, key=existing_key, updates=document
                )
            else:
                # Insert new document
                return self._modify_insert(collection, document)

        except Exception as e:
            return self._error_response(f"Upsert failed: {str(e)}")

    def _search_by_criteria(
        self, collection: str, criteria: dict[str, Any]
    ) -> dict[str, Any]:
        """Helper: Search documents by exact criteria match"""

        query = f"""
        FOR doc IN {collection}
          FILTER {self._build_filter_conditions(criteria)}
          RETURN doc
        """

        bind_vars = dict(criteria)
        return self._execute_query(query, bind_vars, "criteria_search")

    # ==================== MANAGE OPERATIONS ====================

    def manage(self, action: str, **kwargs) -> dict[str, Any]:
        """
        Unified management interface with action-based routing

        actions: collection_info, backup, health, count, exists, create_collection
        """
        try:
            logger.debug(f"Manage: {action} with {kwargs}")

            # Route to appropriate manage engine
            manage_engines = {
                "collection_info": self._manage_collection_info,
                # "backup": self._manage_backup,  # DISABLED - incomplete implementation
                "health": self._manage_health,
                "count": self._manage_count,
                "exists": self._manage_exists,
                "create_collection": self._manage_create_collection,
            }

            engine = manage_engines.get(action)
            if not engine:
                return self._error_response(f"Unknown action: {action}")

            return engine(**kwargs)

        except Exception as e:
            logger.error(f"Manage operation failed: {e}")
            return self._error_response(f"Manage failed: {str(e)}")

    def _manage_collection_info(self, collection: str) -> dict[str, Any]:
        """Get detailed collection information and statistics"""

        if not self.db.has_collection(collection):
            return self._error_response(f"Collection '{collection}' does not exist")

        try:
            coll = self.db.collection(collection)
            properties = coll.properties()

            # Use direct count method instead of statistics
            doc_count = coll.count()

            return {
                "success": True,
                "action": "collection_info",
                "collection": collection,
                "info": {
                    "name": properties["name"],
                    "type": properties["type"],
                    "status": properties["status"],
                    "count": doc_count,
                    "indexes": len(coll.indexes()),
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Collection info failed: {str(e)}")

    def _manage_backup(
        self, collections: list[str] | None = None, output_dir: str = "./backup"
    ) -> dict[str, Any]:
        """Backup collections to specified directory"""

        try:
            if not collections:
                # Backup all collections
                all_collections = [c["name"] for c in self.db.collections()]
                collections = [c for c in all_collections if not c.startswith("_")]

            backup_info = []

            for collection_name in collections:
                if self.db.has_collection(collection_name):
                    coll = self.db.collection(collection_name)
                    documents = list(coll.all())

                    backup_info.append(
                        {
                            "collection": collection_name,
                            "document_count": len(documents),
                            "backup_file": f"{output_dir}/{collection_name}.json",
                        }
                    )

            return {
                "success": True,
                "action": "backup",
                "backed_up_collections": len(backup_info),
                "collections": backup_info,
                "output_directory": output_dir,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Backup failed: {str(e)}")

    def _manage_health(self) -> dict[str, Any]:
        """Agent-IDE database health assessment"""

        try:
            # Check specifically for Agent-IDE collections
            collection_stats = {}
            total_documents = 0
            missing_collections = []

            for coll_name in self.AGENT_IDE_COLLECTIONS:
                if self.db.has_collection(coll_name):
                    coll = self.db.collection(coll_name)
                    count = coll.count()
                    collection_stats[coll_name] = count
                    total_documents += count
                else:
                    missing_collections.append(coll_name)
                    collection_stats[coll_name] = 0

            # Agent-IDE health score based on collection presence and data
            collections_present = len(self.AGENT_IDE_COLLECTIONS) - len(
                missing_collections
            )
            collection_health = collections_present / len(self.AGENT_IDE_COLLECTIONS)
            data_health = min(1.0, total_documents / 100)  # Reasonable for Agent-IDE
            health_score = (collection_health + data_health) / 2

            result = {
                "success": True,
                "action": "health",
                "database": self.database_name,
                "health_score": health_score,
                "total_collections": len(collection_stats),
                "total_documents": total_documents,
                "collections": collection_stats,
                "timestamp": datetime.now().isoformat(),
            }

            if missing_collections:
                result["missing_collections"] = missing_collections
                result[
                    "warning"
                ] = f"Missing Agent-IDE collections: {missing_collections}"

            return result

        except Exception as e:
            return self._error_response(f"Health check failed: {str(e)}")

    def _manage_count(
        self, collection: str, criteria: dict | None = None
    ) -> dict[str, Any]:
        """Count documents in collection with optional criteria"""

        if not self.db.has_collection(collection):
            return self._error_response(f"Collection '{collection}' does not exist")

        try:
            if criteria:
                # Count with criteria
                query = f"""
                FOR doc IN {collection}
                  FILTER {self._build_filter_conditions(criteria)}
                  COLLECT WITH COUNT INTO count
                  RETURN count
                """

                bind_vars = dict(criteria)
                result = self._execute_query(query, bind_vars, "count_with_criteria")
                count = result.get("results", [0])[0] if result.get("results") else 0
            else:
                # Simple count
                coll = self.db.collection(collection)
                count = coll.count()

            return {
                "success": True,
                "action": "count",
                "collection": collection,
                "count": count,
                "criteria": criteria,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Count failed: {str(e)}")

    def _manage_exists(
        self, collection: str, criteria: dict[str, Any]
    ) -> dict[str, Any]:
        """Check if documents matching criteria exist"""

        if not self.db.has_collection(collection):
            return self._error_response(f"Collection '{collection}' does not exist")

        try:
            query = f"""
            FOR doc IN {collection}
              FILTER {self._build_filter_conditions(criteria)}
              LIMIT 1
              RETURN doc._id
            """

            bind_vars = dict(criteria)
            result = self._execute_query(query, bind_vars, "exists_check")

            exists = len(result.get("results", [])) > 0

            return {
                "success": True,
                "action": "exists",
                "collection": collection,
                "exists": exists,
                "criteria": criteria,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Exists check failed: {str(e)}")

    def _manage_create_collection(
        self, name: str, collection_type: str = "document"
    ) -> dict[str, Any]:
        """Create new collection"""

        if self.db.has_collection(name):
            return self._error_response(f"Collection '{name}' already exists")

        try:
            if collection_type == "edge":
                coll = self.db.create_collection(name, edge=True)
            else:
                coll = self.db.create_collection(name)

            return {
                "success": True,
                "action": "create_collection",
                "collection": name,
                "type": collection_type,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Collection creation failed: {str(e)}")

    # ==================== HELPER METHODS ====================

    def _build_filter_conditions(self, criteria: dict[str, Any]) -> str:
        """Build AQL filter conditions from criteria dictionary"""

        conditions = []
        for field, value in criteria.items():
            if isinstance(value, str) or isinstance(value, (int, float)):
                conditions.append(f"doc.{field} == @{field}")
            elif isinstance(value, list):
                conditions.append(f"doc.{field} IN @{field}")
            else:
                conditions.append(f"doc.{field} == @{field}")

        return " AND ".join(conditions)

    def _execute_query(
        self, query: str, bind_vars: dict[str, Any], operation_name: str
    ) -> dict[str, Any]:
        """Execute AQL query with comprehensive error handling"""

        try:
            logger.debug(f"Executing {operation_name}: {query}")
            logger.debug(f"Bind vars: {bind_vars}")

            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)

            logger.debug(f"{operation_name} returned {len(results)} results")

            return {
                "success": True,
                "operation": operation_name,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat(),
            }

        except ArangoError as e:
            logger.error(f"AQL error in {operation_name}: {e}")
            return self._error_response(f"Database query failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error in {operation_name}: {e}")
            return self._error_response(f"Query execution failed: {str(e)}")

    def _error_response(self, message: str) -> dict[str, Any]:
        """Standardized error response format"""

        return {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat(),
        }
