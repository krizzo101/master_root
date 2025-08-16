"""
DRY Database Connection Factory - Single Source of Truth for ArangoDB Connections

This factory eliminates duplication of ArangoDB connection logic across 5+ files.
Implements proper connection management, error handling, and async support.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Protocol, runtime_checkable
from datetime import datetime
from abc import ABC, abstractmethod

from arango import ArangoClient


logger = logging.getLogger(__name__)


@runtime_checkable
class DatabaseConfig(Protocol):
    """Type protocol for database configuration."""

    host: str
    database: str
    username: str
    password: str


class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors."""

    pass


class ArangoConnectionManager:
    """
    Centralized ArangoDB connection manager implementing DRY principles.

    Eliminates code duplication across:
    - database.py
    - cognitive_database_client.py
    - cognitive_database.py
    - api_gateway.py
    - checkpointer.py

    Benefits:
    - Single source of truth for connection logic
    - Consistent error handling
    - Centralized configuration management
    - Reusable across all database clients
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[ArangoClient] = None
        self.db = None
        self.async_db = None
        self._connected = False
        self._connection_attempts = 0
        self._max_retries = 3

    async def connect(
        self, ensure_database: bool = True, required_collections: Optional[list] = None
    ) -> bool:
        """
        Connect to ArangoDB with comprehensive error handling.

        Args:
            ensure_database: Create database if it doesn't exist
            required_collections: List of collections to ensure exist

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize client
            self.client = ArangoClient(hosts=self.config.host)

            if ensure_database:
                await self._ensure_database()

            # Connect to target database
            self.db = self.client.db(
                self.config.database,
                username=self.config.username,
                password=self.config.password,
            )

            # Initialize async execution context
            self.async_db = self.db.begin_async_execution(return_result=True)

            # Ensure required collections if specified
            if required_collections:
                await self._ensure_collections(required_collections)

            self._connected = True
            self._connection_attempts = 0
            logger.info(
                f"Successfully connected to ArangoDB at {self.config.host}/{self.config.database}"
            )
            return True

        except Exception as e:
            self._connection_attempts += 1
            logger.error(
                f"Failed to connect to ArangoDB (attempt {self._connection_attempts}): {e}"
            )

            if self._connection_attempts < self._max_retries:
                logger.info(f"Retrying connection in 2 seconds...")
                await asyncio.sleep(2)
                return await self.connect(ensure_database, required_collections)
            else:
                raise DatabaseConnectionError(
                    f"Failed to connect after {self._max_retries} attempts: {e}"
                )

    async def _ensure_database(self) -> None:
        """Ensure target database exists, create if needed."""
        try:
            sys_db = self.client.db(
                "_system", username=self.config.username, password=self.config.password
            )

            if not sys_db.has_database(self.config.database):
                sys_db.create_database(self.config.database)
                logger.info(f"Created database: {self.config.database}")

        except Exception as e:
            logger.warning(f"Could not ensure database exists: {e}")
            # Continue - database might exist but we lack permissions to check

    async def _ensure_collections(self, collections: list) -> None:
        """Ensure required collections exist."""
        for collection_name in collections:
            try:
                if not self.db.has_collection(collection_name):
                    self.db.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
            except Exception as e:
                logger.warning(f"Could not ensure collection {collection_name}: {e}")

    async def execute_async_query(
        self, query: str, bind_vars: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Execute AQL query asynchronously with consistent error handling.

        Args:
            query: AQL query string
            bind_vars: Query bind variables

        Returns:
            Query result or None if failed
        """
        if not self._connected:
            logger.error("Not connected to database")
            return None

        try:
            job = self.async_db.aql.execute(query, bind_vars=bind_vars or {})

            # Wait for completion with timeout
            timeout_counter = 0
            while (
                job.status() != "done" and timeout_counter < 1000
            ):  # 10 second timeout
                await asyncio.sleep(0.01)
                timeout_counter += 1

            if job.status() != "done":
                logger.error("Query timed out")
                return None

            return job.result()

        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return None

    async def insert_document(
        self, collection: str, document: Dict[str, Any], overwrite: bool = False
    ) -> bool:
        """
        Insert document with consistent error handling.

        Args:
            collection: Collection name
            document: Document to insert
            overwrite: Whether to overwrite existing document

        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            # Add timestamp if not present
            if "created" not in document:
                document["created"] = datetime.utcnow().isoformat() + "Z"
            if "updated" not in document:
                document["updated"] = datetime.utcnow().isoformat() + "Z"

            job = self.async_db.collection(collection).insert(
                document, overwrite=overwrite
            )

            # Wait for completion
            while job.status() != "done":
                await asyncio.sleep(0.01)

            result = job.result()
            logger.debug(f"Inserted document in {collection}: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to insert document in {collection}: {e}")
            return False

    async def cleanup_old_documents(
        self, collection: str, timestamp_field: str = "created", days_old: int = 30
    ) -> bool:
        """
        Clean up old documents with consistent logic.

        Args:
            collection: Collection to clean
            timestamp_field: Field containing timestamp
            days_old: Age threshold in days

        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            logger.error("Not connected to database")
            return False

        try:
            cutoff_date = (
                datetime.utcnow()
                .replace(day=datetime.utcnow().day - days_old)
                .isoformat()
            ) + "Z"

            query = f"""
            FOR doc IN {collection}
            FILTER doc.{timestamp_field} < @cutoff
            REMOVE doc IN {collection}
            """

            result = await self.execute_async_query(query, {"cutoff": cutoff_date})

            if result is not None:
                logger.info(f"Cleaned up old documents in {collection}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to cleanup old documents in {collection}: {e}")
            return False

    async def disconnect(self) -> None:
        """Clean disconnect from database."""
        if self.async_db:
            try:
                if hasattr(self.db, "clear_async_jobs"):
                    self.db.clear_async_jobs()
            except Exception as e:
                logger.warning(f"Error clearing async jobs: {e}")

        self._connected = False
        logger.info("Disconnected from ArangoDB")

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._connected

    def __del__(self):
        """Cleanup on destruction."""
        if self._connected:
            logger.info(
                "ArangoConnectionManager destroyed - connection may still be open"
            )


class DatabaseClientBase(ABC):
    """
    Abstract base class for database clients implementing DRY principles.

    Eliminates common patterns across all database client implementations.
    """

    def __init__(self, host: str, database: str, username: str, password: str):
        from types import SimpleNamespace

        config = SimpleNamespace()
        config.host = host
        config.database = database
        config.username = username
        config.password = password

        self.connection_manager = ArangoConnectionManager(config)
        self._collections: list = []

    @abstractmethod
    def get_required_collections(self) -> list:
        """Return list of collections required by this client."""
        pass

    async def connect(self) -> bool:
        """Connect using shared connection manager."""
        return await self.connection_manager.connect(
            ensure_database=True, required_collections=self.get_required_collections()
        )

    async def disconnect(self) -> None:
        """Disconnect using shared connection manager."""
        await self.connection_manager.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connection_manager.is_connected

    def require_connection(self):
        """Decorator to ensure connection exists."""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                if not self.is_connected:
                    logger.error(f"Not connected to database for {func.__name__}")
                    return None
                return await func(*args, **kwargs)

            return wrapper

        return decorator


# Configuration factory for different client types
class DatabaseConfigFactory:
    """Factory for creating database configurations for different client types."""

    # Default configurations for different environments
    DEFAULT_CONFIGS = {
        "development": {
            "host": "http://127.0.0.1:8529",
            "database": "asea_dev_db",
            "username": "root",
            "password": "arango_dev_password",
        },
        "production": {
            "host": "http://127.0.0.1:8531",
            "database": "asea_prod_db",
            "username": "root",
            "password": "arango_production_password",
        },
        "testing": {
            "host": "http://127.0.0.1:8529",
            "database": "asea_test_db",
            "username": "root",
            "password": "arango_test_password",
        },
    }

    @classmethod
    def create_config(
        cls, environment: str = "production", overrides: Optional[Dict[str, str]] = None
    ) -> object:
        """
        Create database configuration for specified environment.

        Args:
            environment: Environment name (development, production, testing)
            overrides: Configuration overrides

        Returns:
            Configuration object
        """
        from types import SimpleNamespace

        if environment not in cls.DEFAULT_CONFIGS:
            raise ValueError(
                f"Unknown environment: {environment}. Available: {list(cls.DEFAULT_CONFIGS.keys())}"
            )

        config_data = cls.DEFAULT_CONFIGS[environment].copy()

        if overrides:
            config_data.update(overrides)

        config = SimpleNamespace()
        config.host = config_data["host"]
        config.database = config_data["database"]
        config.username = config_data["username"]
        config.password = config_data["password"]

        return config
