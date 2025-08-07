"""
Caching utilities for OPSVI Foundation.

Provides comprehensive caching functionality with multiple backends.
"""

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, TypeVar

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Exception raised when cache operations fail."""


class CacheKeyError(CacheError):
    """Exception raised when cache key operations fail."""


class CacheValueError(CacheError):
    """Exception raised when cache value operations fail."""


T = TypeVar("T")


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in cache."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all values from cache."""

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern."""


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""

    def __init__(self, max_size: int = 1000) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_size = max_size
        self._access_order: list[str] = []

    async def get(self, key: str) -> Any | None:
        """Get a value from memory cache."""
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]

        # Check if expired
        if cache_entry.get("expires_at") and datetime.now() > cache_entry["expires_at"]:
            await self.delete(key)
            return None

        # Update access order (LRU)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return cache_entry["value"]

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in memory cache."""
        try:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_lru()

            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)

            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now(),
            }

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        try:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory cache."""
        if key not in self._cache:
            return False

        # Check if expired
        cache_entry = self._cache[key]
        if cache_entry.get("expires_at") and datetime.now() > cache_entry["expires_at"]:
            await self.delete(key)
            return False

        return True

    async def clear(self) -> bool:
        """Clear all values from memory cache."""
        try:
            self._cache.clear()
            self._access_order.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern (simplified implementation)."""
        try:
            # Simple pattern matching
            if pattern == "*":
                return list(self._cache.keys())

            # Basic wildcard matching
            import fnmatch

            return [key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []

    async def _evict_lru(self) -> None:
        """Evict least recently used items."""
        while len(self._cache) >= self._max_size and self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]


class RedisCacheBackend(CacheBackend):
    """Redis cache backend."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        connection_pool_size: int = 10,
    ) -> None:
        self.redis_url = redis_url
        self.connection_pool_size = connection_pool_size
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                max_connections=self.connection_pool_size,
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get a value from Redis cache."""
        try:
            redis_client = await self._get_redis()
            value = await redis_client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in Redis cache."""
        try:
            redis_client = await self._get_redis()

            # Serialize value to JSON
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value)

            if ttl is not None:
                await redis_client.setex(key, ttl, value)
            else:
                await redis_client.set(key, value)

            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis cache."""
        try:
            redis_client = await self._get_redis()
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all values from Redis cache."""
        try:
            redis_client = await self._get_redis()
            await redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern from Redis cache."""
        try:
            redis_client = await self._get_redis()
            return await redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


class Cache:
    """Main cache class that uses a backend."""

    def __init__(self, backend: CacheBackend) -> None:
        self.backend = backend
        self._key_prefix = ""
        self._default_ttl: int | None = None

    def set_key_prefix(self, prefix: str) -> None:
        """Set a prefix for all cache keys."""
        self._key_prefix = prefix

    def set_default_ttl(self, ttl: int) -> None:
        """Set default TTL for cache entries."""
        self._default_ttl = ttl

    def _make_key(self, key: str) -> str:
        """Make a full cache key with prefix."""
        return f"{self._key_prefix}:{key}" if self._key_prefix else key

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        full_key = self._make_key(key)
        return await self.backend.get(full_key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set a value in cache."""
        full_key = self._make_key(key)
        ttl = ttl or self._default_ttl
        return await self.backend.set(full_key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        full_key = self._make_key(key)
        return await self.backend.delete(full_key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        full_key = self._make_key(key)
        return await self.backend.exists(full_key)

    async def clear(self) -> bool:
        """Clear all values from cache."""
        return await self.backend.clear()

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern."""
        full_pattern = self._make_key(pattern)
        keys = await self.backend.keys(full_pattern)

        # Remove prefix from returned keys
        if self._key_prefix:
            prefix_len = len(self._key_prefix) + 1  # +1 for the colon
            return [key[prefix_len:] for key in keys]
        return keys

    async def get_or_set(
        self,
        key: str,
        default_func: callable,
        ttl: int | None = None,
    ) -> Any:
        """Get a value from cache or set it using a default function."""
        value = await self.get(key)
        if value is not None:
            return value

        # Execute default function
        if asyncio.iscoroutinefunction(default_func):
            value = await default_func()
        else:
            value = default_func()

        # Cache the result
        await self.set(key, value, ttl)
        return value

    async def increment(self, key: str, amount: int = 1) -> int | None:
        """Increment a numeric value in cache."""
        current = await self.get(key)
        if current is None:
            new_value = amount
        else:
            try:
                new_value = int(current) + amount
            except (ValueError, TypeError):
                raise CacheValueError(f"Cannot increment non-numeric value: {current}")

        await self.set(key, new_value)
        return new_value

    async def decrement(self, key: str, amount: int = 1) -> int | None:
        """Decrement a numeric value in cache."""
        return await self.increment(key, -amount)


class CacheManager:
    """Manager for multiple cache instances."""

    def __init__(self) -> None:
        self._caches: dict[str, Cache] = {}
        self._default_cache: str | None = None

    def register_cache(self, name: str, cache: Cache) -> None:
        """Register a cache instance."""
        self._caches[name] = cache
        if self._default_cache is None:
            self._default_cache = name
        logger.info(f"Registered cache: {name}")

    def get_cache(self, name: str | None = None) -> Cache:
        """Get a cache instance by name."""
        cache_name = name or self._default_cache
        if cache_name is None:
            raise CacheError("No default cache registered")

        if cache_name not in self._caches:
            raise CacheError(f"Cache '{cache_name}' not found")

        return self._caches[cache_name]

    def set_default_cache(self, name: str) -> None:
        """Set the default cache."""
        if name not in self._caches:
            raise CacheError(f"Cache '{name}' not found")
        self._default_cache = name
        logger.info(f"Set default cache: {name}")

    def list_caches(self) -> list[str]:
        """List all registered cache names."""
        return list(self._caches.keys())

    async def clear_all_caches(self) -> None:
        """Clear all registered caches."""
        for cache in self._caches.values():
            await cache.clear()
        logger.info("Cleared all caches")


# Global cache manager
cache_manager = CacheManager()


# Cache decorators


def cached(
    ttl: int | None = None,
    key_prefix: str = "",
    cache_name: str | None = None,
):
    """Decorator to cache function results."""

    def decorator(func: callable) -> callable:
        async def async_wrapper(*args, **kwargs):
            cache = cache_manager.get_cache(cache_name)

            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = ":".join(key_parts)

            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await cache.set(cache_key, result, ttl)
            return result

        def sync_wrapper(*args, **kwargs):
            cache = cache_manager.get_cache(cache_name)

            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend([str(arg) for arg in args])
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])

            cache_key = ":".join(key_parts)

            # Try to get from cache
            result = asyncio.run(cache.get(cache_key))
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            asyncio.run(cache.set(cache_key, result, ttl))
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_key(key_func: callable):
    """Decorator to specify a custom cache key function."""

    def decorator(func: callable) -> callable:
        func._cache_key_func = key_func
        return func

    return decorator


# Utility functions


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    key_parts = []

    # Add positional arguments
    for arg in args:
        key_parts.append(str(arg))

    # Add keyword arguments
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")

    # Create hash for long keys
    key_string = ":".join(key_parts)
    if len(key_string) > 250:  # Redis key length limit
        return hashlib.md5(key_string.encode()).hexdigest()

    return key_string


def create_memory_cache(max_size: int = 1000) -> Cache:
    """Create a memory cache instance."""
    backend = MemoryCacheBackend(max_size=max_size)
    return Cache(backend)


def create_redis_cache(redis_url: str = "redis://localhost:6379/0") -> Cache:
    """Create a Redis cache instance."""
    backend = RedisCacheBackend(redis_url=redis_url)
    return Cache(backend)


# Convenience functions


async def get_cached(key: str, cache_name: str | None = None) -> Any | None:
    """Get a value from the default cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.get(key)


async def set_cached(
    key: str,
    value: Any,
    ttl: int | None = None,
    cache_name: str | None = None,
) -> bool:
    """Set a value in the default cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.set(key, value, ttl)


async def delete_cached(key: str, cache_name: str | None = None) -> bool:
    """Delete a value from the default cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.delete(key)


async def exists_cached(key: str, cache_name: str | None = None) -> bool:
    """Check if a key exists in the default cache."""
    cache = cache_manager.get_cache(cache_name)
    return await cache.exists(key)
