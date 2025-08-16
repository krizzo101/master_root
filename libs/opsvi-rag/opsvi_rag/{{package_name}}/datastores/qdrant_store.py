"""
Qdrant vector store provider for OPSVI RAG system.

This module provides integration with Qdrant vector database for storing
and retrieving embeddings with similarity search capabilities.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4

import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from opsvi_foundation import BaseComponent, ComponentError
from opsvi_foundation.config import BaseSettings, Field

logger = logging.getLogger(__name__)


class QdrantConfig(BaseSettings):
    """Configuration for Qdrant vector store."""

    host: str = Field(default="localhost", description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant port")
    api_key: Optional[str] = Field(default=None, description="Qdrant API key")
    collection_name: str = Field(
        default="opsvi_research", description="Default collection name"
    )
    vector_size: int = Field(default=1536, description="Vector dimension size")
    distance: str = Field(
        default="Cosine", description="Distance metric (Cosine, Dot, Euclidean)"
    )

    class Config:
        env_prefix = "OPSVI_QDRANT_"


class QdrantStore(BaseComponent):
    """Qdrant vector store provider for OPSVI RAG system."""

    def __init__(self, config: QdrantConfig, **kwargs):
        """Initialize Qdrant store."""
        super().__init__(name="qdrant-store", **kwargs)
        self.config = config
        self.client: Optional[QdrantClient] = None
        self._lock = asyncio.Lock()

    async def _initialize_impl(self) -> None:
        """Initialize Qdrant client."""
        try:
            # Create Qdrant client
            if self.config.api_key:
                self.client = qdrant_client.QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                    api_key=self.config.api_key,
                )
            else:
                self.client = qdrant_client.QdrantClient(
                    host=self.config.host,
                    port=self.config.port,
                )

            # Ensure collection exists
            await self._ensure_collection_exists()

            logger.info(
                f"Qdrant store initialized successfully on {self.config.host}:{self.config.port}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant store: {e}")
            raise ComponentError(f"Qdrant initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown Qdrant client."""
        if self.client:
            self.client.close()
            logger.info("Qdrant store shut down successfully")

    async def _health_check_impl(self) -> bool:
        """Check Qdrant health."""
        try:
            if not self.client:
                return False

            # Simple health check - try to get collections
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def _ensure_collection_exists(self) -> None:
        """Ensure the default collection exists."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.config.collection_name not in collection_names:
                # Create collection
                distance_map = {
                    "Cosine": Distance.COSINE,
                    "Dot": Distance.DOT,
                    "Euclidean": Distance.EUCLID,
                }

                distance = distance_map.get(self.config.distance, Distance.COSINE)

                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_size, distance=distance
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.config.collection_name}")
            else:
                logger.info(
                    f"Qdrant collection already exists: {self.config.collection_name}"
                )

        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise ComponentError(f"Collection creation failed: {e}") from e

    async def store_embeddings(
        self,
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
        collection_name: Optional[str] = None,
    ) -> List[str]:
        """
        Store embeddings with metadata in Qdrant.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            collection_name: Collection name (uses default if None)

        Returns:
            List of point IDs
        """
        async with self._lock:
            try:
                collection = collection_name or self.config.collection_name
                point_ids = []

                for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
                    point_id = str(uuid4())
                    point_ids.append(point_id)

                    # Create point structure
                    point = PointStruct(id=point_id, vector=embedding, payload=meta)

                    # Insert point
                    self.client.upsert(collection_name=collection, points=[point])

                logger.info(
                    f"Stored {len(embeddings)} embeddings in collection '{collection}'"
                )
                return point_ids

            except Exception as e:
                logger.error(f"Failed to store embeddings: {e}")
                raise ComponentError(f"Embedding storage failed: {e}") from e

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        collection_name: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            collection_name: Collection name (uses default if None)
            filter_conditions: Optional filter conditions

        Returns:
            List of similar documents with scores
        """
        async with self._lock:
            try:
                collection = collection_name or self.config.collection_name

                # Build search request
                search_params = {
                    "collection_name": collection,
                    "query_vector": query_embedding,
                    "limit": limit,
                    "score_threshold": score_threshold,
                }

                if filter_conditions:
                    search_params["query_filter"] = self._build_filter(
                        filter_conditions
                    )

                # Perform search
                results = self.client.search(**search_params)

                # Format results
                formatted_results = []
                for result in results:
                    formatted_results.append(
                        {
                            "id": result.id,
                            "score": result.score,
                            "metadata": result.payload,
                        }
                    )

                logger.info(f"Found {len(formatted_results)} similar documents")
                return formatted_results

            except Exception as e:
                logger.error(f"Failed to search similar embeddings: {e}")
                raise ComponentError(f"Similarity search failed: {e}") from e

    async def delete_points(
        self, point_ids: List[str], collection_name: Optional[str] = None
    ) -> None:
        """
        Delete points by IDs.

        Args:
            point_ids: List of point IDs to delete
            collection_name: Collection name (uses default if None)
        """
        async with self._lock:
            try:
                collection = collection_name or self.config.collection_name

                self.client.delete(
                    collection_name=collection,
                    points_selector=models.PointIdsList(points=point_ids),
                )

                logger.info(
                    f"Deleted {len(point_ids)} points from collection '{collection}'"
                )

            except Exception as e:
                logger.error(f"Failed to delete points: {e}")
                raise ComponentError(f"Point deletion failed: {e}") from e

    async def get_collection_info(
        self, collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get collection information.

        Args:
            collection_name: Collection name (uses default if None)

        Returns:
            Collection information dictionary
        """
        try:
            collection = collection_name or self.config.collection_name

            info = self.client.get_collection(collection)

            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": str(info.config.params.vectors.distance),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise ComponentError(f"Collection info retrieval failed: {e}") from e

    def _build_filter(self, conditions: Dict[str, Any]) -> models.Filter:
        """Build Qdrant filter from conditions."""
        must_conditions = []

        for key, value in conditions.items():
            if isinstance(value, (str, int, float, bool)):
                must_conditions.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )
            elif isinstance(value, list):
                must_conditions.append(
                    models.FieldCondition(key=key, match=models.MatchAny(any=value))
                )

        return models.Filter(must=must_conditions)

    async def get_stats(self) -> Dict[str, Any]:
        """Get Qdrant store statistics."""
        try:
            collections = self.client.get_collections()
            total_points = 0

            for collection in collections.collections:
                info = self.client.get_collection(collection.name)
                total_points += info.points_count

            return {
                "collections_count": len(collections.collections),
                "total_points": total_points,
                "host": self.config.host,
                "port": self.config.port,
                "status": "healthy" if await self.health_check() else "unhealthy",
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e), "status": "error"}
