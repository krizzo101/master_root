"""Enhanced database optimization system for chat import performance."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import asyncpg
import structlog
from asyncpg import Pool

from .performance_cache import PerformanceCacheManager

logger = structlog.get_logger(__name__)


class OptimizedDatabaseConnectionPool:
    """High-performance database connection pool with advanced optimization."""

    def __init__(
        self,
        database_url: str,
        min_connections: int = 10,
        max_connections: int = 100,
        command_timeout: int = 300,
        cache_manager: Optional[PerformanceCacheManager] = None,
    ):
        """Initialize optimized database pool."""
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        self.cache_manager = cache_manager

        self.pool: Optional[Pool] = None
        self.connection_stats = {
            "total_queries": 0,
            "total_duration": 0.0,
            "slowest_query": {"query": "", "duration": 0.0},
            "connection_errors": 0,
        }

    async def initialize(self):
        """Initialize the optimized connection pool."""
        try:
            # Optimized connection settings for high throughput
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.command_timeout,
                server_settings={
                    # Performance optimizations
                    "jit": "off",  # JIT can slow down short queries
                    "shared_preload_libraries": "pg_stat_statements,auto_explain",
                    "log_statement": "none",  # Reduce logging overhead
                    "log_min_duration_statement": "1000",  # Log slow queries only
                    # Connection optimizations
                    "tcp_keepalives_idle": "600",
                    "tcp_keepalives_interval": "30",
                    "tcp_keepalives_count": "3",
                    # Memory optimizations for bulk operations
                    "work_mem": "256MB",  # Increase for sorting/hashing
                    "maintenance_work_mem": "1GB",  # For index creation
                    "effective_cache_size": "4GB",  # Assume 4GB available
                    # Vacuum and analyze optimizations
                    "autovacuum_max_workers": "4",
                    "autovacuum_naptime": "30s",
                    # Application identification
                    "application_name": "optimized_chat_import_pool",
                },
            )

            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            logger.info(
                "Optimized database pool initialized",
                min_connections=self.min_connections,
                max_connections=self.max_connections,
            )

        except Exception as e:
            logger.error("Failed to initialize optimized pool", error=str(e))
            raise

    async def execute_query(
        self,
        query: str,
        *params,
        fetch: str = "all",
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
    ) -> Any:
        """Execute query with caching and performance tracking."""
        start_time = time.time()

        try:
            # Check cache first if enabled
            if use_cache and self.cache_manager and fetch != "none":
                cached_result = await self.cache_manager.query_cache.get(query, params)
                if cached_result is not None:
                    return cached_result

            # Execute query
            async with self.pool.acquire() as conn:
                if fetch == "all":
                    result = await conn.fetch(query, *params)
                    result = [dict(row) for row in result]
                elif fetch == "one":
                    result = await conn.fetchrow(query, *params)
                    result = dict(result) if result else None
                elif fetch == "val":
                    result = await conn.fetchval(query, *params)
                else:  # fetch == "none"
                    result = await conn.execute(query, *params)

            # Cache the result if appropriate
            if use_cache and self.cache_manager and fetch in ["all", "one"] and result:
                await self.cache_manager.query_cache.set(
                    query, params, result, ttl=cache_ttl
                )

            # Update statistics
            duration = time.time() - start_time
            self._update_query_stats(query, duration)

            return result

        except Exception as e:
            self.connection_stats["connection_errors"] += 1
            duration = time.time() - start_time
            logger.error(
                "Query execution failed",
                query=query[:100],
                duration=duration,
                error=str(e),
            )
            raise

    def _update_query_stats(self, query: str, duration: float):
        """Update internal query performance statistics."""
        self.connection_stats["total_queries"] += 1
        self.connection_stats["total_duration"] += duration

        if duration > self.connection_stats["slowest_query"]["duration"]:
            self.connection_stats["slowest_query"] = {
                "query": query[:200],
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def execute_batch(
        self, queries: List[Tuple[str, Tuple[Any, ...]]], use_transaction: bool = True
    ) -> List[Any]:
        """Execute multiple queries in a batch with optional transaction."""
        start_time = time.time()
        results = []

        try:
            async with self.pool.acquire() as conn:
                if use_transaction:
                    async with conn.transaction():
                        for query, params in queries:
                            result = await conn.execute(query, *params)
                            results.append(result)
                else:
                    for query, params in queries:
                        result = await conn.execute(query, *params)
                        results.append(result)

            duration = time.time() - start_time
            logger.debug(
                "Batch execution completed", query_count=len(queries), duration=duration
            )

            return results

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Batch execution failed",
                query_count=len(queries),
                duration=duration,
                error=str(e),
            )
            raise

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get detailed connection pool statistics."""
        if not self.pool:
            return {"error": "Pool not initialized"}

        avg_duration = self.connection_stats["total_duration"] / max(
            1, self.connection_stats["total_queries"]
        )

        return {
            "pool_size": self.pool.get_size(),
            "idle_connections": self.pool.get_idle_size(),
            "total_queries": self.connection_stats["total_queries"],
            "average_query_duration_ms": round(avg_duration * 1000, 2),
            "slowest_query": self.connection_stats["slowest_query"],
            "connection_errors": self.connection_stats["connection_errors"],
            "configuration": {
                "min_connections": self.min_connections,
                "max_connections": self.max_connections,
                "command_timeout": self.command_timeout,
            },
        }

    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()


class BatchInsertOptimizer:
    """Optimized batch insertion system for high-throughput chat import."""

    def __init__(
        self,
        pool: OptimizedDatabaseConnectionPool,
        batch_size: int = 1000,
        max_parallel_batches: int = 4,
    ):
        """Initialize batch insert optimizer."""
        self.pool = pool
        self.batch_size = batch_size
        self.max_parallel_batches = max_parallel_batches
        self.insertion_stats = {
            "total_items": 0,
            "total_batches": 0,
            "total_duration": 0.0,
            "errors": 0,
        }

    async def insert_context_items_batch(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimized batch insertion of context items."""
        if not items:
            return {"inserted": 0, "errors": 0}

        start_time = time.time()
        inserted_count = 0
        error_count = 0

        # Split items into optimal batch sizes
        batches = [
            items[i : i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        # Process batches in parallel
        semaphore = asyncio.Semaphore(self.max_parallel_batches)

        async def process_batch(batch: List[Dict[str, Any]]) -> Tuple[int, int]:
            async with semaphore:
                return await self._insert_single_batch(batch)

        batch_results = await asyncio.gather(
            *[process_batch(batch) for batch in batches], return_exceptions=True
        )

        # Aggregate results
        for result in batch_results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error("Batch insertion failed", error=str(result))
            else:
                batch_inserted, batch_errors = result
                inserted_count += batch_inserted
                error_count += batch_errors

        duration = time.time() - start_time
        self._update_insertion_stats(len(items), len(batches), duration, error_count)

        return {
            "inserted": inserted_count,
            "errors": error_count,
            "duration_seconds": duration,
            "batches_processed": len(batches),
            "items_per_second": round(inserted_count / max(0.1, duration), 2),
        }

    async def _insert_single_batch(
        self, items: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """Insert a single batch of items using COPY for maximum performance."""
        if not items:
            return 0, 0

        try:
            # Prepare data for COPY operation
            columns = [
                "source_type",
                "source_id",
                "title",
                "content",
                "file_path",
                "line_start",
                "line_end",
                "entity_type",
                "timestamp",
                "content_hash",
                "actor_id",
                "actor_type",
                "session_id",
                "project_id",
                "language",
                "source_data",
                "metrics",
                "tags",
                "embedding",
            ]

            # Convert items to rows for COPY
            rows = []
            for item in items:
                row = []
                for column in columns:
                    value = item.get(column)
                    if value is None:
                        row.append(None)
                    elif column in ["source_data", "metrics"]:
                        # JSON columns
                        row.append(json.dumps(value) if value else None)
                    elif column == "tags":
                        # Array column
                        row.append(value if isinstance(value, list) else None)
                    elif column == "embedding":
                        # Vector column
                        row.append(value if isinstance(value, list) else None)
                    else:
                        row.append(value)
                rows.append(tuple(row))

            # Execute COPY operation
            copy_query = f"""
                COPY context_items ({', '.join(columns)})
                FROM STDIN WITH (FORMAT BINARY)
            """

            async with self.pool.pool.acquire() as conn:
                result = await conn.copy_records_to_table(
                    "context_items", records=rows, columns=columns
                )

            # Parse result to get inserted count
            inserted_count = len(rows)  # COPY doesn't return count easily

            return inserted_count, 0

        except Exception as e:
            logger.error(
                "Single batch insertion failed", batch_size=len(items), error=str(e)
            )
            return 0, 1

    def _update_insertion_stats(
        self, items: int, batches: int, duration: float, errors: int
    ):
        """Update insertion performance statistics."""
        self.insertion_stats["total_items"] += items
        self.insertion_stats["total_batches"] += batches
        self.insertion_stats["total_duration"] += duration
        self.insertion_stats["errors"] += errors

    def get_insertion_stats(self) -> Dict[str, Any]:
        """Get detailed insertion performance statistics."""
        total_duration = self.insertion_stats["total_duration"]
        total_items = self.insertion_stats["total_items"]

        return {
            "total_items_inserted": total_items,
            "total_batches_processed": self.insertion_stats["total_batches"],
            "total_duration_seconds": total_duration,
            "average_items_per_second": round(
                total_items / max(0.1, total_duration), 2
            ),
            "average_batch_duration_ms": round(
                (total_duration / max(1, self.insertion_stats["total_batches"])) * 1000,
                2,
            ),
            "error_count": self.insertion_stats["errors"],
            "configuration": {
                "batch_size": self.batch_size,
                "max_parallel_batches": self.max_parallel_batches,
            },
        }


class DatabaseIndexManager:
    """Manage database indexes for optimal chat import performance."""

    def __init__(self, pool: OptimizedDatabaseConnectionPool):
        """Initialize database index manager."""
        self.pool = pool

    async def create_performance_indexes(self) -> Dict[str, Any]:
        """Create all performance-critical indexes for chat import."""
        start_time = time.time()
        created_indexes = []
        failed_indexes = []

        # Core performance indexes
        indexes = [
            # Primary timestamp index for chronological queries
            {
                "name": "idx_context_items_timestamp_desc",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_timestamp_desc
                    ON context_items USING btree (timestamp DESC)
                """,
            },
            # Session-based chat queries (most common for chat import)
            {
                "name": "idx_context_items_session_timestamp",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_session_timestamp
                    ON context_items USING btree (session_id, timestamp DESC)
                    WHERE source_type = 'chat'
                """,
            },
            # Content hash for deduplication (critical for performance)
            {
                "name": "idx_context_items_content_hash_unique",
                "query": """
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_content_hash_unique
                    ON context_items USING btree (content_hash)
                    WHERE content_hash IS NOT NULL
                """,
            },
            # Actor-based queries for user activity analysis
            {
                "name": "idx_context_items_actor_timestamp",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_actor_timestamp
                    ON context_items USING btree (actor_id, timestamp DESC)
                    WHERE source_type = 'chat' AND actor_id IS NOT NULL
                """,
            },
            # Embedding search optimization (requires pgvector)
            {
                "name": "idx_context_items_embedding_cosine",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_embedding_cosine
                    ON context_items USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 1000)
                    WHERE embedding IS NOT NULL
                """,
            },
            # Entity extraction metadata for enhanced searches
            {
                "name": "idx_context_items_entities_gin",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_entities_gin
                    ON context_items USING gin ((metrics->'extracted_entities'))
                    WHERE metrics ? 'extracted_entities'
                """,
            },
            # Source type filtering for multi-adapter performance
            {
                "name": "idx_context_items_source_type_timestamp",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_source_type_timestamp
                    ON context_items USING btree (source_type, timestamp DESC)
                """,
            },
            # Relationship table optimization
            {
                "name": "idx_context_relationships_source_target",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_source_target
                    ON context_relationships USING btree (source_id, target_id, relationship_type)
                """,
            },
            # High-confidence relationships for quality filtering
            {
                "name": "idx_context_relationships_high_confidence",
                "query": """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_high_confidence
                    ON context_relationships USING btree (confidence DESC, created_at DESC)
                    WHERE confidence > 0.7
                """,
            },
        ]

        # Create indexes with error handling
        for index in indexes:
            try:
                await self.pool.execute_query(index["query"], use_cache=False)
                created_indexes.append(index["name"])
                logger.info("Created index", name=index["name"])
            except Exception as e:
                failed_indexes.append({"name": index["name"], "error": str(e)})
                logger.warning(
                    "Failed to create index", name=index["name"], error=str(e)
                )

        duration = time.time() - start_time

        return {
            "created_indexes": created_indexes,
            "failed_indexes": failed_indexes,
            "total_duration_seconds": duration,
            "success_rate": len(created_indexes) / len(indexes) * 100,
        }

    async def analyze_table_statistics(self) -> Dict[str, Any]:
        """Update table statistics for optimal query planning."""
        try:
            # Update statistics for query planner
            await self.pool.execute_query(
                "ANALYZE context_items, context_relationships", use_cache=False
            )

            # Set higher statistics targets for key columns
            stat_updates = [
                "ALTER TABLE context_items ALTER COLUMN source_type SET STATISTICS 1000",
                "ALTER TABLE context_items ALTER COLUMN timestamp SET STATISTICS 1000",
                "ALTER TABLE context_items ALTER COLUMN session_id SET STATISTICS 1000",
                "ALTER TABLE context_items ALTER COLUMN actor_id SET STATISTICS 1000",
                "ALTER TABLE context_relationships ALTER COLUMN relationship_type SET STATISTICS 1000",
            ]

            for update in stat_updates:
                await self.pool.execute_query(update, use_cache=False)

            return {
                "status": "completed",
                "tables_analyzed": ["context_items", "context_relationships"],
                "statistics_updated": len(stat_updates),
            }

        except Exception as e:
            logger.error("Failed to analyze table statistics", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
            }

    async def get_index_usage_stats(self) -> Dict[str, Any]:
        """Get index usage statistics for performance monitoring."""
        query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) as index_size
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
              AND tablename IN ('context_items', 'context_relationships')
            ORDER BY idx_scan DESC
        """

        try:
            stats = await self.pool.execute_query(query, use_cache=True, cache_ttl=300)
            return {
                "index_stats": stats,
                "total_indexes": len(stats),
                "most_used": stats[0] if stats else None,
            }
        except Exception as e:
            logger.error("Failed to get index usage stats", error=str(e))
            return {"error": str(e)}


# Factory function for creating optimized database components
async def create_optimized_database(
    database_url: str,
    cache_manager: Optional[PerformanceCacheManager] = None,
    **pool_kwargs,
) -> Tuple[OptimizedDatabaseConnectionPool, BatchInsertOptimizer, DatabaseIndexManager]:
    """Create all optimized database components."""

    # Create optimized connection pool
    pool = OptimizedDatabaseConnectionPool(
        database_url=database_url, cache_manager=cache_manager, **pool_kwargs
    )
    await pool.initialize()

    # Create batch insert optimizer
    batch_optimizer = BatchInsertOptimizer(pool)

    # Create index manager
    index_manager = DatabaseIndexManager(pool)

    logger.info("Optimized database components created")
    return pool, batch_optimizer, index_manager
