"""
In-memory cache implementation.

Provides a simple in-memory cache with TTL support.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

from opsvi_foundation import get_logger

from .base import CacheBackend

logger = get_logger(__name__)


class InMemoryCache(CacheBackend):
    """Simple TTL-based LRU cache."""

    def __init__(self, *, max_size: int = 1024) -> None:
        super().__init__()
        self._data: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        if key not in self._data:
            return None
        value, expiry = self._data[key]
        if expiry < time.time():
            # Key expired – remove and return None
            self._data.pop(key, None)
            return None
        self._data.move_to_end(key)  # LRU bump
        return value

    async def set(self, key: str, value: Any, *, ttl: int = 60) -> None:
        """Set a value in cache with TTL."""
        if value is None:
            self._data.pop(key, None)
            return
        while len(self._data) >= self._max_size:
            self._data.popitem(last=False)  # evict oldest
        self._data[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._data:
            self._data.pop(key)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if key not in self._data:
            return False
        value, expiry = self._data[key]
        if expiry < time.time():
            # Key expired – remove and return False
            self._data.pop(key, None)
            return False
        return True

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._data.clear()
        logger.info("In-memory cache cleared")
