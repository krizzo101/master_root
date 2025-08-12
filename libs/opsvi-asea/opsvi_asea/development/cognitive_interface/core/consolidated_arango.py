"""
Consolidated ArangoDB Interface - Core Implementation
Eliminates AQL complexity with agent-friendly parameter-based routing
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
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
        host: str = "http://127.0.0.1:8530",
        database: str = "asea_v2_db",
        username: str = "root",
        password: str = "asea_dev_password_v2",
    ):
        """Initialize with V2 ASEA database configuration"""

        self.host = host
        self.database_name = database
        self.username = username
        self.password = password

        # Initialize connection
        self.client = ArangoClient(hosts=host)
        self.db = self.client.db(database, username=username, password=password)

        # Validate connection
        self._validate_connection()
        logger.info(f"ConsolidatedArangoDB initialized: {host}/{database}")

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

    def search(self, search_type: str, collection: str, **kwargs) -> Dict[str, Any]:
        """
        Unified search interface with type-based routing

        search_types: content, tags, date_range, type, recent, quality, related, id
        """
        try:
            logger.debug(f"Search: {search_type} in {collection} with {kwargs}")

            # Validate collection exists
            if not self.db.has_collection(collection):
                return self._error_response(f"Collection '{collection}' does not exist")

            # Route to appropriate search engine
            search_engines = {
                "content": self._search_content,
                "tags": self._search_tags,
                "date_range": self._search_date_range,
                "type": self._search_type,
                "recent": self._search_recent,
                "quality": self._search_quality,
                "related": self._search_related,
                "id": self._search_by_id,
            }

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
        fields: Optional[List[str]] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Search for content across document fields"""

        if not content or len(content) < 2:
            return self._error_response("Content query must be at least 2 characters")

        # Build field filters
        if fields:
            field_conditions = " OR ".join(
                [f"CONTAINS(LOWER(doc.{field}), @content)" for field in fields]
            )
        else:
            # Default fields for content search
            field_conditions = """
                CONTAINS(LOWER(doc.content), @content) OR
                CONTAINS(LOWER(doc.title), @content) OR
                CONTAINS(LOWER(doc.description), @content) OR
                CONTAINS(LOWER(doc.text), @content)
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
        self, collection: str, tags: List[str], match_all: bool = False, limit: int = 20
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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

    def _search_quality(
        self,
        collection: str,
        min_quality: float,
        quality_field: str = "quality_score",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Search documents above quality threshold"""

        query = f"""
        FOR doc IN {collection}
          FILTER doc.{quality_field} >= @min_quality
          SORT doc.{quality_field} DESC
          LIMIT @limit
          RETURN doc
        """

        bind_vars = {"min_quality": min_quality, "limit": limit}
        return self._execute_query(query, bind_vars, "quality_search")

    def _search_related(
        self,
        collection: str,
        reference_id: str,
        relationship_type: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Find documents related to reference document"""

        # First try semantic_relationships collection
        if relationship_type:
            relationship_filter = "AND rel.relationship_type == @rel_type"
            bind_vars = {
                "ref_id": reference_id,
                "rel_type": relationship_type,
                "limit": limit,
            }
        else:
            relationship_filter = ""
            bind_vars = {"ref_id": reference_id, "limit": limit}

        query = f"""
        FOR rel IN semantic_relationships
          FILTER (rel._from == @ref_id OR rel._to == @ref_id) {relationship_filter}
          FOR doc IN {collection}
            FILTER doc._id == (rel._from == @ref_id ? rel._to : rel._from)
            LIMIT @limit
            RETURN doc
        """

        return self._execute_query(query, bind_vars, "related_search")

    def _search_by_id(self, collection: str, document_id: str) -> Dict[str, Any]:
        """Direct document lookup by ID"""

        query = f"""
        FOR doc IN {collection}
          FILTER doc._id == @doc_id OR doc._key == @doc_id
          RETURN doc
        """

        bind_vars = {"doc_id": document_id}
        return self._execute_query(query, bind_vars, "id_search")

    # ==================== MODIFY OPERATIONS ====================

    def modify(self, operation: str, collection: str, **kwargs) -> Dict[str, Any]:
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
        self, collection: str, document: Dict[str, Any], validate_schema: bool = True
    ) -> Dict[str, Any]:
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
        key: Optional[str] = None,
        criteria: Optional[Dict] = None,
        updates: Dict[str, Any] = None,
        upsert: bool = False,
    ) -> Dict[str, Any]:
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
        key: Optional[str] = None,
        criteria: Optional[Dict] = None,
        confirm: bool = False,
    ) -> Dict[str, Any]:
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
        self, collection: str, document: Dict[str, Any], match_fields: List[str]
    ) -> Dict[str, Any]:
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
        self, collection: str, criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Helper: Search documents by exact criteria match"""

        query = f"""
        FOR doc IN {collection}
          FILTER {self._build_filter_conditions(criteria)}
          RETURN doc
        """

        bind_vars = dict(criteria)
        return self._execute_query(query, bind_vars, "criteria_search")

    # ==================== MANAGE OPERATIONS ====================

    def manage(self, action: str, **kwargs) -> Dict[str, Any]:
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

    def _manage_collection_info(self, collection: str) -> Dict[str, Any]:
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
        self, collections: Optional[List[str]] = None, output_dir: str = "./backup"
    ) -> Dict[str, Any]:
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

    def _manage_health(self) -> Dict[str, Any]:
        """Comprehensive database health assessment"""

        try:
            collections = self.db.collections()
            collection_stats = {}
            total_documents = 0

            for coll_info in collections:
                if not coll_info["name"].startswith("_"):
                    coll = self.db.collection(coll_info["name"])
                    count = coll.count()
                    collection_stats[coll_info["name"]] = count
                    total_documents += count

            health_score = min(1.0, total_documents / 1000)  # Basic health calculation

            return {
                "success": True,
                "action": "health",
                "database": self.database_name,
                "health_score": health_score,
                "total_collections": len(collection_stats),
                "total_documents": total_documents,
                "collections": collection_stats,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return self._error_response(f"Health check failed: {str(e)}")

    def _manage_count(
        self, collection: str, criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
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
        self, collection: str, criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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

    def _build_filter_conditions(self, criteria: Dict[str, Any]) -> str:
        """Build AQL filter conditions from criteria dictionary"""

        conditions = []
        for field, value in criteria.items():
            if isinstance(value, str):
                conditions.append(f"doc.{field} == @{field}")
            elif isinstance(value, (int, float)):
                conditions.append(f"doc.{field} == @{field}")
            elif isinstance(value, list):
                conditions.append(f"doc.{field} IN @{field}")
            else:
                conditions.append(f"doc.{field} == @{field}")

        return " AND ".join(conditions)

    def _execute_query(
        self, query: str, bind_vars: Dict[str, Any], operation_name: str
    ) -> Dict[str, Any]:
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

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Standardized error response format"""

        return {
            "success": False,
            "error": message,
            "timestamp": datetime.now().isoformat(),
        }
