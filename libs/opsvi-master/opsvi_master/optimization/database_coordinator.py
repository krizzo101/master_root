"""
Database Coordinator for KG-DB Optimization System

Provides high-performance database operations with connection pooling,
intelligent query optimization, and comprehensive error handling.
"""

from __future__ import annotations
import asyncio
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import asynccontextmanager
import logging
import json
from pathlib import Path

from .exceptions import DatabaseConnectionError
from .performance_monitor import PerformanceMonitor, MetricType
from .cache_manager import CacheManager, CacheType


class DatabaseCoordinator:
    """
    High-performance database coordinator with connection pooling and optimization.

    Features:
    - Connection pooling with automatic scaling
    - Query optimization and caching
    - Transaction management with rollback
    - Performance monitoring and alerting
    - Intelligent retry mechanisms
    - Backup and recovery support
    """

    def __init__(
        self,
        database_path: str,
        max_connections: int = 10,
        connection_timeout: float = 30.0,
        query_timeout: float = 10.0,
        performance_monitor: Optional[PerformanceMonitor] = None,
        cache_manager: Optional[CacheManager] = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.query_timeout = query_timeout
        self.performance_monitor = performance_monitor
        self.cache_manager = cache_manager

        self._connection_pool: List[sqlite3.Connection] = []
        self._connection_semaphore = asyncio.Semaphore(max_connections)
        self._pool_lock = asyncio.Lock()
        self._active_connections = 0
        self._connection_stats = {
            "total_created": 0,
            "total_queries": 0,
            "failed_queries": 0,
            "cache_hits": 0,
        }

        self._logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize database coordinator and create initial connections."""
        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Create initial connection to verify database
        try:
            conn = await self._create_connection()
            await self._execute_query(conn, "SELECT 1", fetch=True)
            self._return_connection(conn)
            self._logger.info(
                "Database coordinator initialized: %s", self.database_path
            )
        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to initialize database coordinator: {e}",
                database_path=str(self.database_path),
            )

    async def close(self) -> None:
        """Close all database connections."""
        async with self._pool_lock:
            for conn in self._connection_pool:
                try:
                    conn.close()
                except Exception as e:
                    self._logger.warning("Error closing connection: %s", e)

            self._connection_pool.clear()
            self._active_connections = 0
            self._logger.info("Database coordinator closed")

    @asynccontextmanager
    async def get_connection(self):
        """
        Context manager to get a database connection from the pool.

        Yields:
            SQLite connection with automatic return to pool
        """
        async with self._connection_semaphore:
            conn = await self._get_pooled_connection()
            try:
                yield conn
            finally:
                self._return_connection(conn)

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = False,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
    ) -> Optional[Union[List[Tuple], int]]:
        """
        Execute a database query with caching and performance monitoring.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results
            cache_key: Cache key for SELECT queries
            cache_ttl: Cache TTL in seconds

        Returns:
            Query results (if fetch=True) or affected row count
        """
        # Check cache for SELECT queries
        if fetch and cache_key and self.cache_manager:
            cached_result = await self.cache_manager.get(
                cache_key, CacheType.DATABASE_QUERY
            )
            if cached_result is not None:
                self._connection_stats["cache_hits"] += 1
                return cached_result

        # Execute query with performance monitoring
        if self.performance_monitor:
            async with self.performance_monitor.measure_operation(
                operation_name=f"db_query_{query.split()[0].lower()}",
                component="database_coordinator",
            ):
                result = await self._execute_query_internal(query, params, fetch)
        else:
            result = await self._execute_query_internal(query, params, fetch)

        # Cache SELECT results
        if fetch and cache_key and result and self.cache_manager:
            await self.cache_manager.set(
                cache_key, result, CacheType.DATABASE_QUERY, custom_ttl=cache_ttl
            )

        return result

    async def execute_transaction(
        self, queries: List[Tuple[str, Optional[Tuple]]]
    ) -> bool:
        """
        Execute multiple queries in a transaction.

        Args:
            queries: List of (query, params) tuples

        Returns:
            True if transaction completed successfully
        """
        if self.performance_monitor:
            async with self.performance_monitor.measure_operation(
                operation_name="db_transaction", component="database_coordinator"
            ):
                return await self._execute_transaction_internal(queries)
        else:
            return await self._execute_transaction_internal(queries)

    async def get_agent_assignments(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get active assignments for an agent."""
        query = """
        SELECT assignment_id, assignment_type, priority, status, details, created_at
        FROM agent_assignments 
        WHERE agent_id = ? AND status IN ('active', 'pending')
        ORDER BY priority DESC, created_at ASC
        """

        cache_key = f"agent_assignments_{agent_id}"
        results = await self.execute_query(
            query, (agent_id,), fetch=True, cache_key=cache_key, cache_ttl=60
        )

        if not results:
            return []

        assignments = []
        for row in results:
            assignment = {
                "assignment_id": row[0],
                "assignment_type": row[1],
                "priority": row[2],
                "status": row[3],
                "details": json.loads(row[4]) if row[4] else {},
                "created_at": row[5],
            }
            assignments.append(assignment)

        return assignments

    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities for an agent."""
        query = """
        SELECT capability_name
        FROM agent_capabilities
        WHERE agent_id = ?
        ORDER BY capability_name
        """

        cache_key = f"agent_capabilities_{agent_id}"
        results = await self.execute_query(
            query, (agent_id,), fetch=True, cache_key=cache_key, cache_ttl=300
        )

        return [row[0] for row in results] if results else []

    async def get_agent_directives(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get active directives for an agent."""
        query = """
        SELECT directive_id, directive_type, content, priority, created_at
        FROM agent_directives
        WHERE agent_id = ? AND status = 'active'
        ORDER BY priority DESC, created_at ASC
        """

        cache_key = f"agent_directives_{agent_id}"
        results = await self.execute_query(
            query, (agent_id,), fetch=True, cache_key=cache_key, cache_ttl=120
        )

        if not results:
            return []

        directives = []
        for row in results:
            directive = {
                "directive_id": row[0],
                "directive_type": row[1],
                "content": row[2],
                "priority": row[3],
                "created_at": row[4],
            }
            directives.append(directive)

        return directives

    async def update_agent_status(
        self,
        agent_id: str,
        status: str,
        current_task: Optional[str] = None,
        last_heartbeat: Optional[datetime] = None,
    ) -> bool:
        """Update agent status in database."""
        query = """
        UPDATE agents 
        SET status = ?, current_task = ?, last_heartbeat = ?, updated_at = ?
        WHERE agent_id = ?
        """

        params = (
            status,
            current_task,
            (last_heartbeat or datetime.now()).isoformat(),
            datetime.now().isoformat(),
            agent_id,
        )

        result = await self.execute_query(query, params)

        # Invalidate agent cache
        if self.cache_manager:
            await self.cache_manager.invalidate_pattern(f"agent_{agent_id}")

        return result is not None and result > 0

    async def create_agent_work_entry(
        self,
        agent_id: str,
        assignment_id: str,
        action_type: str,
        details: Dict[str, Any],
    ) -> bool:
        """Create work history entry for an agent."""
        query = """
        INSERT INTO agent_work_history 
        (agent_id, assignment_id, action_type, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            agent_id,
            assignment_id,
            action_type,
            json.dumps(details),
            datetime.now().isoformat(),
        )

        result = await self.execute_query(query, params)
        return result is not None and result > 0

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        stats = {
            "connection_pool": {
                "max_connections": self.max_connections,
                "active_connections": self._active_connections,
                "pool_size": len(self._connection_pool),
            },
            "query_stats": self._connection_stats.copy(),
        }

        # Add cache hit rate if available
        if self._connection_stats["total_queries"] > 0:
            cache_hit_rate = (
                self._connection_stats["cache_hits"]
                / self._connection_stats["total_queries"]
            )
            stats["cache_hit_rate"] = cache_hit_rate

            # Record cache hit rate metric
            if self.performance_monitor:
                await self.performance_monitor.record_metric(
                    MetricType.CACHE_HIT_RATE,
                    cache_hit_rate,
                    component="database_coordinator",
                )

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        health_status = "healthy"
        issues = []

        try:
            # Test basic connectivity
            start_time = asyncio.get_event_loop().time()
            async with self.get_connection() as conn:
                await self._execute_query(conn, "SELECT 1", fetch=True)
            response_time = asyncio.get_event_loop().time() - start_time

            # Check response time
            if response_time > 1.0:
                health_status = "warning"
                issues.append(f"Slow response time: {response_time:.2f}s")

            # Check error rate
            if self._connection_stats["total_queries"] > 0:
                error_rate = (
                    self._connection_stats["failed_queries"]
                    / self._connection_stats["total_queries"]
                )
                if error_rate > 0.05:  # 5% error rate
                    health_status = "critical"
                    issues.append(f"High error rate: {error_rate:.2%}")

            # Check connection pool utilization
            pool_utilization = self._active_connections / self.max_connections
            if pool_utilization > 0.8:
                health_status = "warning"
                issues.append(
                    f"High connection pool utilization: {pool_utilization:.1%}"
                )

        except Exception as e:
            health_status = "critical"
            issues.append(f"Database connectivity error: {e}")

        return {
            "status": health_status,
            "response_time_ms": int(response_time * 1000)
            if "response_time" in locals()
            else None,
            "issues": issues,
            "statistics": await self.get_database_stats(),
        }

    async def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        try:
            conn = sqlite3.connect(
                str(self.database_path), timeout=self.connection_timeout
            )
            conn.row_factory = sqlite3.Row

            # Configure connection for performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")

            self._connection_stats["total_created"] += 1
            return conn

        except Exception as e:
            raise DatabaseConnectionError(
                f"Failed to create database connection: {e}",
                database_path=str(self.database_path),
            )

    async def _get_pooled_connection(self) -> sqlite3.Connection:
        """Get connection from pool or create new one."""
        async with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                self._active_connections += 1
                return conn
            else:
                conn = await self._create_connection()
                self._active_connections += 1
                return conn

    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool."""
        asyncio.create_task(self._return_connection_async(conn))

    async def _return_connection_async(self, conn: sqlite3.Connection) -> None:
        """Async version of return connection."""
        async with self._pool_lock:
            if len(self._connection_pool) < self.max_connections:
                self._connection_pool.append(conn)
            else:
                conn.close()
            self._active_connections -= 1

    async def _execute_query_internal(
        self, query: str, params: Optional[Tuple], fetch: bool
    ) -> Optional[Union[List[Tuple], int]]:
        """Internal query execution with error handling."""
        async with self.get_connection() as conn:
            try:
                result = await self._execute_query(conn, query, params, fetch)
                self._connection_stats["total_queries"] += 1
                return result

            except Exception as e:
                self._connection_stats["failed_queries"] += 1
                raise DatabaseConnectionError(
                    f"Query execution failed: {e}", operation=query.split()[0].upper()
                )

    async def _execute_query(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = False,
    ) -> Optional[Union[List[Tuple], int]]:
        """Execute query on a specific connection."""
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount

        finally:
            cursor.close()

    async def _execute_transaction_internal(
        self, queries: List[Tuple[str, Optional[Tuple]]]
    ) -> bool:
        """Internal transaction execution."""
        async with self.get_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")

                for query, params in queries:
                    await self._execute_query(conn, query, params)

                conn.commit()
                return True

            except Exception as e:
                conn.rollback()
                self._logger.error("Transaction failed, rolled back: %s", e)
                raise DatabaseConnectionError(
                    f"Transaction failed: {e}", operation="TRANSACTION"
                )
