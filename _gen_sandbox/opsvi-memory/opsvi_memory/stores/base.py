"""Memory store base for opsvi-memory.

Provides an asynchronous abstract base class for simple key-value memory
stores with optional TTL support. Concrete stores should override methods
as needed. This module intentionally keeps a small, dependency-free API
suitable for in-memory or distributed implementations.
"""
from __future__ import annotations

import abc
import asyncio
import time
from typing import Any, Dict, Optional, Tuple


class MemoryStore(abc.ABC):
    """Asynchronous base class for a key-value memory store.

    Methods are coroutine-friendly to allow implementations that perform
    I/O or coordination. The default implementations provide an
    in-memory dict-based behavior suitable for testing and simple uses.
    """

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Return the value for key, or None if missing or expired."""

    @abc.abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set the value for key. If ttl is provided, it is the number of
        seconds until the key expires.
        """

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key. Return True if key was present, False otherwise."""

    @abc.abstractmethod
    async def ttl(self, key: str) -> Optional[float]:
        """Return remaining TTL in seconds, or None if no TTL or key missing."""


class InMemoryStore(MemoryStore):
    """Simple asyncio-friendly in-memory store implementing MemoryStore.

    Stores values in a dict with optional expiry times. All operations are
    protected by an asyncio.Lock to be safe when used concurrently.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._expires: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def _purge_if_expired(self, key: str) -> None:
        exp = self._expires.get(key)
        if exp is None:
            return
        if time.time() >= exp:
            # expired — remove
            self._data.pop(key, None)
            self._expires.pop(key, None)

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            await self._purge_if_expired(key)
            return self._data.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        async with self._lock:
            self._data[key] = value
            if ttl is None:
                self._expires.pop(key, None)
            else:
                if ttl <= 0:
                    # immediate expiry: ensure key is not stored
                    self._data.pop(key, None)
                    self._expires.pop(key, None)
                else:
                    self._expires[key] = time.time() + float(ttl)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            await self._purge_if_expired(key)
            existed = key in self._data
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return existed

    async def ttl(self, key: str) -> Optional[float]:
        async with self._lock:
            await self._purge_if_expired(key)
            exp = self._expires.get(key)
            if exp is None:
                return None
            remaining = exp - time.time()
            return remaining if remaining > 0 else None


# Provide a simple factory function for convenience
def create_inmemory_store() -> MemoryStore:
    """Create a new InMemoryStore instance."""
    return InMemoryStore()
