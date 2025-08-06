"""
Embedding providers for OPSVI RAG system.

This module provides a pluggable embedding provider interface supporting:
- OpenAI embeddings (leveraging opsvi-llm)
- Sentence Transformers embeddings (for on-premise capabilities)
- Factory pattern for dynamic provider selection
- Async API conformity for pipeline integration
"""

from .base import BaseEmbeddingProvider
from .factory import EmbeddingProviderFactory
from .openai_provider import OpenAIEmbeddingProvider
from .sentence_transformer_provider import SentenceTransformerEmbeddingProvider

__all__ = [
    "BaseEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "SentenceTransformerEmbeddingProvider",
    "EmbeddingProviderFactory",
]
