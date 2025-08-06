"""
opsvi-rag Library

Domain-specific components for the OPSVI ecosystem.
Builds on opsvi-foundation for shared concerns.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Import foundation components
from opsvi_foundation import (
    AuthManager,
    BaseComponent,
    CircuitBreaker,
    FoundationConfig,
    get_logger,
)

# Import analytics
from .analytics.performance import (
    PerformanceConfig,
    PerformanceMonitor,
    profile_datastore_operation,
    profile_search,
)

# Import domain-specific components
from .core import RAGConfig, config
from .core.exceptions import RAGConfigurationError, RAGError, RAGValidationError

# Import enhanced datastore components
from .datastores import (
    BaseDatastore,
    ChromaDBConfig,
    ChromaDBStore,
    Neo4jConfig,
    Neo4jStore,
    SQLiteConfig,
    SQLiteStore,
)

# Import embedding components
from .embeddings import (
    BaseEmbeddingProvider,
    EmbeddingProviderFactory,
    OpenAIEmbeddingConfig,
    OpenAIEmbeddingProvider,
    ProviderType,
    SentenceTransformerConfig,
    SentenceTransformerEmbeddingProvider,
)

# Import storage components
from .storage import (
    BaseVectorStore,
    Document,
    InMemoryConfig,
    InMemoryStore,
    Metadata,
    QdrantConfig,
    QdrantStore,
    SearchResult,
    VectorStoreConfig,
)

# Import utilities
from .utils.datastore_factory import (
    DatastoreFactory,
    create_chromadb_store,
    create_neo4j_store,
    create_sqlite_store,
)

__all__ = [
    # Foundation exports
    "FoundationConfig",
    "AuthManager",
    "CircuitBreaker",
    "BaseComponent",
    "get_logger",
    # Domain exports
    "RAGConfig",
    "config",
    "RAGError",
    "RAGValidationError",
    "RAGConfigurationError",
    # Embedding exports
    "BaseEmbeddingProvider",
    "EmbeddingProviderFactory",
    "ProviderType",
    "OpenAIEmbeddingProvider",
    "OpenAIEmbeddingConfig",
    "SentenceTransformerEmbeddingProvider",
    "SentenceTransformerConfig",
    # Storage exports
    "BaseVectorStore",
    "VectorStoreConfig",
    "SearchResult",
    "Document",
    "Metadata",
    "QdrantStore",
    "QdrantConfig",
    "InMemoryStore",
    "InMemoryConfig",
    # Enhanced datastore exports
    "BaseDatastore",
    "Neo4jStore",
    "Neo4jConfig",
    "ChromaDBStore",
    "ChromaDBConfig",
    "SQLiteStore",
    "SQLiteConfig",
    # Utility exports
    "DatastoreFactory",
    "create_neo4j_store",
    "create_chromadb_store",
    "create_sqlite_store",
    # Analytics exports
    "PerformanceMonitor",
    "PerformanceConfig",
    "profile_search",
    "profile_datastore_operation",
]
