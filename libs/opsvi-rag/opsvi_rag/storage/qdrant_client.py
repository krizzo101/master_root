"""
Qdrant vector database client for OPSVI RAG Library.

Provides async interface for Qdrant vector database operations.
"""

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Filter as QdrantFilter
from qdrant_client.http.models import VectorParams
from qdrant_client.models import PointStruct, ScoredPoint

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """
    Async wrapper around Qdrant vector database interactions.

    Handles collection management, embedding storage, and search operations
    with comprehensive error handling and logging.
    """

    def __init__(
        self,
        url: str,
        collection_name: str,
        api_key: str | None = None,
        vector_size: int = 768,
        distance: str = "Cosine",
    ):
        """
        Initialize Qdrant vector store.

        Args:
            url: Qdrant server URL
            collection_name: Name of the collection
            api_key: Optional API key for authentication
            vector_size: Dimension of vectors
            distance: Distance metric (Cosine, Dot, Euclidean)
        """
        self.url = url
        self.collection_name = collection_name
        self.api_key = api_key
        self.vector_size = vector_size
        self.distance = distance

        # Initialize async client
        self.client = AsyncQdrantClient(url=url, api_key=api_key)

        logger.info("QdrantVectorStore initialized for collection: %s", collection_name)

    async def ensure_collection(self) -> None:
        """Ensure collection exists, create if missing."""
        try:
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                await self.create_collection()
                logger.info("Created collection: %s", self.collection_name)
            else:
                logger.info("Collection already exists: %s", self.collection_name)

        except Exception as e:
            logger.exception("Error ensuring collection: %s", e)
            raise

    async def create_collection(self) -> None:
        """Create collection with specified parameters."""
        try:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=self.distance
                ),
            )
        except Exception as e:
            logger.exception("Error creating collection: %s", e)
            raise

    async def upsert_points(self, points: list[PointStruct]) -> None:
        """Upsert points into the collection."""
        try:
            await self.client.upsert(
                collection_name=self.collection_name, points=points
            )
            logger.info("Upserted %d points", len(points))
        except Exception as e:
            logger.exception("Error upserting points: %s", e)
            raise

    async def search(
        self,
        vector: list[float],
        limit: int = 5,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[ScoredPoint]:
        """Perform vector similarity search."""
        try:
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit,
                filter=QdrantFilter(**filter_payload) if filter_payload else None,
            )
            logger.info("Search returned %d results", len(results))
            return results
        except Exception as e:
            logger.exception("Error during search: %s", e)
            raise

    async def delete_points(self, point_ids: list[str]) -> None:
        """Delete points by IDs."""
        try:
            await self.client.delete(
                collection_name=self.collection_name, points_selector=point_ids
            )
            logger.info("Deleted %d points", len(point_ids))
        except Exception as e:
            logger.exception("Error deleting points: %s", e)
            raise

    async def get_collection_info(self) -> dict[str, Any]:
        """Get collection information."""
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.exception("Error getting collection info: %s", e)
            raise
