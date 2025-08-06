"""
OPSVI RAG Library

Retrieval-Augmented Generation library for the OPSVI ecosystem.
Provides vector search, embedding management, and RAG capabilities.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

from .providers import (
    BaseEmbeddingProvider,
    EmbeddingProviderFactory,
    OpenAIEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
)
from .storage.qdrant_client import QdrantVectorStore

__all__ = [
    # Storage
    "QdrantVectorStore",
    # Providers
    "BaseEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "EmbeddingProviderFactory",
]
