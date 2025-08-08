"""Vector datastore base for opsvi-rag."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Protocol, runtime_checkable
import asyncio

from opsvi_rag.core.base import OpsviRagManager


@runtime_checkable
class VectorRecord(Protocol):
    """Protocol describing a record accepted by vector stores.

    Minimal required fields are id (str), vector (List[float]) and optional metadata.
    """

    id: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]]


class VectorStore(OpsviRagManager):
    """Abstract base for vector datastores.

    Subclasses should implement the underlying storage and retrieval logic by
    overriding the protected methods prefixed with _.
    """

    async def upsert(self, vectors: List[Dict[str, Any]]) -> None:
        """Insert or update a batch of vector records.

        Each record should include at minimum: 'id' (str) and 'vector' (List[float]).
        Optional 'metadata' may be provided.
        """
        if not vectors:
            return
        await self._upsert(vectors)

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return up to top_k nearest records to the provided vector.

        'filters' is an optional dictionary used to filter candidates by metadata.
        """
        if top_k <= 0:
            return []
        return await self._query(vector=vector, top_k=top_k, filters=filters)

    async def delete(self, ids: Iterable[str]) -> None:
        """Delete records by id.

        If a requested id does not exist, implementations should silently ignore it.
        """
        ids_list = list(ids)
        if not ids_list:
            return
        await self._delete(ids_list)

    async def count(self) -> int:
        """Return approximate or exact number of vectors stored."""
        return await self._count()

    # Protected methods to be implemented by concrete subclasses.

    async def _upsert(self, vectors: List[Dict[str, Any]]) -> None:
        """Persist a batch of vectors. Override in subclass."""
        raise NotImplementedError

    async def _query(
        self, vector: List[float], top_k: int, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform similarity search. Override in subclass.

        Should return a list of records with at least 'id', 'score', 'vector', and
        optional 'metadata'. 'score' should be a lower-is-better or higher-is-better
        value defined by the implementation (document in subclass).
        """
        raise NotImplementedError

    async def _delete(self, ids: List[str]) -> None:
        """Remove records by id. Override in subclass."""
        raise NotImplementedError

    async def _count(self) -> int:
        """Return number of records. Override in subclass."""
        raise NotImplementedError

    # Utility: simple in-memory fallback for tests or development.
    @classmethod
    def in_memory(cls) -> "_InMemoryVectorStore":
        """Return a simple in-memory implementation of VectorStore."""

        class _InMemoryVectorStore(VectorStore):
            def __init__(self) -> None:
                self._store: Dict[str, Dict[str, Any]] = {}
                self._lock = asyncio.Lock()

            async def _upsert(self, vectors: List[Dict[str, Any]]) -> None:
                async with self._lock:
                    for rec in vectors:
                        rid = rec["id"]
                        self._store[rid] = {
                            "id": rid,
                            "vector": rec["vector"],
                            "metadata": rec.get("metadata"),
                        }

            async def _query(
                self, vector: List[float], top_k: int, filters: Optional[Dict[str, Any]]
            ) -> List[Dict[str, Any]]:
                # naive linear scan using cosine similarity
                import math

                def dot(a: List[float], b: List[float]) -> float:
                    return sum(x * y for x, y in zip(a, b))

                def norm(a: List[float]) -> float:
                    return math.sqrt(sum(x * x for x in a))

                async with self._lock:
                    candidates = list(self._store.values())

                if filters:
                    def match(m: Optional[Dict[str, Any]]) -> bool:
                        if not m:
                            return False
                        for k, v in filters.items():
                            if m.get(k) != v:
                                return False
                        return True

                    candidates = [c for c in candidates if match(c.get("metadata"))]

                scores: List[Dict[str, Any]] = []
                qnorm = norm(vector) or 1.0
                for c in candidates:
                    vec = c["vector"]
                    if len(vec) != len(vector):
                        continue
                    score = dot(vector, vec) / (qnorm * (norm(vec) or 1.0))
                    scores.append({"id": c["id"], "score": score, "vector": vec, "metadata": c.get("metadata")})

                # sort by descending cosine similarity
                scores.sort(key=lambda x: x["score"], reverse=True)
                return scores[:top_k]

            async def _delete(self, ids: List[str]) -> None:
                async with self._lock:
                    for _id in ids:
                        self._store.pop(_id, None)

            async def _count(self) -> int:
                async with self._lock:
                    return len(self._store)

        return _InMemoryVectorStore()
