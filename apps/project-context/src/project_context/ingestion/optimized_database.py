"""Optimized database interface for high-performance chat import."""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import asyncpg
import structlog

from ..models.common import BatchProcessingResult, ContextItem, ContextRelationship

logger = structlog.get_logger(__name__)


class ProductionDatabaseConfig:
    """Optimized database configuration for production-scale imports."""

    def __init__(
        self,
        # High-throughput connection pooling
        min_connections: int = 10,  # Increased from 5
        max_connections: int = 50,  # Increased from 20
        command_timeout: int = 120,  # Increased from 60
        statement_cache_size: int = 1024,  # Enable statement caching
        max_inactive_time: int = 300,  # Connection lifecycle management
        # Performance tuning
        enable_prepared_statements: bool = True,
        connection_validation_interval: int = 30,
        pool_recycle_time: int = 3600,  # 1 hour
        # Batch optimization
        optimal_batch_sizes: Dict[str, int] = None,
        adaptive_batching: bool = True,
        # Monitoring
        enable_connection_metrics: bool = True,
        slow_query_threshold: float = 5.0,  # 5 seconds
    ):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        self.statement_cache_size = statement_cache_size
        self.max_inactive_time = max_inactive_time

        self.enable_prepared_statements = enable_prepared_statements
        self.connection_validation_interval = connection_validation_interval
        self.pool_recycle_time = pool_recycle_time

        self.optimal_batch_sizes = optimal_batch_sizes or {
            "simple_messages": 2000,
            "entity_rich": 500,
            "embedding_heavy": 100,
            "relationship_complex": 200,
        }
        self.adaptive_batching = adaptive_batching

        self.enable_connection_metrics = enable_connection_metrics
        self.slow_query_threshold = slow_query_threshold


class ConnectionMetrics:
    """Track database connection performance metrics."""

    def __init__(self):
        self.total_queries = 0
        self.total_query_time = 0.0
        self.slow_queries = 0
        self.connection_errors = 0
        self.pool_utilization_samples = []
        self.last_metric_time = time.time()

    def record_query(self, duration: float, is_slow: bool = False):
        """Record query execution metrics."""
        self.total_queries += 1
        self.total_query_time += duration
        if is_slow:
            self.slow_queries += 1

    def record_pool_utilization(self, active: int, total: int):
        """Record connection pool utilization."""
        if total > 0:
            utilization = active / total
            self.pool_utilization_samples.append(utilization)
            # Keep only recent samples (last 100)
            if len(self.pool_utilization_samples) > 100:
                self.pool_utilization_samples = self.pool_utilization_samples[-100:]

    def get_average_query_time(self) -> float:
        """Get average query execution time."""
        return (
            self.total_query_time / self.total_queries
            if self.total_queries > 0
            else 0.0
        )

    def get_average_utilization(self) -> float:
        """Get average pool utilization."""
        return (
            sum(self.pool_utilization_samples) / len(self.pool_utilization_samples)
            if self.pool_utilization_samples
            else 0.0
        )


class OptimizedDatabaseConnectionPool:
    """High-performance database connection pool for production imports."""

    def __init__(
        self,
        database_url: str,
        config: ProductionDatabaseConfig,
    ):
        self.database_url = database_url
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None
        self.metrics = ConnectionMetrics()
        self.logger = logger.bind(component="optimized_database_pool")

        # Prepared statement cache
        self._prepared_statements: Dict[str, str] = {}

    async def initialize(self) -> None:
        """Initialize the optimized connection pool."""
        try:
            # Enhanced pool configuration for high performance
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                max_inactive_connection_lifetime=self.config.max_inactive_time,
                server_settings={
                    "jit": "off",  # Disable JIT for predictable performance
                    "application_name": "unified_context_optimized_import",
                    "shared_preload_libraries": "pg_stat_statements",
                    "log_statement": "none",  # Reduce logging overhead
                    "log_min_duration_statement": str(
                        int(self.config.slow_query_threshold * 1000)
                    ),
                    # Performance optimizations
                    "work_mem": "256MB",
                    "maintenance_work_mem": "1GB",
                    "effective_cache_size": "8GB",
                    "random_page_cost": "1.1",
                    "checkpoint_completion_target": "0.7",
                    "wal_buffers": "16MB",
                },
            )

            # Prepare common statements
            if self.config.enable_prepared_statements:
                await self._prepare_common_statements()

            self.logger.info(
                "Optimized database connection pool initialized",
                min_connections=self.config.min_connections,
                max_connections=self.config.max_connections,
                prepared_statements=len(self._prepared_statements),
            )

        except Exception as e:
            self.logger.error(
                "Failed to initialize optimized database pool", error=str(e)
            )
            raise

    async def _prepare_common_statements(self) -> None:
        """Prepare frequently used SQL statements for better performance."""
        common_statements = {
            "insert_context_item": """
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
            """,
            "insert_relationship": """
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
            """,
            "get_recent_items": """
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
            """,
        }

        async with self._pool.acquire() as conn:
            for name, sql in common_statements.items():
                try:
                    await conn.prepare(sql)
                    self._prepared_statements[name] = sql
                    self.logger.debug("Prepared statement ready", statement=name)
                except Exception as e:
                    self.logger.warning(
                        "Failed to prepare statement", statement=name, error=str(e)
                    )

    async def close(self) -> None:
        """Close the connection pool with cleanup."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self.logger.info(
                "Optimized database connection pool closed",
                total_queries=self.metrics.total_queries,
                avg_query_time=self.metrics.get_average_query_time(),
                slow_queries=self.metrics.slow_queries,
            )

    @asynccontextmanager
    async def acquire(self):
        """Acquire a database connection with metrics tracking."""
        if not self._pool:
            raise Exception("Database pool not initialized")

        start_time = time.time()
        try:
            async with self._pool.acquire() as connection:
                # Track pool utilization
                pool_size = self._pool.get_size()
                idle_size = self._pool.get_idle_size()
                active_connections = pool_size - idle_size

                if self.config.enable_connection_metrics:
                    self.metrics.record_pool_utilization(active_connections, pool_size)

                yield connection

        except Exception as e:
            self.metrics.connection_errors += 1
            self.logger.error("Database connection error", error=str(e))
            raise
        finally:
            duration = time.time() - start_time
            is_slow = duration > self.config.slow_query_threshold
            self.metrics.record_query(duration, is_slow)

    @asynccontextmanager
    async def transaction(self):
        """Acquire a database connection and start a transaction with retry logic."""
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                async with self.acquire() as connection:
                    async with connection.transaction():
                        yield connection
                return
            except (asyncpg.PostgresError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    self.logger.warning(
                        "Transaction failed, retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=retry_delay,
                        error=str(e),
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise

    async def execute_optimized_query(
        self,
        query: str,
        *args,
        fetch: str = "none",
        statement_name: Optional[str] = None,
    ) -> Any:
        """Execute query with performance optimization and metrics."""
        start_time = time.time()

        try:
            async with self.acquire() as connection:
                # Use prepared statement if available
                if statement_name and statement_name in self._prepared_statements:
                    prepared_stmt = await connection.prepare(
                        self._prepared_statements[statement_name]
                    )

                    if fetch == "none":
                        return await prepared_stmt.execute(*args)
                    elif fetch == "one":
                        return await prepared_stmt.fetchrow(*args)
                    elif fetch == "all":
                        return await prepared_stmt.fetch(*args)
                    elif fetch == "val":
                        return await prepared_stmt.fetchval(*args)
                else:
                    # Fallback to regular execution
                    if fetch == "none":
                        return await connection.execute(query, *args)
                    elif fetch == "one":
                        return await connection.fetchrow(query, *args)
                    elif fetch == "all":
                        return await connection.fetch(query, *args)
                    elif fetch == "val":
                        return await connection.fetchval(query, *args)

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                "Query execution failed",
                duration=duration,
                statement=statement_name,
                error=str(e),
            )
            raise
        finally:
            duration = time.time() - start_time
            is_slow = duration > self.config.slow_query_threshold
            if is_slow:
                self.logger.warning(
                    "Slow query detected",
                    duration=duration,
                    threshold=self.config.slow_query_threshold,
                    statement=statement_name or query[:100],
                )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive database performance metrics."""
        pool_stats = {}
        if self._pool:
            pool_stats = {
                "pool_size": self._pool.get_size(),
                "idle_connections": self._pool.get_idle_size(),
                "active_connections": self._pool.get_size()
                - self._pool.get_idle_size(),
                "utilization_pct": (
                    1.0 - self._pool.get_idle_size() / self._pool.get_size()
                )
                * 100
                if self._pool.get_size() > 0
                else 0,
            }

        return {
            "connection_pool": pool_stats,
            "query_metrics": {
                "total_queries": self.metrics.total_queries,
                "average_query_time_ms": self.metrics.get_average_query_time() * 1000,
                "slow_queries": self.metrics.slow_queries,
                "slow_query_rate_pct": (
                    self.metrics.slow_queries / self.metrics.total_queries * 100
                )
                if self.metrics.total_queries > 0
                else 0,
                "connection_errors": self.metrics.connection_errors,
            },
            "pool_utilization": {
                "average_utilization_pct": self.metrics.get_average_utilization() * 100,
                "samples_collected": len(self.metrics.pool_utilization_samples),
            },
            "prepared_statements": len(self._prepared_statements),
        }


class AdaptiveBatchSizer:
    """Dynamically optimize batch sizes based on system performance."""

    def __init__(self, config: ProductionDatabaseConfig):
        self.config = config
        self.performance_history: Dict[
            str, List[Tuple[int, float]]
        ] = {}  # batch_size -> duration samples
        self.optimal_sizes: Dict[str, int] = config.optimal_batch_sizes.copy()
        self.learning_enabled = config.adaptive_batching

    def get_optimal_batch_size(
        self, data_type: str, current_throughput: float, available_memory_mb: int
    ) -> int:
        """Calculate optimal batch size based on current conditions."""
        base_size = self.optimal_sizes.get(data_type, 500)

        if not self.learning_enabled:
            return base_size

        # Adjust based on memory constraints
        memory_factor = min(1.0, available_memory_mb / 2048)  # 2GB baseline
        memory_adjusted_size = int(base_size * memory_factor)

        # Adjust based on throughput performance
        if (
            data_type in self.performance_history
            and self.performance_history[data_type]
        ):
            # Find the batch size with best performance
            history = self.performance_history[data_type]
            best_performance = min(history, key=lambda x: x[1])  # x[1] is duration
            best_batch_size = best_performance[0]

            # Gradually move toward optimal size
            adjustment_factor = 0.8  # Conservative adjustment
            throughput_adjusted_size = int(
                base_size * adjustment_factor
                + best_batch_size * (1 - adjustment_factor)
            )
        else:
            throughput_adjusted_size = base_size

        # Return the minimum to ensure we don't exceed constraints
        optimal_size = min(
            memory_adjusted_size, throughput_adjusted_size, base_size * 2
        )  # Cap at 2x base
        optimal_size = max(optimal_size, base_size // 4)  # Floor at 25% of base

        return optimal_size

    def record_batch_performance(
        self, data_type: str, batch_size: int, duration: float
    ):
        """Record batch performance for learning."""
        if not self.learning_enabled:
            return

        if data_type not in self.performance_history:
            self.performance_history[data_type] = []

        # Add performance sample
        self.performance_history[data_type].append((batch_size, duration))

        # Keep only recent samples (last 50)
        if len(self.performance_history[data_type]) > 50:
            self.performance_history[data_type] = self.performance_history[data_type][
                -50:
            ]

        # Update optimal size if we have enough samples
        if len(self.performance_history[data_type]) >= 10:
            self._update_optimal_size(data_type)

    def _update_optimal_size(self, data_type: str):
        """Update optimal batch size based on performance history."""
        history = self.performance_history[data_type]

        # Find the batch size with consistently good performance
        size_performance: Dict[int, List[float]] = {}
        for batch_size, duration in history:
            if batch_size not in size_performance:
                size_performance[batch_size] = []
            size_performance[batch_size].append(duration)

        # Calculate average performance for each batch size
        avg_performance = {}
        for size, durations in size_performance.items():
            if len(durations) >= 3:  # Need at least 3 samples
                avg_performance[size] = sum(durations) / len(durations)

        if avg_performance:
            # Find the best performing size
            best_size = min(avg_performance, key=avg_performance.get)

            # Update optimal size conservatively
            current_optimal = self.optimal_sizes[data_type]
            new_optimal = int(current_optimal * 0.9 + best_size * 0.1)  # 10% adjustment

            self.optimal_sizes[data_type] = new_optimal
            logger.debug(
                "Updated optimal batch size",
                data_type=data_type,
                old_size=current_optimal,
                new_size=new_optimal,
                best_observed=best_size,
            )


class HighPerformanceIngestionDatabase:
    """Enhanced database operations optimized for production-scale imports."""

    def __init__(self, pool: OptimizedDatabaseConnectionPool):
        self.pool = pool
        self.batch_sizer = AdaptiveBatchSizer(pool.config)
        self.logger = logger.bind(component="high_performance_ingestion_db")

    async def store_context_items_optimized(
        self,
        items: List[ContextItem],
        data_type: str = "simple_messages",
        available_memory_mb: int = 2048,
    ) -> BatchProcessingResult:
        """Store context items with adaptive batch sizing and performance optimization."""
        start_time = datetime.utcnow()
        result = BatchProcessingResult(total_items=len(items))

        if not items:
            return result

        try:
            # Calculate optimal batch size
            current_throughput = len(items)  # Simplistic throughput measure
            optimal_batch_size = self.batch_sizer.get_optimal_batch_size(
                data_type, current_throughput, available_memory_mb
            )

            self.logger.info(
                "Starting optimized batch storage",
                total_items=len(items),
                optimal_batch_size=optimal_batch_size,
                data_type=data_type,
            )

            # Process in optimized batches
            for i in range(0, len(items), optimal_batch_size):
                batch = items[i : i + optimal_batch_size]
                batch_start_time = time.time()

                try:
                    async with self.pool.transaction() as conn:
                        batch_result = await self._store_batch_optimized(conn, batch)

                        result.processed_items += batch_result["processed"]
                        result.failed_items += batch_result["failed"]
                        result.duplicate_items += batch_result["duplicates"]
                        result.errors.extend(batch_result["errors"])

                    # Record performance for adaptive learning
                    batch_duration = time.time() - batch_start_time
                    self.batch_sizer.record_batch_performance(
                        data_type, len(batch), batch_duration
                    )

                except Exception as e:
                    self.logger.error(
                        "Optimized batch storage failed",
                        batch_start=i,
                        batch_size=len(batch),
                        optimal_size=optimal_batch_size,
                        error=str(e),
                    )
                    result.failed_items += len(batch)
                    result.errors.append(
                        {"batch_start": i, "batch_size": len(batch), "error": str(e)}
                    )

            # Calculate final metrics
            end_time = datetime.utcnow()
            result.processing_time_seconds = (end_time - start_time).total_seconds()

            # Calculate throughput
            if result.processing_time_seconds > 0:
                throughput = result.processed_items / result.processing_time_seconds
            else:
                throughput = 0

            self.logger.info(
                "Optimized context items storage completed",
                total_items=result.total_items,
                processed_items=result.processed_items,
                failed_items=result.failed_items,
                processing_time=result.processing_time_seconds,
                throughput_items_per_sec=throughput,
                optimal_batch_size=optimal_batch_size,
            )

            return result

        except Exception as e:
            self.logger.error("Optimized storage operation failed", error=str(e))
            result.failed_items = len(items)
            result.errors.append({"error": str(e)})
            return result

    async def _store_batch_optimized(
        self, conn: asyncpg.Connection, items: List[ContextItem]
    ) -> Dict[str, Any]:
        """Store a batch using optimized prepared statements and bulk operations."""
        processed = 0
        failed = 0
        duplicates = 0
        errors = []

        # Use prepared statement for better performance
        try:
            # Bulk insert using COPY for maximum performance on large batches
            if len(items) > 100:  # Use COPY for large batches
                return await self._store_batch_copy_optimized(conn, items)
            else:
                # Use prepared statements for smaller batches
                return await self._store_batch_prepared_statement(conn, items)

        except Exception as e:
            # Fallback to individual inserts if bulk operations fail
            self.logger.warning(
                "Bulk storage failed, falling back to individual inserts",
                batch_size=len(items),
                error=str(e),
            )
            return await self._store_batch_individual(conn, items)

    async def _store_batch_copy_optimized(
        self, conn: asyncpg.Connection, items: List[ContextItem]
    ) -> Dict[str, Any]:
        """Use PostgreSQL COPY for maximum throughput on large batches."""
        # Prepare data for COPY
        copy_data = []
        for item in items:
            row = [
                str(item.id),
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
            copy_data.append(row)

        # Create temporary table for COPY operation
        temp_table = f"temp_context_items_{int(time.time() * 1000000)}"

        try:
            # Create temporary table with same structure
            await conn.execute(
                f"""
                CREATE TEMP TABLE {temp_table} (LIKE context_items INCLUDING DEFAULTS)
            """
            )

            # COPY data to temporary table
            await conn.copy_records_to_table(temp_table, records=copy_data)

            # Merge from temporary table with conflict handling
            merge_result = await conn.fetch(
                f"""
                INSERT INTO context_items
                SELECT * FROM {temp_table}
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
            )

            processed = sum(1 for row in merge_result if row["inserted"])
            duplicates = len(merge_result) - processed

            return {
                "processed": processed,
                "failed": 0,
                "duplicates": duplicates,
                "errors": [],
            }

        except Exception as e:
            self.logger.error("COPY-based batch storage failed", error=str(e))
            return {
                "processed": 0,
                "failed": len(items),
                "duplicates": 0,
                "errors": [{"error": f"COPY operation failed: {str(e)}"}],
            }
        finally:
            # Clean up temporary table
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {temp_table}")
            except:
                pass

    async def _store_batch_prepared_statement(
        self, conn: asyncpg.Connection, items: List[ContextItem]
    ) -> Dict[str, Any]:
        """Use prepared statement for medium-sized batches."""
        processed = 0
        failed = 0
        duplicates = 0
        errors = []

        # Prepare the insert statement if not already prepared
        insert_query = self.pool._prepared_statements.get(
            "insert_context_item",
            """
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
        """,
        )

        prepared_stmt = await conn.prepare(insert_query)

        # Execute prepared statement for each item
        for item in items:
            try:
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

                row = await prepared_stmt.fetchrow(*params)

                if row["inserted"]:
                    processed += 1
                else:
                    duplicates += 1

            except Exception as e:
                failed += 1
                errors.append({"item_source_id": item.source_id, "error": str(e)})

        return {
            "processed": processed,
            "failed": failed,
            "duplicates": duplicates,
            "errors": errors,
        }

    async def _store_batch_individual(
        self, conn: asyncpg.Connection, items: List[ContextItem]
    ) -> Dict[str, Any]:
        """Fallback to individual inserts with error handling."""
        processed = 0
        failed = 0
        duplicates = 0
        errors = []

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

                row = await conn.fetchrow(insert_query, *params)

                if row["inserted"]:
                    processed += 1
                else:
                    duplicates += 1

            except Exception as e:
                failed += 1
                errors.append({"item_source_id": item.source_id, "error": str(e)})

        return {
            "processed": processed,
            "failed": failed,
            "duplicates": duplicates,
            "errors": errors,
        }

    async def get_comprehensive_health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check with performance metrics."""
        try:
            start_time = datetime.utcnow()

            # Basic connectivity test
            result = await self.pool.execute_optimized_query("SELECT 1", fetch="val")

            # Table access and count test
            count = await self.pool.execute_optimized_query(
                "SELECT COUNT(*) FROM context_items", fetch="val"
            )

            # Performance metrics
            perf_metrics = await self.pool.get_performance_metrics()

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "total_items": count,
                "performance_metrics": perf_metrics,
                "adaptive_batching": {
                    "enabled": self.batch_sizer.learning_enabled,
                    "optimal_sizes": self.batch_sizer.optimal_sizes,
                    "performance_samples": {
                        data_type: len(samples)
                        for data_type, samples in self.batch_sizer.performance_history.items()
                    },
                },
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "performance_metrics": await self.pool.get_performance_metrics()
                if self.pool
                else {},
            }
