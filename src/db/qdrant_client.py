# mypy: ignore-errors
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    CollectionInfo,
    CollectionStatus,
    Distance,
    PointStruct,
    VectorParams,
)

from src.utils.config import get_settings

CHUNK_COLLECTION = "chunks"


class QdrantWrapper:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            check_compatibility=False,
        )

    async def ensure_collections(self, dim: int = 3072) -> None:
        existing: CollectionInfo | None = None
        try:
            existing = await self.client.get_collection(CHUNK_COLLECTION)
        except Exception:
            pass
        if not existing or existing.status != CollectionStatus.GREEN:
            await self.client.recreate_collection(
                collection_name=CHUNK_COLLECTION,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    async def upsert_chunks(
        self, embeddings: list[list[float]], payloads: list[dict[str, Any]]
    ):
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=vec, payload=payload)
            for vec, payload in zip(embeddings, payloads, strict=False)
        ]
        await self.client.upsert(collection_name=CHUNK_COLLECTION, points=points)

    async def search(self, query_vec: list[float], limit: int = 10):
        res = await self.client.search(
            collection_name=CHUNK_COLLECTION, query_vector=query_vec, limit=limit
        )
        return res
