"""Cache manager for opsvi-memory.

Provides an asynchronous cache manager abstraction with simple in-memory
implementation, eviction strategies, and basic metrics. The manager supports
invalidate and get/set operations and tracks hit/miss counts.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Optional


class CacheItem:
    """Internal container for cached values with metadata."""

    __slots__ = ("value", "expiry", "last_access")

    def __init__(self, value: Any, ttl: Optional[float]) -> None:
        self.value = value
        self.expiry = (time.monotonic() + ttl) if (ttl is not None and ttl > 0) else None
        self.last_access = time.monotonic()

    def is_expired(self) -> bool:
        if self.expiry is None:
            return False
        return time.monotonic() >= self.expiry


class CacheManager:
    """Asynchronous in-memory cache manager with LRU eviction and TTL.

    Usage:
        cache = CacheManager(max_size=100)
        await cache.set("k", 1, ttl=5.0)
        v = await cache.get("k")
        v = await cache.get_or_set("k", factory=lambda: 2, ttl=10)
        await cache.invalidate("k")
    """

    def __init__(self, max_size: int = 1024) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be a positive integer")
        self._max_size = max_size
        self._store: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions_lru = 0
        self._expirations = 0
        self._invalidations = 0
        self._inflight: Dict[str, asyncio.Future] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache or None if missing/expired."""
        async with self._lock:
            item = self._store.get(key)
            if item is None:
                self._misses += 1
                return None
            if item.is_expired():
                del self._store[key]
                self._misses += 1
                self._expirations += 1
                return None
            item.last_access = time.monotonic()
            self._hits += 1
            return item.value

    async def peek(self, key: str) -> Optional[Any]:
        """Get value without updating LRU timestamp. None if missing/expired."""
        async with self._lock:
            item = self._store.get(key)
            if item is None or item.is_expired():
                if item is not None and item.is_expired():
                    del self._store[key]
                    self._expirations += 1
                return None
            return item.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set a value with optional TTL seconds. Evicts LRU on capacity."""
        async with self._lock:
            if key in self._store:
                self._store[key] = CacheItem(value, ttl)
                return
            await self._ensure_capacity_locked()
            self._store[key] = CacheItem(value, ttl)

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any | Awaitable[Any]],
        ttl: Optional[float] = None,
    ) -> Any:
        """Return cached value or compute, store, and return it.

        Ensures only one concurrent factory runs per key; others await it.
        """
        # Fast path using regular get; ambiguity for None handled below.
        val = await self.get(key)
        if val is not None:
            return val
        # If value might legitimately be None, disambiguate under lock.
        async with self._lock:
            item = self._store.get(key)
            if item is not None and not item.is_expired():
                item.last_access = time.monotonic()
                self._hits += 1
                return item.value

            fut = self._inflight.get(key)
            if fut is None:
                loop = asyncio.get_running_loop()
                fut = loop.create_future()
                self._inflight[key] = fut

                async def runner() -> None:
                    try:
                        res = factory()
                        if asyncio.iscoroutine(res):
                            result = await res  # type: ignore[assignment]
                        else:
                            result = res
                        async with self._lock:
                            if key in self._store:
                                self._store[key] = CacheItem(result, ttl)
                            else:
                                await self._ensure_capacity_locked()
                                self._store[key] = CacheItem(result, ttl)
                        fut.set_result(result)
                    except Exception as exc:  # pragma: no cover - propagate
                        fut.set_exception(exc)
                    finally:
                        async with self._lock:
                            self._inflight.pop(key, None)

                asyncio.create_task(runner())
        return await fut  # type: ignore[has-type]

    async def invalidate(self, key: str) -> None:
        """Remove a specific key if present."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                self._invalidations += 1

    async def clear(self) -> None:
        """Clear the entire cache and count invalidations."""
        async with self._lock:
            removed = len(self._store)
            self._store.clear()
            self._invalidations += removed

    async def prune_expired(self) -> int:
        """Remove all expired items and return count removed."""
        async with self._lock:
            to_remove = [k for k, v in self._store.items() if v.is_expired()]
            for k in to_remove:
                self._store.pop(k, None)
            self._expirations += len(to_remove)
            return len(to_remove)

    async def metrics(self) -> Dict[str, Any]:
        """Return basic metrics and current size limits."""
        async with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "current_size": len(self._store),
                "max_size": self._max_size,
                "evictions_lru": self._evictions_lru,
                "expirations": self._expirations,
                "invalidations": self._invalidations,
                "inflight": len(self._inflight),
            }

    async def _ensure_capacity_locked(self) -> None:
        """Evict items until size is below max_size. Requires lock held."""
        while len(self._store) >= self._max_size:
            lru_key: Optional[str] = None
            lru_time = float("inf")
            # Prefer removing expired entries first
            for k, item in self._store.items():
                if item.is_expired():
                    lru_key = k
                    break
                if item.last_access < lru_time:
                    lru_time = item.last_access
                    lru_key = k
            if lru_key is None:
                break
            item = self._store.pop(lru_key, None)
            if item is None:
                continue
            if item.is_expired():
                self._expirations += 1
            else:
                self._evictions_lru += 1

    # convenience synchronous-compatible helpers
    def size(self) -> int:
        """Return current number of items in cache (approximate)."""
        return len(self._store)


# Module-level default cache
_default_cache: Optional[CacheManager] = None


def get_default_cache(max_size: int = 1024) -> CacheManager:
    """Get or create a module-level default CacheManager."""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheManager(max_size=max_size)
    return _default_cache
