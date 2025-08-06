"""
OPSVI RAG Library

Retrieval-Augmented Generation library for the OPSVI ecosystem.
Provides vector search, embedding management, and RAG capabilities.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

from .processors.document_processor import DocumentProcessor
from .providers.embedding_provider import BaseEmbeddingProvider
from .providers.openai_embedding import OpenAIEmbeddingProvider
from .providers.sentence_transformers_embedding import (
    SentenceTransformersEmbeddingProvider,
)
from .retrieval.rag_pipeline import RAGPipeline
from .retrieval.retrieval_engine import RetrievalEngine
from .storage.qdrant_client import QdrantVectorStore

__all__ = [
    # Storage
    "QdrantVectorStore",
    # Providers
    "BaseEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "SentenceTransformersEmbeddingProvider",
    # Processors
    "DocumentProcessor",
    # Retrieval
    "RetrievalEngine",
    "RAGPipeline",
]
