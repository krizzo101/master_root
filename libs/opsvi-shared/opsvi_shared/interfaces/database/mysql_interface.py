"""
MySQL Shared Interface
---------------------
Authoritative implementation based on the official mysql-connector-python and aiomysql documentation:
- https://dev.mysql.com/doc/connector-python/en/
- https://aiomysql.readthedocs.io/en/latest/
Implements all core features: connection pooling, query execution, transaction management, and error handling.
Version: Referenced as of July 2024
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    from mysql.connector import pooling
except ImportError:
    raise ImportError(
        "mysql-connector-python is required. Install with `pip install mysql-connector-python`."
    )

try:
    import aiomysql
except ImportError:
    aiomysql = None  # Async support is optional

logger = logging.getLogger(__name__)


class MySQLInterface:
    """
    Authoritative shared interface for MySQL database operations.
    See: https://dev.mysql.com/doc/connector-python/en/
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: int = 3306,
        pool_name: str = "mypool",
        pool_size: int = 5,
    ):
        """
        Initialize a MySQLInterface with connection pooling.
        Args:
            host: MySQL server host.
            user: Username.
            password: Password.
            database: Database name.
            port: MySQL port (default 3306).
            pool_name: Name for the connection pool.
            pool_size: Number of connections in the pool.
        """
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
        }
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name=pool_name, pool_size=pool_size, **self.config
            )
            logger.info("MySQL connection pool initialized.")
        except MySQLError as e:
            logger.error(f"MySQL pool initialization failed: {e}")
            raise

    def get_connection(self):
        """
        Get a connection from the pool.
        Returns:
            MySQLConnection instance.
        """
        return self.pool.get_connection()

    def execute_query(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as a list of dicts.
        Args:
            query: SQL query string.
            params: Optional query parameters (tuple or dict).
        Returns:
            List of result rows as dicts.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except MySQLError as e:
            logger.error(f"MySQL query failed: {e}")
            raise
        finally:
            conn.close()

    def execute_update(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        Args:
            query: SQL query string.
            params: Optional query parameters (tuple or dict).
        Returns:
            Number of affected rows.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected
        except MySQLError as e:
            logger.error(f"MySQL update failed: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_many(self, query: str, param_list: List[Union[Tuple, Dict]]) -> int:
        """
        Execute a query with multiple parameter sets (bulk insert/update).
        Args:
            query: SQL query string.
            param_list: List of parameter tuples or dicts.
        Returns:
            Total number of affected rows.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, param_list)
            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            return affected
        except MySQLError as e:
            logger.error(f"MySQL bulk operation failed: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def transaction(self):
        """
        Context manager for a transaction.
        Usage:
            with mysql.transaction() as conn:
                ...
        Yields:
            Connection object with manual commit/rollback.
        """

        class TransactionContext:
            def __init__(self, pool):
                self.conn = pool.get_connection()

            def __enter__(self):
                return self.conn

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.conn.rollback()
                else:
                    self.conn.commit()
                self.conn.close()

        return TransactionContext(self.pool)

    # Optional: Async support using aiomysql
    async def aexecute_query(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query asynchronously (requires aiomysql).
        Args:
            query: SQL query string.
            params: Optional query parameters.
        Returns:
            List of result rows as dicts.
        """
        if not aiomysql:
            raise ImportError(
                "aiomysql is required for async support. Install with `pip install aiomysql`."
            )
        pool = await aiomysql.create_pool(**self.config)
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params or ())
                results = await cursor.fetchall()
        pool.close()
        await pool.wait_closed()
        return results

    async def aexecute_update(
        self, query: str, params: Optional[Union[Tuple, Dict]] = None
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query asynchronously (requires aiomysql).
        Args:
            query: SQL query string.
            params: Optional query parameters.
        Returns:
            Number of affected rows.
        """
        if not aiomysql:
            raise ImportError(
                "aiomysql is required for async support. Install with `pip install aiomysql`."
            )
        pool = await aiomysql.create_pool(**self.config)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params or ())
                affected = cursor.rowcount
                await conn.commit()
        pool.close()
        await pool.wait_closed()
        return affected


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mysql = MySQLInterface(
        host="localhost",
        user="root",
        password="password",
        database="testdb",
    )
    # Create table
    mysql.execute_update(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            age INT
        )
    """
    )
    # Insert
    mysql.execute_update("INSERT INTO users (name, age) VALUES (%s, %s)", ("Alice", 30))
    # Query
    users = mysql.execute_query("SELECT * FROM users")
    print("Users:", users)
    # Transaction
    with mysql.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET age = age + 1 WHERE name = %s", ("Alice",))
        cursor.close()
    print("Updated users:", mysql.execute_query("SELECT * FROM users"))
