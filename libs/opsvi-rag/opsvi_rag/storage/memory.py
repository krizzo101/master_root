"""
In-memory vector store implementation.

Provides a simple in-memory vector store for testing and development
with basic similarity search capabilities.
"""

from __future__ import annotations

import math
from typing import Any
from uuid import uuid4

from opsvi_foundation import get_logger
from pydantic import Field

from .base import (
    BaseVectorStore,
    Document,
    Metadata,
    SearchResult,
    VectorStoreConfig,
    VectorStoreError,
)


class InMemoryConfig(VectorStoreConfig):
    """Configuration for in-memory vector store."""

    collection_name: str = Field(
        default="in_memory_collection", description="Collection name"
    )
    vector_dimensions: int = Field(..., description="Number of dimensions in vectors")
    distance_metric: str = Field(
        default="cosine", description="Distance metric for similarity"
    )

    class Config:
        extra = "allow"


class InMemoryStore(BaseVectorStore):
    """
    In-memory vector store implementation.

    Provides a simple in-memory vector store for testing and development
    with basic similarity search capabilities.
    """

    def __init__(self, config: InMemoryConfig, **kwargs):
        """Initialize the in-memory vector store."""
        super().__init__(config, **kwargs)
        self.config = config
        self.logger = get_logger(__name__)

        # In-memory storage
        self._documents: dict[str, Document] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the in-memory vector store."""
        self._initialized = True
        self.logger.info(
            f"Initialized in-memory vector store: {self.config.collection_name}"
        )

    async def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """Add documents to the in-memory store."""
        if not documents:
            return []

        await self._ensure_initialized()

        try:
            added_ids = []
            for doc in documents:
                # Ensure document has an ID
                if not doc.id:
                    doc.id = str(uuid4())

                # Ensure document has embedding
                if doc.embedding is None:
                    raise VectorStoreError("Documents must have embeddings provided")

                # Validate embedding dimensions
                if len(doc.embedding) != self.config.vector_dimensions:
                    raise VectorStoreError(
                        f"Embedding dimensions {len(doc.embedding)} don't match expected {self.config.vector_dimensions}"
                    )

                # Store document
                self._documents[doc.id] = doc
                added_ids.append(doc.id)

            self.logger.info(f"Added {len(added_ids)} documents to in-memory store")
            return added_ids

        except Exception as e:
            raise VectorStoreError(
                f"Failed to add documents to in-memory store: {e}"
            ) from e

    async def add_embeddings(
        self, embeddings: list[list[float]], documents: list[Document], **kwargs
    ) -> list[str]:
        """Add documents with pre-computed embeddings."""
        if len(embeddings) != len(documents):
            raise VectorStoreError(
                "Number of embeddings must match number of documents"
            )

        # Create documents with embeddings
        docs_with_embeddings = []
        for doc, embedding in zip(documents, embeddings, strict=False):
            doc.embedding = embedding
            docs_with_embeddings.append(doc)

        return await self.add_documents(docs_with_embeddings, **kwargs)

    async def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> list[SearchResult]:
        """Search for similar documents using vector similarity."""
        await self._ensure_initialized()

        try:
            # Validate query embedding dimensions
            if len(query_embedding) != self.config.vector_dimensions:
                raise VectorStoreError(
                    f"Query embedding dimensions {len(query_embedding)} don't match expected {self.config.vector_dimensions}"
                )

            # Calculate similarities
            similarities = []
            for doc_id, doc in self._documents.items():
                # Apply metadata filter if specified
                if filter_metadata and not self._matches_filter(
                    doc.metadata, filter_metadata
                ):
                    continue

                # Calculate similarity
                similarity = self._calculate_similarity(query_embedding, doc.embedding)

                # Apply score threshold if specified
                if score_threshold is not None and similarity < score_threshold:
                    continue

                similarities.append((doc, similarity))

            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Take top results
            results = []
            for doc, similarity in similarities[:limit]:
                result = SearchResult(
                    document=doc,
                    score=similarity,
                    distance=1.0 - similarity
                    if self.config.distance_metric == "cosine"
                    else None,
                )
                results.append(result)

            return results

        except Exception as e:
            raise VectorStoreError(f"Failed to search in-memory store: {e}") from e

    async def get_document(self, document_id: str) -> Document | None:
        """Retrieve a document by ID."""
        await self._ensure_initialized()

        return self._documents.get(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        await self._ensure_initialized()

        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

    async def update_document(self, document_id: str, document: Document) -> bool:
        """Update an existing document."""
        await self._ensure_initialized()

        if document_id not in self._documents:
            return False

        # Ensure the document has the correct ID
        document.id = document_id

        # Validate embedding dimensions if provided
        if (
            document.embedding
            and len(document.embedding) != self.config.vector_dimensions
        ):
            raise VectorStoreError(
                f"Embedding dimensions {len(document.embedding)} don't match expected {self.config.vector_dimensions}"
            )

        self._documents[document_id] = document
        return True

    async def list_documents(
        self,
        limit: int | None = None,
        offset: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[Document]:
        """List documents in the store."""
        await self._ensure_initialized()

        documents = list(self._documents.values())

        # Apply metadata filter if specified
        if filter_metadata:
            documents = [
                doc
                for doc in documents
                if self._matches_filter(doc.metadata, filter_metadata)
            ]

        # Apply offset and limit
        if offset:
            documents = documents[offset:]
        if limit:
            documents = documents[:limit]

        return documents

    async def count_documents(self) -> int:
        """Get the total number of documents in the store."""
        await self._ensure_initialized()
        return len(self._documents)

    async def clear(self) -> None:
        """Clear all documents from the store."""
        await self._ensure_initialized()
        self._documents.clear()
        self.logger.info("Cleared all documents from in-memory store")

    async def health_check(self) -> bool:
        """Perform a health check on the in-memory store."""
        return self._initialized

    async def _ensure_initialized(self) -> None:
        """Ensure the store is initialized."""
        if not self._initialized:
            await self.initialize()

    def _calculate_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate similarity between two vectors."""
        if self.config.distance_metric == "cosine":
            return self._cosine_similarity(vec1, vec2)
        elif self.config.distance_metric == "dot":
            return self._dot_product(vec1, vec2)
        elif self.config.distance_metric == "euclidean":
            return 1.0 / (1.0 + self._euclidean_distance(vec1, vec2))
        else:
            # Default to cosine similarity
            return self._cosine_similarity(vec1, vec2)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _dot_product(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate dot product between two vectors."""
        return sum(a * b for a, b in zip(vec1, vec2, strict=False))

    def _euclidean_distance(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate Euclidean distance between two vectors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2, strict=False)))

    def _matches_filter(
        self, metadata: Metadata, filter_metadata: dict[str, Any]
    ) -> bool:
        """Check if metadata matches the filter criteria."""
        for key, value in filter_metadata.items():
            metadata_value = getattr(metadata, key, None)

            if isinstance(value, list):
                if metadata_value not in value:
                    return False
            else:
                if metadata_value != value:
                    return False

        return True
