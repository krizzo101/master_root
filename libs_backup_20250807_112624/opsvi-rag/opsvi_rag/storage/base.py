"""
Base vector store interface and data models.

Defines the common interface for all vector stores and provides
data models for documents, metadata, and search results.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class VectorStoreError(ComponentError):
    """Base exception for vector store errors."""

    pass


class VectorStoreConfig(BaseModel):
    """Base configuration for vector stores."""

    collection_name: str = Field(..., description="Name of the vector collection")
    vector_dimensions: int = Field(..., description="Number of dimensions in vectors")
    distance_metric: str = Field(
        default="cosine", description="Distance metric for similarity"
    )
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")

    class Config:
        extra = "allow"


class Metadata(BaseModel):
    """Document metadata model."""

    id: str | None = Field(default=None, description="Document ID")
    source: str | None = Field(default=None, description="Document source")
    title: str | None = Field(default=None, description="Document title")
    author: str | None = Field(default=None, description="Document author")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None, description="Last update timestamp"
    )
    tags: list[str] = Field(default_factory=list, description="Document tags")
    custom_fields: dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata fields"
    )

    class Config:
        extra = "allow"


class Document(BaseModel):
    """Document model with content and metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Metadata = Field(
        default_factory=Metadata, description="Document metadata"
    )
    embedding: list[float] | None = Field(
        default=None, description="Document embedding vector"
    )

    class Config:
        extra = "allow"


class SearchResult(BaseModel):
    """Search result model."""

    document: Document = Field(..., description="Retrieved document")
    score: float = Field(..., description="Similarity score")
    distance: float | None = Field(default=None, description="Distance metric value")

    class Config:
        extra = "allow"


class BaseVectorStore(BaseComponent, ABC):
    """
    Abstract base class for vector stores.

    Provides a unified interface for storing and retrieving vector embeddings
    with metadata and similarity search capabilities.
    """

    def __init__(self, config: VectorStoreConfig, **kwargs):
        """Initialize the vector store."""
        super().__init__(**kwargs)
        self.config = config
        self.logger = get_logger(__name__)

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector store and create necessary collections.

        Raises:
            VectorStoreError: If initialization fails
        """
        pass

    @abstractmethod
    async def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of documents to add
            **kwargs: Additional store-specific arguments

        Returns:
            List of document IDs that were added

        Raises:
            VectorStoreError: If adding documents fails
        """
        pass

    @abstractmethod
    async def add_embeddings(
        self, embeddings: list[list[float]], documents: list[Document], **kwargs
    ) -> list[str]:
        """
        Add documents with pre-computed embeddings.

        Args:
            embeddings: List of embedding vectors
            documents: List of documents (embeddings will be ignored)
            **kwargs: Additional store-specific arguments

        Returns:
            List of document IDs that were added

        Raises:
            VectorStoreError: If adding embeddings fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[SearchResult]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filter_metadata: Metadata filters to apply
            **kwargs: Additional search parameters

        Returns:
            List of search results ordered by similarity

        Raises:
            VectorStoreError: If search fails
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Document | None:
        """
        Retrieve a document by ID.

        Args:
            document_id: Document ID to retrieve

        Returns:
            Document if found, None otherwise

        Raises:
            VectorStoreError: If retrieval fails
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            document_id: Document ID to delete

        Returns:
            True if document was deleted, False if not found

        Raises:
            VectorStoreError: If deletion fails
        """
        pass

    @abstractmethod
    async def update_document(self, document_id: str, document: Document) -> bool:
        """
        Update an existing document.

        Args:
            document_id: Document ID to update
            document: Updated document content

        Returns:
            True if document was updated, False if not found

        Raises:
            VectorStoreError: If update fails
        """
        pass

    @abstractmethod
    async def list_documents(
        self,
        limit: int | None = None,
        offset: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[Document]:
        """
        List documents in the store.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            filter_metadata: Metadata filters to apply

        Returns:
            List of documents

        Raises:
            VectorStoreError: If listing fails
        """
        pass

    @abstractmethod
    async def count_documents(self) -> int:
        """
        Get the total number of documents in the store.

        Returns:
            Number of documents

        Raises:
            VectorStoreError: If count operation fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all documents from the store.

        Raises:
            VectorStoreError: If clear operation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check on the vector store.

        Returns:
            True if the store is healthy, False otherwise
        """
        pass

    async def search_by_text(
        self,
        query_text: str,
        embedding_provider,
        limit: int = 10,
        score_threshold: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[SearchResult]:
        """
        Search for similar documents using text query.

        Args:
            query_text: Text query to search for
            embedding_provider: Provider to generate query embedding
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            filter_metadata: Metadata filters to apply
            **kwargs: Additional search parameters

        Returns:
            List of search results ordered by similarity
        """
        # Generate embedding for query text
        query_embedding = await embedding_provider.embed_single(query_text)

        # Perform vector search
        return await self.search(
            query_embedding=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            filter_metadata=filter_metadata,
            **kwargs,
        )

    async def batch_add_documents(
        self, documents: list[Document], batch_size: int = 100, **kwargs
    ) -> list[str]:
        """
        Add documents in batches.

        Args:
            documents: List of documents to add
            batch_size: Size of each batch
            **kwargs: Additional arguments

        Returns:
            List of all document IDs that were added
        """
        all_ids = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_ids = await self.add_documents(batch, **kwargs)
            all_ids.extend(batch_ids)

        return all_ids
