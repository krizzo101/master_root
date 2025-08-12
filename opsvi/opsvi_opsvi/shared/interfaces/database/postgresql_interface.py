"""
PostgreSQL Shared Interface
--------------------------
Authoritative implementation based on the official psycopg2 and asyncpg documentation:
- https://www.psycopg.org/docs/
- https://magicstack.github.io/asyncpg/current/
Implements all core features: connection pooling, query execution, transaction management, and error handling.
Version: Referenced as of July 2024
"""

import logging
from typing import Any

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

logger = logging.getLogger(__name__)


class PostgreSQLInterface:
    """
    Authoritative shared interface for PostgreSQL database operations.
    See: https://www.psycopg.org/docs/
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 5432,
        pool_size: int = 5,
    ):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
        }
        try:
            self.pool = pool.SimpleConnectionPool(1, pool_size, **self.config)
            logger.info("PostgreSQL connection pool initialized.")
        except PostgresError as e:
            logger.error(f"PostgreSQL pool initialization failed: {e}")
            raise

    def get_connection(self):
        return self.pool.getconn()

    def execute_query(
        self, query: str, params: tuple | dict | None = None
    ) -> list[dict[str, Any]]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            columns = [desc[0] for desc in cursor.description]
            results = [
                dict(zip(columns, row, strict=False)) for row in cursor.fetchall()
            ]
            cursor.close()
            return results
        except PostgresError as e:
            logger.error(f"PostgreSQL query failed: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def execute_update(self, query: str, params: tuple | dict | None = None) -> int:
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
            raise
        finally:
            self.pool.putconn(conn)

    def execute_many(self, query: str, param_list: list[tuple | dict]) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected
        except PostgresError as e:
            logger.error(f"PostgreSQL bulk operation failed: {e}")
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def transaction(self):
        class TransactionContext:
            def __init__(self, pool):
                self.conn = pool.getconn()

            def __enter__(self):
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.conn.rollback()
                else:
                    self.conn.commit()
                pool.putconn(self.conn)

        return TransactionContext(self.pool)

    # Async support using asyncpg
    async def aexecute_query(
        self, query: str, params: tuple | dict | None = None
    ) -> list[dict[str, Any]]:
        if not asyncpg:
            raise ImportError(
                "asyncpg is required for async support. Install with `pip install asyncpg`."
            )
        conn = await asyncpg.connect(**self.config)
        try:
            stmt = await conn.prepare(query)
            records = await stmt.fetch(*(params or ()))
            results = [dict(record) for record in records]
            return results
        finally:
            await conn.close()

    async def aexecute_update(
        self, query: str, params: tuple | dict | None = None
    ) -> int:
        if not asyncpg:
            raise ImportError(
                "asyncpg is required for async support. Install with `pip install asyncpg`."
            )
        conn = await asyncpg.connect(**self.config)
        try:
            result = await conn.execute(query, *(params or ()))
            # asyncpg returns a string like 'INSERT 0 1', so parse the affected row count
            affected = int(result.split()[-1])
            return affected
        finally:
            await conn.close()


# Example usage and advanced features are available in the official docs:
# https://www.psycopg.org/docs/
# https://magicstack.github.io/asyncpg/current/
