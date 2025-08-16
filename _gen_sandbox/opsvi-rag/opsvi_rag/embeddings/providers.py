"""Embeddings providers for opsvi-rag.

This module defines an abstract async embeddings provider and a simple
in-memory provider useful for testing or small-scale usage. It supports
batched embedding, optional L2-normalization, and a simple async-aware
LRU cache to avoid recomputing identical texts.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import asyncio
import hashlib
import math

__all__ = ["EmbeddingsProvider", "InMemoryEmbeddingsProvider"]


class EmbeddingsProvider:
    """Abstract async embeddings provider.

    Implementors should override async _embed_batch to produce embeddings for
    a list of texts. The public async embed method handles batching,
    optional normalization, and caching.
    """

    def __init__(self, batch_size: int = 16, normalize: bool = True, cache_size: int = 1024):
        self.batch_size = max(1, int(batch_size))
        self.normalize = bool(normalize)
        self._cache: Dict[str, List[float]] = {}
        self._cache_order: List[str] = []
        self._cache_size = max(0, int(cache_size))
        # protect async cache access
        self._lock = asyncio.Lock()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for the provided texts.

        This method will use an internal cache and process texts in batches.
        """
        if not texts:
            return []

        result: List[Optional[List[float]]] = [None] * len(texts)
        pending_batches: List[Tuple[int, str]] = []  # (index, text)

        # First pass: try to serve from cache
        async with self._lock:
            for i, t in enumerate(texts):
                key = self._cache_key(t)
                if key in self._cache:
                    result[i] = list(self._cache[key])
                else:
                    pending_batches.append((i, t))

        # Process remaining in batches
        for start in range(0, len(pending_batches), self.batch_size):
            batch = pending_batches[start : start + self.batch_size]
            indices, batch_texts = zip(*batch)
            embeddings = await self._embed_batch(list(batch_texts))
            if self.normalize:
                embeddings = [self._l2_normalize(e) for e in embeddings]
            # store in cache and fill results
            async with self._lock:
                for idx, txt, emb in zip(indices, batch_texts, embeddings):
                    key = self._cache_key(txt)
                    if self._cache_size > 0:
                        # simple LRU: evict oldest when exceeding size
                        if key not in self._cache:
                            self._cache_order.append(key)
                        self._cache[key] = list(emb)
                        while len(self._cache_order) > self._cache_size:
                            old = self._cache_order.pop(0)
                            self._cache.pop(old, None)
                    result[idx] = list(emb)

        # At this point all entries should be filled
        return [r if r is not None else [] for r in result]

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Produce embeddings for a batch of texts.

        Subclasses must implement this coroutine to return a list of float
        vectors, one per text.
        """
        raise NotImplementedError

    def _cache_key(self, text: str) -> str:
        # stable key for caching: sha1 of text
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _l2_normalize(vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0 or math.isinf(norm) or math.isnan(norm):
            return vec
        return [x / norm for x in vec]


class InMemoryEmbeddingsProvider(EmbeddingsProvider):
    """A trivial embeddings provider that deterministically maps text to
    a fixed-size vector using hashing. Intended for tests and examples.

    The embedding dimension can be set; vectors are deterministic and
    reasonably distributed but are not semantically meaningful.
    """

    def __init__(self, dim: int = 64, **kwargs) -> None:
        super().__init__(**kwargs)
        if dim <= 0:
            raise ValueError("dim must be > 0")
        self.dim = int(dim)

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Non-blocking CPU-bound work; yield control occasionally
        out: List[List[float]] = []
        for i, t in enumerate(texts):
            out.append(self._embed_one(t))
            # yield control every 16 items
            if (i & 0xF) == 0:
                await asyncio.sleep(0)
        return out

    def _embed_one(self, text: str) -> List[float]:
        # Use SHA256 digest to produce deterministic bytes
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vals: List[float] = []
        # Expand bytes into floats, repeat digest as needed
        i = 0
        while len(vals) < self.dim:
            byte = h[i % len(h)]
            # map byte to [-1, 1]
            vals.append((byte / 255.0) * 2.0 - 1.0)
            i += 1
        return vals[: self.dim]
