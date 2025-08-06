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

# Import domain-specific components
from .core import RAGConfig, config
from .core.exceptions import RAGConfigurationError, RAGError, RAGValidationError

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
]
