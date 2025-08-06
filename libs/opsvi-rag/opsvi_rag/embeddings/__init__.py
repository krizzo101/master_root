"""
Embedding generation and management for RAG systems.

Provides unified interfaces for various embedding providers including
OpenAI, Sentence Transformers, and other vector generation services.
"""

from .openai import OpenAIEmbeddingConfig, OpenAIEmbeddingProvider
from .providers import (
    BaseEmbeddingProvider,
    EmbeddingProviderFactory,
    ProviderType,
)
from .sentence_transformers import (
    SentenceTransformerConfig,
    SentenceTransformerEmbeddingProvider,
)

# Register providers with the factory
EmbeddingProviderFactory.register_provider(ProviderType.OPENAI, OpenAIEmbeddingProvider)
EmbeddingProviderFactory.register_provider(
    ProviderType.SENTENCE_TRANSFORMERS, SentenceTransformerEmbeddingProvider
)

__all__ = [
    # Base classes
    "BaseEmbeddingProvider",
    "EmbeddingProviderFactory",
    "ProviderType",
    # OpenAI provider
    "OpenAIEmbeddingProvider",
    "OpenAIEmbeddingConfig",
    # Sentence Transformers provider
    "SentenceTransformerEmbeddingProvider",
    "SentenceTransformerConfig",
]
