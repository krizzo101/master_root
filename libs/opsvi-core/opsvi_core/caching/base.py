"""
Base caching infrastructure for OPSVI Core.

Provides cache backend interface and common caching utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from opsvi_foundation import BaseComponent, ComponentError, get_logger

logger = get_logger(__name__)


class CacheError(ComponentError):
    """Raised when cache operations fail."""

    pass


class CacheBackend(BaseComponent, ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl: int = 60) -> None:
        """Set a value in cache with TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass


class CacheManager(BaseComponent):
    """Cache manager with multiple backend support."""

    def __init__(self, default_backend: CacheBackend):
        super().__init__()
        self.default_backend = default_backend
        self._backends: dict[str, CacheBackend] = {"default": default_backend}

    def add_backend(self, name: str, backend: CacheBackend) -> None:
        """Add a cache backend."""
        self._backends[name] = backend
        logger.info("Added cache backend: %s", name)

    def get_backend(self, name: str = "default") -> CacheBackend:
        """Get a cache backend by name."""
        return self._backends.get(name, self.default_backend)

    async def get(self, key: str, backend: str = "default") -> Optional[Any]:
        """Get a value from cache."""
        cache = self.get_backend(backend)
        return await cache.get(key)

    async def set(self, key: str, value: Any, *, ttl: int = 60, backend: str = "default") -> None:
        """Set a value in cache."""
        cache = self.get_backend(backend)
        await cache.set(key, value, ttl=ttl)

    async def delete(self, key: str, backend: str = "default") -> bool:
        """Delete a key from cache."""
        cache = self.get_backend(backend)
        return await cache.delete(key)

    async def exists(self, key: str, backend: str = "default") -> bool:
        """Check if a key exists in cache."""
        cache = self.get_backend(backend)
        return await cache.exists(key)

    async def clear(self, backend: str = "default") -> None:
        """Clear cache."""
        cache = self.get_backend(backend)
        await cache.clear()
