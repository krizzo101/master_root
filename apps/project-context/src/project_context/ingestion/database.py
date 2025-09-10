"""Database interface for ingestion pipeline."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg
import structlog

from ..models.common import BatchProcessingResult, ContextItem, ContextRelationship

logger = structlog.get_logger(__name__)


class DatabaseError(Exception):
    """Database operation error."""

    pass


class DatabaseConnectionPool:
    """Async database connection pool for ingestion operations."""

    def __init__(
        self,
        database_url: str,
        min_connections: int = 5,
        max_connections: int = 20,
        command_timeout: int = 60,
    ):
        """Initialize connection pool.

        Args:
            database_url: PostgreSQL connection URL
            min_connections: Minimum pool size
            max_connections: Maximum pool size
            command_timeout: Command timeout in seconds
        """
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        self._pool: Optional[asyncpg.Pool] = None
        self.logger = logger.bind(component="database_pool")

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.command_timeout,
                server_settings={
                    "jit": "off",  # Disable JIT for better performance with short queries
                    "application_name": "unified_context_ingestion",
                },
            )
            self.logger.info(
                "Database connection pool initialized",
                min_connections=self.min_connections,
                max_connections=self.max_connections,
            )
        except Exception as e:
            self.logger.error("Failed to initialize database pool", error=str(e))
            raise DatabaseError(f"Database pool initialization failed: {e}")

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self.logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection from the pool."""
        if not self._pool:
            raise DatabaseError("Database pool not initialized")

        async with self._pool.acquire() as connection:
            yield connection

    @asynccontextmanager
    async def transaction(self):
        """Acquire a database connection and start a transaction."""
        async with self.acquire() as connection:
            async with connection.transaction():
                yield connection

    async def execute_query(self, query: str, *args, fetch: str = "none") -> Any:
        """Execute a query with automatic connection management.

        Args:
            query: SQL query to execute
            *args: Query parameters
            fetch: 'none', 'one', 'all', or 'val'

        Returns:
            Query result based on fetch parameter
        """
        async with self.acquire() as connection:
            if fetch == "none":
                return await connection.execute(query, *args)
            elif fetch == "one":
                return await connection.fetchrow(query, *args)
            elif fetch == "all":
                return await connection.fetch(query, *args)
            elif fetch == "val":
                return await connection.fetchval(query, *args)
            else:
                raise ValueError(f"Invalid fetch type: {fetch}")


class IngestionDatabase:
    """High-level database operations for ingestion pipeline."""

    def __init__(self, pool: DatabaseConnectionPool):
        """Initialize with database pool."""
        self.pool = pool
        self.logger = logger.bind(component="ingestion_database")

    async def store_context_items(
        self, items: List[ContextItem], batch_size: int = 1000
    ) -> BatchProcessingResult:
        """Store context items in batches with comprehensive error handling.

        Args:
            items: List of ContextItem objects to store
            batch_size: Items per batch

        Returns:
            BatchProcessingResult with operation details
        """
        start_time = datetime.utcnow()
        result = BatchProcessingResult(total_items=len(items))

        try:
            # Process in batches
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]

                try:
                    async with self.pool.transaction() as conn:
                        batch_result = await self._store_batch(conn, batch)

                        result.processed_items += batch_result["processed"]
                        result.failed_items += batch_result["failed"]
                        result.duplicate_items += batch_result["duplicates"]
                        result.errors.extend(batch_result["errors"])

                except Exception as e:
                    self.logger.error(
                        "Batch storage failed",
                        batch_start=i,
                        batch_size=len(batch),
                        error=str(e),
                    )
                    result.failed_items += len(batch)
                    result.errors.append(
                        {"batch_start": i, "batch_size": len(batch), "error": str(e)}
                    )

            # Calculate metrics
            end_time = datetime.utcnow()
            result.processing_time_seconds = (end_time - start_time).total_seconds()

            self.logger.info(
                "Context items storage completed",
                total_items=result.total_items,
                processed_items=result.processed_items,
                failed_items=result.failed_items,
                processing_time=result.processing_time_seconds,
            )

            return result

        except Exception as e:
            self.logger.error("Context items storage failed", error=str(e))
            result.failed_items = len(items)
            result.errors.append({"error": str(e)})
            return result

    async def _store_batch(
        self, conn: asyncpg.Connection, items: List[ContextItem]
    ) -> Dict[str, Any]:
        """Store a single batch of items."""
        processed = 0
        failed = 0
        duplicates = 0
        errors = []

        # Prepare batch insert query
        insert_query = """
            INSERT INTO context_items (
                id, source_type, source_id, entity_type, timestamp, timestamp_end,
                ingested_at, title, content, content_hash, summary, project_id,
                file_path, line_start, line_end, function_name, class_name,
                actor_id, actor_type, session_id, severity, tags, metrics,
                source_data, embedding, neo4j_node_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23,
                $24, $25, $26
            )
            ON CONFLICT (source_type, source_id)
            DO UPDATE SET
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                ingested_at = EXCLUDED.ingested_at,
                summary = EXCLUDED.summary,
                tags = EXCLUDED.tags,
                metrics = EXCLUDED.metrics
            RETURNING id, (xmax = 0) as inserted
        """

        for item in items:
            try:
                # Convert item to parameters
                params = [
                    item.id,
                    item.source_type,
                    item.source_id,
                    item.entity_type,
                    item.timestamp,
                    item.timestamp_end,
                    item.ingested_at,
                    item.title,
                    item.content,
                    item.content_hash,
                    item.summary,
                    item.project_id,
                    item.file_path,
                    item.line_start,
                    item.line_end,
                    item.function_name,
                    item.class_name,
                    item.actor_id,
                    item.actor_type,
                    item.session_id,
                    item.severity,
                    item.tags or [],
                    item.metrics or {},
                    item.source_data or {},
                    item.embedding,
                    item.neo4j_node_id,
                ]

                # Execute insert
                row = await conn.fetchrow(insert_query, *params)

                if row["inserted"]:
                    processed += 1
                else:
                    duplicates += 1

                # Update item with database ID if it was generated
                if row["id"] != item.id:
                    item.id = row["id"]

            except Exception as e:
                failed += 1
                errors.append({"item_source_id": item.source_id, "error": str(e)})
                self.logger.warning(
                    "Failed to store context item",
                    source_id=item.source_id,
                    error=str(e),
                )

        return {
            "processed": processed,
            "failed": failed,
            "duplicates": duplicates,
            "errors": errors,
        }

    async def store_relationships(
        self, relationships: List[ContextRelationship], batch_size: int = 1000
    ) -> BatchProcessingResult:
        """Store context relationships in batches.

        Args:
            relationships: List of ContextRelationship objects
            batch_size: Relationships per batch

        Returns:
            BatchProcessingResult with operation details
        """
        start_time = datetime.utcnow()
        result = BatchProcessingResult(total_items=len(relationships))

        try:
            # Process in batches
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i : i + batch_size]

                try:
                    async with self.pool.transaction() as conn:
                        batch_result = await self._store_relationship_batch(conn, batch)

                        result.processed_items += batch_result["processed"]
                        result.failed_items += batch_result["failed"]
                        result.duplicate_items += batch_result["duplicates"]
                        result.errors.extend(batch_result["errors"])

                except Exception as e:
                    self.logger.error(
                        "Relationship batch storage failed",
                        batch_start=i,
                        batch_size=len(batch),
                        error=str(e),
                    )
                    result.failed_items += len(batch)
                    result.errors.append(
                        {"batch_start": i, "batch_size": len(batch), "error": str(e)}
                    )

            # Calculate metrics
            end_time = datetime.utcnow()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
            result.relationships_created = result.processed_items

            return result

        except Exception as e:
            self.logger.error("Relationship storage failed", error=str(e))
            result.failed_items = len(relationships)
            result.errors.append({"error": str(e)})
            return result

    async def _store_relationship_batch(
        self, conn: asyncpg.Connection, relationships: List[ContextRelationship]
    ) -> Dict[str, Any]:
        """Store a single batch of relationships."""
        processed = 0
        failed = 0
        duplicates = 0
        errors = []

        insert_query = """
            INSERT INTO context_relationships (
                id, source_id, target_id, relationship_type, confidence,
                metadata, created_at, created_by, temporal_context,
                time_delta_seconds, validation_status, validation_score,
                neo4j_relationship_id
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            ON CONFLICT (source_id, target_id, relationship_type)
            DO UPDATE SET
                confidence = EXCLUDED.confidence,
                metadata = EXCLUDED.metadata,
                validation_status = EXCLUDED.validation_status,
                validation_score = EXCLUDED.validation_score
            RETURNING id, (xmax = 0) as inserted
        """

        for rel in relationships:
            try:
                params = [
                    rel.id,
                    rel.source_id,
                    rel.target_id,
                    rel.relationship_type,
                    rel.confidence,
                    rel.metadata or {},
                    rel.created_at,
                    rel.created_by,
                    rel.temporal_context,
                    rel.time_delta_seconds,
                    rel.validation_status,
                    rel.validation_score,
                    rel.neo4j_relationship_id,
                ]

                row = await conn.fetchrow(insert_query, *params)

                if row["inserted"]:
                    processed += 1
                else:
                    duplicates += 1

                # Update relationship with database ID
                if row["id"] != rel.id:
                    rel.id = row["id"]

            except Exception as e:
                failed += 1
                errors.append(
                    {
                        "relationship_type": rel.relationship_type,
                        "source_id": str(rel.source_id),
                        "target_id": str(rel.target_id),
                        "error": str(e),
                    }
                )
                self.logger.warning(
                    "Failed to store relationship",
                    relationship_type=rel.relationship_type,
                    error=str(e),
                )

        return {
            "processed": processed,
            "failed": failed,
            "duplicates": duplicates,
            "errors": errors,
        }

    async def get_recent_items(
        self,
        source_types: Optional[List[str]] = None,
        limit: int = 1000,
        since: Optional[datetime] = None,
    ) -> List[ContextItem]:
        """Get recent context items for relationship detection.

        Args:
            source_types: Filter by source types
            limit: Maximum items to return
            since: Items newer than this timestamp

        Returns:
            List of ContextItem objects
        """
        query = """
            SELECT id, source_type, source_id, entity_type, timestamp, timestamp_end,
                   ingested_at, title, content, content_hash, summary, project_id,
                   file_path, line_start, line_end, function_name, class_name,
                   actor_id, actor_type, session_id, severity, tags, metrics,
                   source_data, embedding, neo4j_node_id
            FROM context_items
            WHERE ($1::text[] IS NULL OR source_type = ANY($1))
              AND ($2::timestamptz IS NULL OR timestamp >= $2)
            ORDER BY timestamp DESC
            LIMIT $3
        """

        try:
            rows = await self.pool.execute_query(
                query, source_types, since, limit, fetch="all"
            )

            items = []
            for row in rows:
                item = ContextItem(
                    id=row["id"],
                    source_type=row["source_type"],
                    source_id=row["source_id"],
                    entity_type=row["entity_type"],
                    timestamp=row["timestamp"],
                    timestamp_end=row["timestamp_end"],
                    ingested_at=row["ingested_at"],
                    title=row["title"],
                    content=row["content"],
                    content_hash=row["content_hash"],
                    summary=row["summary"],
                    project_id=row["project_id"],
                    file_path=row["file_path"],
                    line_start=row["line_start"],
                    line_end=row["line_end"],
                    function_name=row["function_name"],
                    class_name=row["class_name"],
                    actor_id=row["actor_id"],
                    actor_type=row["actor_type"],
                    session_id=row["session_id"],
                    severity=row["severity"],
                    tags=row["tags"] or [],
                    metrics=row["metrics"] or {},
                    source_data=row["source_data"] or {},
                    embedding=row["embedding"],
                    neo4j_node_id=row["neo4j_node_id"],
                )
                items.append(item)

            return items

        except Exception as e:
            self.logger.error("Failed to get recent items", error=str(e))
            raise DatabaseError(f"Failed to get recent items: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check.

        Returns:
            Health check results
        """
        try:
            start_time = datetime.utcnow()

            # Test basic connectivity
            result = await self.pool.execute_query("SELECT 1", fetch="val")

            # Test table access
            count = await self.pool.execute_query(
                "SELECT COUNT(*) FROM context_items", fetch="val"
            )

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "total_items": count,
                "pool_size": self.pool._pool.get_size() if self.pool._pool else 0,
                "pool_idle": self.pool._pool.get_idle_size() if self.pool._pool else 0,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
