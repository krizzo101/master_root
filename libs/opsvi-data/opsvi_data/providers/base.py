"""Base database provider interface for OPSVI Data library.

Comprehensive database abstraction for the OPSVI ecosystem
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncIterator
import asyncio
import logging
from enum import Enum
from datetime import datetime
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field, ConfigDict

from opsvi_foundation import BaseComponent, ComponentError, BaseSettings

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database type enumeration."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    ARANGODB = "arangodb"
    NEO4J = "neo4j"


class ConnectionState(Enum):
    """Database connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class DataError(ComponentError):
    """Base exception for data errors."""

    pass


class DatabaseError(DataError):
    """Database-specific errors."""

    pass


class ConnectionError(DatabaseError):
    """Connection-related errors."""

    pass


class QueryError(DatabaseError):
    """Query-related errors."""

    pass


class TransactionError(DatabaseError):
    """Transaction-related errors."""

    pass


class DataConfig(BaseSettings):
    """Base configuration for database providers."""

    # Connection configuration
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port") = Field(description="Database port")
    database: str = Field(default="opsvi", description="Database name") = Field(description="Database name")
    username: Optional[str] = Field(default=None, description="Database username")
    password: Optional[str] = Field(default=None, description="Database password")

    # Connection pool configuration
    min_connections: int = Field(default=1, description="Minimum connections in pool")
    max_connections: int = Field(default=10, description="Maximum connections in pool")
    connection_timeout: float = Field(
        default=30.0, description="Connection timeout in seconds"
    )
    command_timeout: float = Field(
        default=30.0, description="Command timeout in seconds"
    )

    # SSL configuration
    ssl_mode: Optional[str] = Field(default=None, description="SSL mode")
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL key path")
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA certificate path")

    # Connection string (alternative to individual fields)
    connection_string: Optional[str] = Field(
        default=None, description="Full connection string"
    )

    # Additional options
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional connection options"
    )

    model_config = ConfigDict(env_prefix="OPSVI_DATA_")


class QueryResult(BaseModel):
    """Result of a database query."""

    rows: List[Dict[str, Any]] = Field(description="Query result rows")
    row_count: int = Field(description="Number of rows returned")
    affected_rows: int = Field(default=0, description="Number of affected rows")
    last_insert_id: Optional[Any] = Field(default=None, description="Last insert ID")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Transaction(BaseModel):
    """Database transaction context."""

    id: str = Field(description="Transaction ID")
    started_at: datetime = Field(description="Transaction start time")
    is_active: bool = Field(default=True, description="Whether transaction is active")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseDatabaseProvider(BaseComponent):
    """Base class for database providers.

    Provides common functionality for all database providers in the OPSVI ecosystem.
    """

    def __init__(self, config: DataConfig, **kwargs: Any) -> None:
        """Initialize database provider.

        Args:
            config: Database configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(f"db-provider-{id(self)}", config.model_dump())
        self.config = config
        self._connection_pool: Optional[Any] = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._query_count = 0
        self._error_count = 0
        self._start_time = datetime.utcnow()

    async def _initialize_impl(self) -> None:
        """Initialize the database connection pool."""
        try:
            self._connection_state = ConnectionState.CONNECTING
            self._connection_pool = await self._create_connection_pool()
            self._connection_state = ConnectionState.CONNECTED
            logger.info(f"Initialized database provider for {self.config.database}")
        except Exception as e:
            self._connection_state = ConnectionState.ERROR
            logger.error(f"Failed to initialize database provider: {e}")
            raise DatabaseError(f"Provider initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown the database connection pool."""
        try:
            if self._connection_pool:
                await self._close_connection_pool()
            self._connection_state = ConnectionState.DISCONNECTED
            logger.info("Database provider shutdown successfully")
        except Exception as e:
            logger.error(f"Failed to shutdown database provider: {e}")
            raise DatabaseError(f"Provider shutdown failed: {e}") from e

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        try:
            if self._connection_state != ConnectionState.CONNECTED:
                return False

            # Try a simple health check query
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    @abstractmethod
    async def _create_connection_pool(self) -> Any:
        """Create the database connection pool."""
        pass

    @abstractmethod
    async def _close_connection_pool(self) -> None:
        """Close the database connection pool."""
        pass

    @abstractmethod
    async def _execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Execute a database query."""
        pass

    @abstractmethod
    async def _begin_transaction(self) -> Transaction:
        """Begin a database transaction."""
        pass

    @abstractmethod
    async def _commit_transaction(self, transaction: Transaction) -> None:
        """Commit a database transaction."""
        pass

    @abstractmethod
    async def _rollback_transaction(self, transaction: Transaction) -> None:
        """Rollback a database transaction."""
        pass

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Execute a database query."""
        if not self._initialized:
            raise DatabaseError("Database provider not initialized")

        self._query_count += 1

        try:
            result = await self._execute_query(query, params)
            return result
        except Exception as e:
            self._error_count += 1
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query failed: {e}") from e

    async def execute_many(
        self, query: str, params_list: List[Dict[str, Any]]
    ) -> QueryResult:
        """Execute a query with multiple parameter sets."""
        if not self._initialized:
            raise DatabaseError("Database provider not initialized")

        self._query_count += 1

        try:
            # Default implementation - execute each query separately
            # Subclasses can override for better performance
            all_rows = []
            total_affected = 0
            last_insert_id = None

            for params in params_list:
                result = await self._execute_query(query, params)
                all_rows.extend(result.rows)
                total_affected += result.affected_rows
                if result.last_insert_id:
                    last_insert_id = result.last_insert_id

            return QueryResult(
                rows=all_rows,
                row_count=len(all_rows),
                affected_rows=total_affected,
                last_insert_id=last_insert_id,
            )
        except Exception as e:
            self._error_count += 1
            logger.error(f"Batch query execution failed: {e}")
            raise QueryError(f"Batch query failed: {e}") from e

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        if not self._initialized:
            raise DatabaseError("Database provider not initialized")

        transaction = None
        try:
            transaction = await self._begin_transaction()
            yield transaction
            await self._commit_transaction(transaction)
        except Exception as e:
            if transaction:
                await self._rollback_transaction(transaction)
            raise TransactionError(f"Transaction failed: {e}") from e

    async def stream_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream query results."""
        if not self._initialized:
            raise DatabaseError("Database provider not initialized")

        self._query_count += 1

        try:
            async for row in self._stream_query(query, params):
                yield row
        except Exception as e:
            self._error_count += 1
            logger.error(f"Stream query failed: {e}")
            raise QueryError(f"Stream query failed: {e}") from e

    @abstractmethod
    async def _stream_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream query results (implementation specific)."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics."""
        uptime = datetime.utcnow() - self._start_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "connection_state": self._connection_state.value,
            "total_queries": self._query_count,
            "error_count": self._error_count,
            "success_rate": (self._query_count - self._error_count)
            / max(self._query_count, 1),
            "initialized": self._initialized,
        }
