"""OPSVI RAG Library - Retrieval Augmented Generation utilities."""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.ai"

from .client import RAGClient
from .embeddings import get_embeddings
from .search import search_documents

__all__ = [
    "RAGClient",
    "get_embeddings",
    "search_documents",
]
