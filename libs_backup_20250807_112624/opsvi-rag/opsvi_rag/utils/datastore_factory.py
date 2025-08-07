"""
Datastore Factory for OPSVI-RAG

Factory pattern implementation for creating and managing different datastore instances.
Provides unified interface for datastore creation and configuration.
"""

import logging
from typing import Any

from ..base import BaseDatastore
from ..datastores import (
    ChromaDBConfig,
    ChromaDBStore,
    Neo4jConfig,
    Neo4jStore,
    QdrantConfig,
    QdrantStore,
    SQLiteConfig,
    SQLiteStore,
)

logger = logging.getLogger(__name__)


class DatastoreFactory:
    """Factory for creating datastore instances."""

    # Registry of available datastores
    _registry: dict[str, dict[str, Any]] = {
        "qdrant": {
            "class": QdrantStore,
            "config_class": QdrantConfig,
            "description": "Qdrant vector database for high-performance similarity search",
        },
        "neo4j": {
            "class": Neo4jStore,
            "config_class": Neo4jConfig,
            "description": "Neo4j graph database for GraphRAG and knowledge graphs",
        },
        "chromadb": {
            "class": ChromaDBStore,
            "config_class": ChromaDBConfig,
            "description": "ChromaDB vector database for AI-native embeddings",
        },
        "sqlite": {
            "class": SQLiteStore,
            "config_class": SQLiteConfig,
            "description": "SQLite with FTS5 for local hybrid search",
        },
    }

    @classmethod
    def create_datastore(
        self,
        datastore_type: str,
        config: dict[str, Any] | object | None = None,
        **kwargs,
    ) -> BaseDatastore:
        """
        Create a datastore instance.

        Args:
            datastore_type: Type of datastore to create
            config: Configuration object or dictionary
            **kwargs: Additional configuration parameters

        Returns:
            Configured datastore instance

        Raises:
            ValueError: If datastore type is not supported
            TypeError: If configuration is invalid
        """
        if datastore_type not in self._registry:
            available_types = list(self._registry.keys())
            raise ValueError(
                f"Unsupported datastore type: {datastore_type}. "
                f"Available types: {available_types}"
            )

        store_info = self._registry[datastore_type]
        store_class = store_info["class"]
        config_class = store_info["config_class"]

        # Handle configuration
        if config is None:
            # Create default configuration with any provided kwargs
            store_config = config_class(**kwargs)
        elif isinstance(config, dict):
            # Merge provided config with kwargs
            merged_config = {**config, **kwargs}
            store_config = config_class(**merged_config)
        elif isinstance(config, config_class):
            # Use provided configuration object
            store_config = config
            if kwargs:
                logger.warning(f"Ignoring kwargs {kwargs} when config object provided")
        else:
            raise TypeError(
                f"Config must be dict, {config_class.__name__}, or None. "
                f"Got: {type(config)}"
            )

        # Create and return datastore instance
        try:
            datastore = store_class(store_config)
            logger.info(
                f"Created {datastore_type} datastore: {store_info['description']}"
            )
            return datastore
        except Exception as e:
            logger.error(f"Failed to create {datastore_type} datastore: {e}")
            raise

    @classmethod
    def get_available_datastores(cls) -> dict[str, str]:
        """Get list of available datastore types with descriptions."""
        return {name: info["description"] for name, info in cls._registry.items()}

    @classmethod
    def register_datastore(
        cls,
        name: str,
        store_class: type[BaseDatastore],
        config_class: type,
        description: str = "",
    ) -> None:
        """
        Register a new datastore type.

        Args:
            name: Name of the datastore type
            store_class: Datastore implementation class
            config_class: Configuration class
            description: Human-readable description
        """
        if not issubclass(store_class, BaseDatastore):
            raise TypeError("store_class must inherit from BaseDatastore")

        cls._registry[name] = {
            "class": store_class,
            "config_class": config_class,
            "description": description,
        }

        logger.info(f"Registered datastore type: {name}")

    @classmethod
    def unregister_datastore(cls, name: str) -> None:
        """Unregister a datastore type."""
        if name in cls._registry:
            del cls._registry[name]
            logger.info(f"Unregistered datastore type: {name}")
        else:
            logger.warning(f"Datastore type not found: {name}")

    @classmethod
    def create_multi_datastore(
        cls, configs: dict[str, dict[str, Any]], primary: str | None = None
    ) -> "MultiDatastore":
        """
        Create a multi-datastore setup.

        Args:
            configs: Dictionary mapping datastore names to their configurations
            primary: Name of the primary datastore (for writes)

        Returns:
            MultiDatastore instance
        """
        datastores = {}

        for name, config in configs.items():
            datastore_type = config.pop("type")
            datastore = cls.create_datastore(datastore_type, config)
            datastores[name] = datastore

        return MultiDatastore(datastores, primary)


class MultiDatastore(BaseDatastore):
    """
    Multi-datastore wrapper for using multiple datastores together.

    Supports patterns like:
    - Primary/replica setup
    - Specialized datastores for different data types
    - Fallback datastores for reliability
    """

    def __init__(
        self, datastores: dict[str, BaseDatastore], primary: str | None = None
    ):
        super().__init__()
        self.datastores = datastores
        self.primary = primary or list(datastores.keys())[0]

        if self.primary not in self.datastores:
            raise ValueError(f"Primary datastore '{self.primary}' not found")

    @property
    def primary_datastore(self) -> BaseDatastore:
        """Get the primary datastore."""
        return self.datastores[self.primary]

    async def initialize(self) -> None:
        """Initialize all datastores."""
        for name, datastore in self.datastores.items():
            try:
                await datastore.initialize()
                logger.info(f"Initialized datastore: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize datastore {name}: {e}")
                raise

    async def add_document(self, document) -> str:
        """Add document to primary datastore."""
        return await self.primary_datastore.add_document(document)

    async def add_documents(self, documents) -> list:
        """Add documents to primary datastore."""
        return await self.primary_datastore.add_documents(documents)

    async def update_document(self, document_id: str, document) -> None:
        """Update document in primary datastore."""
        await self.primary_datastore.update_document(document_id, document)

    async def delete_document(self, document_id: str) -> None:
        """Delete document from primary datastore."""
        await self.primary_datastore.delete_document(document_id)

    async def get_document(self, document_id: str):
        """Get document from primary datastore."""
        return await self.primary_datastore.get_document(document_id)

    async def search(self, query: str, **kwargs):
        """Search using primary datastore."""
        return await self.primary_datastore.search(query, **kwargs)

    async def count_documents(self, **kwargs) -> int:
        """Count documents in primary datastore."""
        return await self.primary_datastore.count_documents(**kwargs)

    async def list_documents(self, **kwargs):
        """List documents from primary datastore."""
        return await self.primary_datastore.list_documents(**kwargs)

    async def search_all(self, query: str, **kwargs) -> dict[str, Any]:
        """Search across all datastores and combine results."""
        results = {}

        for name, datastore in self.datastores.items():
            try:
                search_results = await datastore.search(query, **kwargs)
                results[name] = search_results
            except Exception as e:
                logger.error(f"Search failed on datastore {name}: {e}")
                results[name] = []

        return results

    async def replicate_to_all(self, document) -> dict[str, str]:
        """Add document to all datastores."""
        results = {}

        for name, datastore in self.datastores.items():
            try:
                doc_id = await datastore.add_document(document)
                results[name] = doc_id
            except Exception as e:
                logger.error(f"Replication failed to datastore {name}: {e}")
                results[name] = None

        return results

    async def close(self) -> None:
        """Close all datastores."""
        for name, datastore in self.datastores.items():
            try:
                await datastore.close()
                logger.info(f"Closed datastore: {name}")
            except Exception as e:
                logger.error(f"Error closing datastore {name}: {e}")


# Convenience functions
def create_qdrant_store(
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "opsvi_documents",
    **kwargs,
) -> QdrantStore:
    """Create a Qdrant datastore with common defaults."""
    return DatastoreFactory.create_datastore(
        "qdrant", host=host, port=port, collection_name=collection_name, **kwargs
    )


def create_neo4j_store(
    uri: str = "bolt://localhost:7687",
    username: str = "neo4j",
    password: str = "password",
    **kwargs,
) -> Neo4jStore:
    """Create a Neo4j datastore with common defaults."""
    return DatastoreFactory.create_datastore(
        "neo4j", uri=uri, username=username, password=password, **kwargs
    )


def create_chromadb_store(
    persist_directory: str = "./chroma_db",
    collection_name: str = "opsvi_documents",
    **kwargs,
) -> ChromaDBStore:
    """Create a ChromaDB datastore with common defaults."""
    return DatastoreFactory.create_datastore(
        "chromadb",
        persist_directory=persist_directory,
        collection_name=collection_name,
        **kwargs,
    )


def create_sqlite_store(
    database_path: str = "./rag_database.db",
    fts_enabled: bool = True,
    vector_search_enabled: bool = True,
    **kwargs,
) -> SQLiteStore:
    """Create a SQLite datastore with common defaults."""
    return DatastoreFactory.create_datastore(
        "sqlite",
        database_path=database_path,
        fts_enabled=fts_enabled,
        vector_search_enabled=vector_search_enabled,
        **kwargs,
    )
