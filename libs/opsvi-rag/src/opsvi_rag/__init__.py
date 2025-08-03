"""OPSVI RAG Library - Retrieval Augmented Generation utilities."""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.ai"

from .client import QdrantClient
from .embeddings import EmbeddingModel
from .search import SearchEngine

__all__ = [
    "QdrantClient",
    "EmbeddingModel",
    "SearchEngine",
]
