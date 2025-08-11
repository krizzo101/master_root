"""Tests for OPSVI Data provider functionality."""

import pytest
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from opsvi_data import (
    BaseDatabaseProvider,
    DataConfig,
    QueryResult,
    Transaction,
    DatabaseType,
    ConnectionState,
    DataError,
    DatabaseError,
    ConnectionError,
    QueryError,
    TransactionError,
)
from opsvi_foundation import ComponentError


class MockConnectionPool:
    """Mock connection pool for testing."""

    def __init__(self):
        self.acquire = AsyncMock()
        self.release = AsyncMock()
        self.close = AsyncMock()


class MockTransaction:
    """Mock transaction for testing."""

    def __init__(self, transaction_id: str):
        self.id = transaction_id
        self.started_at = datetime.utcnow()
        self.is_active = True
        self.commit = AsyncMock()
        self.rollback = AsyncMock()


class MockDatabaseProvider(BaseDatabaseProvider):
    """Mock database provider for testing."""

    async def _create_connection_pool(self) -> MockConnectionPool:
        """Create mock connection pool."""
        return MockConnectionPool()

    async def _close_connection_pool(self) -> None:
        """Close mock connection pool."""
        if self._connection_pool:
            await self._connection_pool.close()

    async def _execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Execute mock query."""
        # Mock query execution
        if query == "SELECT 1":
            return QueryResult(
                rows=[{"1": 1}],
                row_count=1,
                affected_rows=0,
            )
        elif query == "INSERT INTO users (name) VALUES ($1)":
            return QueryResult(
                rows=[],
                row_count=0,
                affected_rows=1,
                last_insert_id=123,
            )
        elif query == "SELECT * FROM users":
            return QueryResult(
                rows=[
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Smith"},
                ],
                row_count=2,
                affected_rows=0,
            )
        else:
            return QueryResult(
                rows=[],
                row_count=0,
                affected_rows=0,
            )

    async def _begin_transaction(self) -> Transaction:
        """Begin mock transaction."""
        transaction_id = f"tx_{datetime.utcnow().timestamp()}"
        return Transaction(
            id=transaction_id,
            started_at=datetime.utcnow(),
            is_active=True,
        )

    async def _commit_transaction(self, transaction: Transaction) -> None:
        """Commit mock transaction."""
        transaction.is_active = False

    async def _rollback_transaction(self, transaction: Transaction) -> None:
        """Rollback mock transaction."""
        transaction.is_active = False

    async def _stream_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Stream mock query results."""
        if query == "SELECT * FROM users":
            yield {"id": 1, "name": "John Doe"}
            yield {"id": 2, "name": "Jane Smith"}
        else:
            yield {}


@pytest.fixture
def data_config():
    """Create a test data configuration."""
    return DataConfig(
        host="localhost",
        port=5432,
        database="testdb",
        username="testuser",
        password="testpass",
        min_connections=1,
        max_connections=5,
    )


@pytest.fixture
def mock_provider(data_config):
    """Create a mock database provider."""
    return MockDatabaseProvider(data_config)


class TestDataConfig:
    """Test data configuration."""

    def test_data_config_defaults(self):
        """Test data config default values."""
        config = DataConfig(
            port=5432,
            database="testdb",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.username is None
        assert config.password is None
        assert config.min_connections == 1
        assert config.max_connections == 10
        assert config.connection_timeout == 30.0
        assert config.command_timeout == 30.0
        assert config.ssl_mode is None
        assert config.connection_string is None
        assert config.options == {}

    def test_data_config_custom_values(self):
        """Test data config with custom values."""
        config = DataConfig(
            host="db.example.com",
            port=3306,
            database="production",
            username="admin",
            password="secret",
            min_connections=5,
            max_connections=50,
            connection_timeout=60.0,
            command_timeout=45.0,
            ssl_mode="require",
            options={"charset": "utf8mb4"},
        )

        assert config.host == "db.example.com"
        assert config.port == 3306
        assert config.database == "production"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.min_connections == 5
        assert config.max_connections == 50
        assert config.connection_timeout == 60.0
        assert config.command_timeout == 45.0
        assert config.ssl_mode == "require"
        assert config.options == {"charset": "utf8mb4"}


class TestQueryResult:
    """Test query result model."""

    def test_query_result_creation(self):
        """Test query result creation."""
        result = QueryResult(
            rows=[{"id": 1, "name": "John"}],
            row_count=1,
            affected_rows=0,
            last_insert_id=None,
        )

        assert result.rows == [{"id": 1, "name": "John"}]
        assert result.row_count == 1
        assert result.affected_rows == 0
        assert result.last_insert_id is None

    def test_query_result_with_insert_id(self):
        """Test query result with insert ID."""
        result = QueryResult(
            rows=[],
            row_count=0,
            affected_rows=1,
            last_insert_id=123,
        )

        assert result.rows == []
        assert result.row_count == 0
        assert result.affected_rows == 1
        assert result.last_insert_id == 123


class TestTransaction:
    """Test transaction model."""

    def test_transaction_creation(self):
        """Test transaction creation."""
        transaction = Transaction(
            id="tx_123",
            started_at=datetime.utcnow(),
            is_active=True,
        )

        assert transaction.id == "tx_123"
        assert isinstance(transaction.started_at, datetime)
        assert transaction.is_active is True


class TestMockDatabaseProvider:
    """Test mock database provider functionality."""

    @pytest.mark.asyncio
    async def test_provider_initialization(self, data_config):
        """Test database provider initialization."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        assert provider._initialized
        assert provider._connection_pool is not None
        assert provider._connection_state == ConnectionState.CONNECTED
        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_execute_query(self, data_config):
        """Test database provider query execution."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            # Test simple query
            result = await provider.execute_query("SELECT 1")
            assert result.row_count == 1
            assert result.rows == [{"1": 1}]

            # Test insert query
            result = await provider.execute_query(
                "INSERT INTO users (name) VALUES ($1)", {"name": "John Doe"}
            )
            assert result.affected_rows == 1
            assert result.last_insert_id == 123

            # Test select query
            result = await provider.execute_query("SELECT * FROM users")
            assert result.row_count == 2
            assert len(result.rows) == 2

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_execute_many(self, data_config):
        """Test database provider batch execution."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            params_list = [
                {"name": "John Doe"},
                {"name": "Jane Smith"},
                {"name": "Bob Johnson"},
            ]

            result = await provider.execute_many(
                "INSERT INTO users (name) VALUES ($1)", params_list
            )

            assert result.affected_rows == 3
            assert result.last_insert_id == 123

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_transaction(self, data_config):
        """Test database provider transactions."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            async with provider.transaction() as transaction:
                assert transaction.is_active
                assert isinstance(transaction.id, str)
                assert isinstance(transaction.started_at, datetime)

                # Execute queries within transaction
                result = await provider.execute_query("SELECT 1")
                assert result.row_count == 1

            # Transaction should be committed automatically

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_stream_query(self, data_config):
        """Test database provider streaming queries."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            rows = []
            async for row in provider.stream_query("SELECT * FROM users"):
                rows.append(row)

            assert len(rows) == 2
            assert rows[0]["id"] == 1
            assert rows[0]["name"] == "John Doe"
            assert rows[1]["id"] == 2
            assert rows[1]["name"] == "Jane Smith"

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_health_check(self, data_config):
        """Test database provider health check."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            # Health check should pass
            assert await provider.health_check()

        finally:
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_provider_stats(self, data_config):
        """Test database provider statistics."""
        provider = MockDatabaseProvider(data_config)
        await provider.initialize()

        try:
            stats = provider.get_stats()

            assert "uptime_seconds" in stats
            assert "connection_state" in stats
            assert "total_queries" in stats
            assert "error_count" in stats
            assert "success_rate" in stats
            assert "initialized" in stats
            assert stats["initialized"] is True
            assert stats["connection_state"] == "connected"
            assert stats["total_queries"] == 0
            assert stats["error_count"] == 0

        finally:
            await provider.shutdown()


class TestDatabaseExceptions:
    """Test database exception classes."""

    def test_data_error_inheritance(self):
        """Test data error inheritance."""
        error = DataError("Test error")
        assert isinstance(error, DataError)
        assert isinstance(error, ComponentError)
        assert str(error) == "Test error"

    def test_database_error_inheritance(self):
        """Test database error inheritance."""
        error = DatabaseError("Database error")
        assert isinstance(error, DataError)
        assert str(error) == "Database error"

    def test_connection_error_inheritance(self):
        """Test connection error inheritance."""
        error = ConnectionError("Connection error")
        assert isinstance(error, DatabaseError)
        assert str(error) == "Connection error"

    def test_query_error_inheritance(self):
        """Test query error inheritance."""
        error = QueryError("Query error")
        assert isinstance(error, DatabaseError)
        assert str(error) == "Query error"

    def test_transaction_error_inheritance(self):
        """Test transaction error inheritance."""
        error = TransactionError("Transaction error")
        assert isinstance(error, DatabaseError)
        assert str(error) == "Transaction error"


class TestDatabaseType:
    """Test database type enumeration."""

    def test_database_type_values(self):
        """Test database type values."""
        assert DatabaseType.POSTGRESQL.value == "postgresql"
        assert DatabaseType.MYSQL.value == "mysql"
        assert DatabaseType.SQLITE.value == "sqlite"
        assert DatabaseType.MONGODB.value == "mongodb"
        assert DatabaseType.REDIS.value == "redis"
        assert DatabaseType.ARANGODB.value == "arangodb"
        assert DatabaseType.NEO4J.value == "neo4j"


class TestConnectionState:
    """Test connection state enumeration."""

    def test_connection_state_values(self):
        """Test connection state values."""
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.ERROR.value == "error"
