"""
PostgreSQL Provider for OPSVI Data Services

Comprehensive PostgreSQL integration for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official psycopg2 and asyncpg documentation:
- https://www.psycopg.org/docs/
- https://magicstack.github.io/asyncpg/current/

Implements all core features:
- Connection pooling
- Query execution
- Transaction management
- Error handling
- Async support

Version: Referenced as of July 2024
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import psycopg2
    from psycopg2 import Error as PostgresError
    from psycopg2 import pool
except ImportError:
    raise ImportError("psycopg2 is required. Install with `pip install psycopg2`.")

try:
    import asyncpg
except ImportError:
    asyncpg = None  # Async support is optional

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class PostgreSQLError(ComponentError):
    """Custom exception for PostgreSQL operations."""

    pass


class PostgreSQLConfig:
    """Configuration for PostgreSQL provider."""

    def __init__(
        self,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        port: int = 5432,
        pool_size: int = 5,
        **kwargs: Any,
    ):
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "password")
        self.database = database or os.getenv("POSTGRES_DB", "postgres")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.pool_size = pool_size

        # Additional configuration
        for key, value in kwargs.items():
            setattr(self, key, value)


class PostgreSQLProvider(BaseComponent):
    """
    Comprehensive PostgreSQL provider for OPSVI ecosystem.

    Provides full database capabilities:
    - Connection pooling
    - Query execution
    - Transaction management
    - Error handling
    - Async support (when asyncpg is available)
    """

    def __init__(self, config: PostgreSQLConfig, **kwargs: Any) -> None:
        """Initialize PostgreSQL provider.

        Args:
            config: PostgreSQL configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__("postgresql", config.__dict__)
        self.config = config
        self.pool = None
        self.async_pool = None

        logger.debug(f"PostgreSQLProvider initialized with host: {config.host}")

    async def _initialize_impl(self) -> None:
        """Initialize PostgreSQL connection pool."""
        try:
            # Initialize sync pool
            self.pool = pool.SimpleConnectionPool(
                1,
                self.config.pool_size,
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port,
            )

            # Initialize async pool if available
            if asyncpg:
                self.async_pool = await asyncpg.create_pool(
                    host=self.config.host,
                    user=self.config.user,
                    password=self.config.password,
                    database=self.config.database,
                    port=self.config.port,
                    min_size=1,
                    max_size=self.config.pool_size,
                )

            logger.info(
                f"PostgreSQL connected: {self.config.host}:{self.config.port}/{self.config.database}"
            )

        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise PostgreSQLError(f"Failed to initialize PostgreSQL: {e}")

    async def _shutdown_impl(self) -> None:
        """Shutdown PostgreSQL connection pools."""
        try:
            if self.pool:
                self.pool.closeall()
                self.pool = None

            if self.async_pool:
                await self.async_pool.close()
                self.async_pool = None

            logger.info("PostgreSQL connections closed")
        except Exception as e:
            logger.error(f"PostgreSQL shutdown error: {e}")

    async def _health_check_impl(self) -> bool:
        """Check PostgreSQL health."""
        try:
            if not self.pool:
                return False
            result = self.execute_query("SELECT 1")
            return len(result) > 0 and result[0].get("?column?") == 1
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self._initialize_impl()

    def get_connection(self):
        """Get a connection from the pool."""
        if not self.pool:
            raise PostgreSQLError("Connection pool not initialized")
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool:
            self.pool.putconn(conn)

    # ==================== SYNC OPERATIONS ====================

    def execute_query(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                results = []

            cursor.close()
            return results

        except PostgresError as e:
            logger.error(f"PostgreSQL query failed: {e}")
            raise PostgreSQLError(f"Query execution failed: {e}")
        finally:
            self.return_connection(conn)

    def execute_update(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected

        except PostgresError as e:
            logger.error(f"PostgreSQL update failed: {e}")
            conn.rollback()
            raise PostgreSQLError(f"Update execution failed: {e}")
        finally:
            self.return_connection(conn)

    def execute_many(self, query: str, param_list: List[Union[Tuple, Dict]]) -> int:
        """Execute a query with multiple parameter sets."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected

        except PostgresError as e:
            logger.error(f"PostgreSQL batch execution failed: {e}")
            conn.rollback()
            raise PostgreSQLError(f"Batch execution failed: {e}")
        finally:
            self.return_connection(conn)

    def transaction(self):
        """Context manager for transactions."""

        class TransactionContext:
            def __init__(self, pool):
                self.pool = pool
                self.conn = None

            def __enter__(self):
                self.conn = self.pool.getconn()
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    self.conn.rollback()
                else:
                    self.conn.commit()
                self.pool.putconn(self.conn)

        return TransactionContext(self.pool)

    # ==================== ASYNC OPERATIONS ====================

    async def aexecute_query(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Async: Execute a SELECT query and return results."""
        if not self.async_pool:
            raise PostgreSQLError(
                "Async pool not available. Install asyncpg for async support."
            )

        try:
            async with self.async_pool.acquire() as conn:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Async PostgreSQL query failed: {e}")
            raise PostgreSQLError(f"Async query execution failed: {e}")

    async def aexecute_update(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> int:
        """Async: Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        if not self.async_pool:
            raise PostgreSQLError(
                "Async pool not available. Install asyncpg for async support."
            )

        try:
            async with self.async_pool.acquire() as conn:
                if params:
                    result = await conn.execute(query, *params)
                else:
                    result = await conn.execute(query)

                # Extract affected rows count from result
                if "UPDATE" in result:
                    return int(result.split()[-1])
                elif "INSERT" in result:
                    return int(result.split()[-1])
                elif "DELETE" in result:
                    return int(result.split()[-1])
                else:
                    return 0

        except Exception as e:
            logger.error(f"Async PostgreSQL update failed: {e}")
            raise PostgreSQLError(f"Async update execution failed: {e}")

    # ==================== UTILITY OPERATIONS ====================

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            """
            result = self.execute_query(query, (table_name,))
            return result[0]["exists"] if result else False
        except Exception as e:
            logger.error(f"Table existence check failed: {e}")
            return False

    def create_table(self, table_name: str, columns: List[str]) -> bool:
        """Create a table with specified columns."""
        try:
            columns_sql = ", ".join(columns)
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql});"
            self.execute_update(query)
            return True
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            return False

    def drop_table(self, table_name: str) -> bool:
        """Drop a table."""
        try:
            query = f"DROP TABLE IF EXISTS {table_name};"
            self.execute_update(query)
            return True
        except Exception as e:
            logger.error(f"Table drop failed: {e}")
            return False

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        try:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            result = self.execute_query(query)
            return [row["table_name"] for row in result]
        except Exception as e:
            logger.error(f"Table listing failed: {e}")
            return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a table."""
        try:
            query = """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """
            result = self.execute_query(query, (table_name,))
            return {
                "table_name": table_name,
                "columns": result,
                "column_count": len(result),
            }
        except Exception as e:
            logger.error(f"Table info retrieval failed: {e}")
            return {"table_name": table_name, "columns": [], "column_count": 0}

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        try:
            # Test basic operations
            tables = self.list_tables()
            version_result = self.execute_query("SELECT version();")
            version = version_result[0]["version"] if version_result else "unknown"

            return {
                "success": True,
                "status": "healthy",
                "tables_count": len(tables),
                "version": version,
                "database": self.config.database,
                "host": self.config.host,
                "port": self.config.port,
                "async_available": asyncpg is not None,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
            }
