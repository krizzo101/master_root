"""
Qdrant vector store implementation.

Provides vector storage and retrieval using Qdrant vector database
with proper error handling, batching, and metadata filtering.
"""

from __future__ import annotations

from typing import Any

from opsvi_foundation import get_logger
from pydantic import Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as rest

from .base import (
    BaseVectorStore,
    Document,
    Metadata,
    SearchResult,
    VectorStoreConfig,
    VectorStoreError,
)


class QdrantConfig(VectorStoreConfig):
    """Configuration for Qdrant vector store."""

    url: str = Field(default="http://localhost:6333", description="Qdrant server URL")
    api_key: str | None = Field(default=None, description="Qdrant API key")
    prefer_grpc: bool = Field(default=True, description="Prefer gRPC over HTTP")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    # Collection settings
    collection_name: str = Field(..., description="Name of the vector collection")
    vector_dimensions: int = Field(..., description="Number of dimensions in vectors")
    distance_metric: str = Field(
        default="cosine", description="Distance metric for similarity"
    )

    # Performance settings
    batch_size: int = Field(default=100, description="Batch size for operations")
    on_disk_payload: bool = Field(default=False, description="Store payload on disk")

    class Config:
        extra = "allow"


class QdrantStore(BaseVectorStore):
    """
    Qdrant vector store implementation.

    Provides vector storage and retrieval using Qdrant vector database
    with proper error handling, batching, and metadata filtering.
    """

    def __init__(self, config: QdrantConfig, **kwargs):
        """Initialize the Qdrant vector store."""
        super().__init__(config, **kwargs)
        self.config = config
        self.logger = get_logger(__name__)

        # Initialize Qdrant client
        self.client = AsyncQdrantClient(
            url=config.url,
            api_key=config.api_key,
            prefer_grpc=config.prefer_grpc,
            timeout=config.timeout,
        )

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Qdrant vector store and create collection."""
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.config.collection_name not in collection_names:
                # Create collection
                await self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=rest.VectorParams(
                        size=self.config.vector_dimensions,
                        distance=self._get_distance_metric(),
                        on_disk=self.config.on_disk_payload,
                    ),
                )
                self.logger.info(
                    f"Created Qdrant collection: {self.config.collection_name}"
                )
            else:
                self.logger.info(
                    f"Using existing Qdrant collection: {self.config.collection_name}"
                )

            self._initialized = True

        except Exception as e:
            raise VectorStoreError(f"Failed to initialize Qdrant store: {e}") from e

    def _get_distance_metric(self) -> rest.Distance:
        """Convert distance metric string to Qdrant Distance enum."""
        metric_map = {
            "cosine": rest.Distance.COSINE,
            "dot": rest.Distance.DOT,
            "euclidean": rest.Distance.EUCLID,
        }
        return metric_map.get(self.config.distance_metric, rest.Distance.COSINE)

    async def add_documents(self, documents: list[Document], **kwargs) -> list[str]:
        """Add documents to the Qdrant store."""
        if not documents:
            return []

        await self._ensure_initialized()

        try:
            # Generate embeddings if not provided
            documents_with_embeddings = []
            for doc in documents:
                if doc.embedding is None:
                    # This would require an embedding provider
                    # For now, we'll require embeddings to be provided
                    raise VectorStoreError("Documents must have embeddings provided")
                documents_with_embeddings.append(doc)

            # Prepare points for Qdrant
            points = []
            for doc in documents_with_embeddings:
                point = rest.PointStruct(
                    id=doc.id,
                    vector=doc.embedding,
                    payload=self._document_to_payload(doc),
                )
                points.append(point)

            # Add points to collection
            await self.client.upsert(
                collection_name=self.config.collection_name,
                points=points,
            )

            return [doc.id for doc in documents_with_embeddings]

        except Exception as e:
            raise VectorStoreError(f"Failed to add documents to Qdrant: {e}") from e

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
            # Build search filter
            search_filter = None
            if filter_metadata:
                search_filter = self._build_search_filter(filter_metadata)

            # Perform search
            search_result = await self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False,  # Don't return vectors to save bandwidth
            )

            # Convert to SearchResult objects
            results = []
            for scored_point in search_result:
                document = self._payload_to_document(
                    scored_point.payload, scored_point.id
                )
                result = SearchResult(
                    document=document,
                    score=scored_point.score,
                    distance=1.0 - scored_point.score
                    if self.config.distance_metric == "cosine"
                    else None,
                )
                results.append(result)

            return results

        except Exception as e:
            raise VectorStoreError(f"Failed to search Qdrant store: {e}") from e

    async def get_document(self, document_id: str) -> Document | None:
        """Retrieve a document by ID."""
        await self._ensure_initialized()

        try:
            point = await self.client.retrieve(
                collection_name=self.config.collection_name,
                ids=[document_id],
                with_payload=True,
                with_vectors=True,
            )

            if not point:
                return None

            point_data = point[0]
            document = self._payload_to_document(point_data.payload, point_data.id)
            document.embedding = point_data.vector

            return document

        except Exception as e:
            raise VectorStoreError(
                f"Failed to retrieve document from Qdrant: {e}"
            ) from e

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID."""
        await self._ensure_initialized()

        try:
            await self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=rest.PointIdsList(
                    points=[document_id],
                ),
            )
            return True

        except Exception as e:
            self.logger.warning(f"Failed to delete document {document_id}: {e}")
            return False

    async def update_document(self, document_id: str, document: Document) -> bool:
        """Update an existing document."""
        await self._ensure_initialized()

        try:
            # Check if document exists
            existing = await self.get_document(document_id)
            if not existing:
                return False

            # Update document
            point = rest.PointStruct(
                id=document_id,
                vector=document.embedding,
                payload=self._document_to_payload(document),
            )

            await self.client.upsert(
                collection_name=self.config.collection_name,
                points=[point],
            )

            return True

        except Exception as e:
            raise VectorStoreError(f"Failed to update document in Qdrant: {e}") from e

    async def list_documents(
        self,
        limit: int | None = None,
        offset: int | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[Document]:
        """List documents in the store."""
        await self._ensure_initialized()

        try:
            # Build filter
            search_filter = None
            if filter_metadata:
                search_filter = self._build_search_filter(filter_metadata)

            # Get all points
            points = await self.client.scroll(
                collection_name=self.config.collection_name,
                limit=limit,
                offset=offset,
                scroll_filter=search_filter,
                with_payload=True,
                with_vectors=False,
            )

            # Convert to documents
            documents = []
            for point in points[0]:  # scroll returns (points, next_page_offset)
                document = self._payload_to_document(point.payload, point.id)
                documents.append(document)

            return documents

        except Exception as e:
            raise VectorStoreError(f"Failed to list documents from Qdrant: {e}") from e

    async def count_documents(self) -> int:
        """Get the total number of documents in the store."""
        await self._ensure_initialized()

        try:
            collection_info = await self.client.get_collection(
                collection_name=self.config.collection_name,
            )
            return collection_info.points_count

        except Exception as e:
            raise VectorStoreError(f"Failed to count documents in Qdrant: {e}") from e

    async def clear(self) -> None:
        """Clear all documents from the store."""
        await self._ensure_initialized()

        try:
            await self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=rest.FilterSelector(
                    filter=rest.Filter(
                        must=[],
                    ),
                ),
            )

        except Exception as e:
            raise VectorStoreError(f"Failed to clear Qdrant collection: {e}") from e

    async def health_check(self) -> bool:
        """Perform a health check on the Qdrant store."""
        try:
            await self._ensure_initialized()
            # Try to get collection info
            await self.client.get_collection(
                collection_name=self.config.collection_name,
            )
            return True
        except Exception as e:
            self.logger.warning(f"Qdrant health check failed: {e}")
            return False

    async def _ensure_initialized(self) -> None:
        """Ensure the store is initialized."""
        if not self._initialized:
            await self.initialize()

    def _document_to_payload(self, document: Document) -> dict[str, Any]:
        """Convert document to Qdrant payload."""
        payload = {
            "content": document.content,
            "metadata": document.metadata.dict(),
        }
        return payload

    def _payload_to_document(self, payload: dict[str, Any], point_id: str) -> Document:
        """Convert Qdrant payload to document."""
        content = payload.get("content", "")
        metadata_dict = payload.get("metadata", {})

        metadata = Metadata(**metadata_dict)
        metadata.id = point_id

        return Document(
            id=point_id,
            content=content,
            metadata=metadata,
        )

    def _build_search_filter(self, filter_metadata: dict[str, Any]) -> rest.Filter:
        """Build Qdrant search filter from metadata."""
        conditions = []

        for key, value in filter_metadata.items():
            if isinstance(value, str | int | float | bool):
                conditions.append(
                    rest.FieldCondition(
                        key=f"metadata.{key}",
                        match=rest.MatchValue(value=value),
                    )
                )
            elif isinstance(value, list):
                conditions.append(
                    rest.FieldCondition(
                        key=f"metadata.{key}",
                        match=rest.MatchAny(any=value),
                    )
                )

        return rest.Filter(must=conditions)
