"""In-memory vector store for opsvi-rag (for dev/testing)."""
from __future__ import annotations
from typing import Any, List, Tuple
import math

class InMemoryVectorStore:
    def __init__(self) -> None:
        self._vectors: list[tuple[str, list[float], dict[str, Any]]] = []

    async def upsert(self, items: list[tuple[str, list[float], dict[str, Any]]]) -> None:
        id_to_idx = {vid: i for i, (vid, _, _) in enumerate(self._vectors)}
        for vid, vec, meta in items:
            if vid in id_to_idx:
                self._vectors[id_to_idx[vid]] = (vid, vec, meta)
            else:
                self._vectors.append((vid, vec, meta))

    async def query(self, vec: list[float], top_k: int = 5) -> list[tuple[str, float, dict[str, Any]]]:
        def cosine(a: list[float], b: list[float]) -> float:
            num = sum(x * y for x, y in zip(a, b))
            da = math.sqrt(sum(x * x for x in a))
            db = math.sqrt(sum(y * y for y in b))
            return 0.0 if da == 0 or db == 0 else num / (da * db)
        scored = [(vid, cosine(vec, v), meta) for (vid, v, meta) in self._vectors]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:top_k]
