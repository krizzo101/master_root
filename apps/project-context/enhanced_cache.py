#!/usr/bin/env python3
"""
Enhanced caching implementation with Redis support for project-context system.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import redis.asyncio as redis
import structlog
from aiocache import Cache, cached, caches
from aiocache.serializers import JsonSerializer, PickleSerializer

logger = structlog.get_logger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class EnhancedCacheManager:
    """Enhanced cache manager with Redis support and intelligent invalidation."""

    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 1,  # Use different DB than Context Bridge
        default_ttl: int = 300,  # 5 minutes
        file_data_ttl: int = 60,  # 1 minute for file data
        project_stats_ttl: int = 300,  # 5 minutes for project stats
        query_result_ttl: int = 120,  # 2 minutes for query results
        cache_namespace: str = "project_context",
        enable_redis: bool = True,
    ):
        """Initialize enhanced cache manager.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number
            default_ttl: Default TTL for cache entries in seconds
            file_data_ttl: TTL for file data cache entries
            project_stats_ttl: TTL for project stats cache entries
            query_result_ttl: TTL for database query results
            cache_namespace: Namespace for cache keys
            enable_redis: Whether to use Redis (falls back to memory cache)
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.default_ttl = default_ttl
        self.file_data_ttl = file_data_ttl
        self.project_stats_ttl = project_stats_ttl
        self.query_result_ttl = query_result_ttl
        self.cache_namespace = cache_namespace
        self.enable_redis = enable_redis

        # Redis client
        self.redis_client: Optional[redis.Redis] = None
        self.redis_connected = False

        # Fallback to memory cache
        self.memory_cache = {}
        self.cache_timestamps = {}

        # Track file modification times for invalidation
        self._file_mtimes: Dict[str, float] = {}

        # Performance metrics
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "invalidations": 0,
        }

        logger.info(
            "Enhanced cache manager initialized",
            redis_enabled=enable_redis,
            default_ttl=default_ttl,
            file_ttl=file_data_ttl,
            stats_ttl=project_stats_ttl,
        )

    async def initialize(self):
        """Initialize cache connections."""
        if self.enable_redis:
            try:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

                # Test connection
                await self.redis_client.ping()
                self.redis_connected = True
                logger.info(
                    "Redis cache connected",
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                )

            except Exception as e:
                logger.warning(
                    "Failed to connect to Redis, using memory cache", error=str(e)
                )
                self.redis_connected = False
                self.redis_client = None
        else:
            logger.info("Redis disabled, using memory cache only")

    def _get_cache_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Generate a namespaced cache key."""
        ns = namespace or self.cache_namespace
        return f"{ns}:{key}"

    def _hash_key(self, data: Any) -> str:
        """Create a hash of the data for consistent caching."""
        key_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(self, key: str, namespace: Optional[str] = None) -> Any:
        """Get a value from cache."""
        cache_key = self._get_cache_key(key, namespace)

        try:
            if self.redis_connected and self.redis_client:
                # Try Redis first
                result = await self.redis_client.get(cache_key)
                if result is not None:
                    self.cache_stats["hits"] += 1
                    logger.debug("Redis cache hit", key=cache_key)
                    return json.loads(result)

            # Fallback to memory cache
            if cache_key in self.memory_cache:
                cached_data, timestamp = self.memory_cache[cache_key]

                # Check if expired
                if time.time() - timestamp < self.default_ttl:
                    self.cache_stats["hits"] += 1
                    logger.debug("Memory cache hit", key=cache_key)
                    return cached_data
                else:
                    # Expired, remove
                    del self.memory_cache[cache_key]

            # Cache miss
            self.cache_stats["misses"] += 1
            logger.debug("Cache miss", key=cache_key)
            return None

        except Exception as e:
            logger.warning("Cache get error", key=cache_key, error=str(e))
            self.cache_stats["misses"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
    ) -> bool:
        """Set a value in cache."""
        cache_key = self._get_cache_key(key, namespace)
        cache_ttl = ttl or self.default_ttl

        try:
            if self.redis_connected and self.redis_client:
                # Set in Redis
                serialized = json.dumps(value, default=str)
                await self.redis_client.setex(cache_key, cache_ttl, serialized)

            # Also set in memory cache as backup
            self.memory_cache[cache_key] = (value, time.time())

            self.cache_stats["sets"] += 1
            logger.debug("Cache set", key=cache_key, ttl=cache_ttl)
            return True

        except Exception as e:
            logger.warning("Cache set error", key=cache_key, error=str(e))
            return False

    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete a value from cache."""
        cache_key = self._get_cache_key(key, namespace)

        try:
            deleted = False

            if self.redis_connected and self.redis_client:
                result = await self.redis_client.delete(cache_key)
                deleted = result > 0

            # Also delete from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                deleted = True

            if deleted:
                self.cache_stats["deletes"] += 1
                logger.debug("Cache delete", key=cache_key)

            return deleted

        except Exception as e:
            logger.warning("Cache delete error", key=cache_key, error=str(e))
            return False

    async def invalidate_pattern(
        self, pattern: str, namespace: Optional[str] = None
    ) -> int:
        """Invalidate cache entries matching a pattern."""
        full_pattern = self._get_cache_key(pattern, namespace)

        try:
            invalidated = 0

            if self.redis_connected and self.redis_client:
                # Get keys matching pattern
                keys = []
                async for key in self.redis_client.scan_iter(match=full_pattern):
                    keys.append(key)

                if keys:
                    invalidated = await self.redis_client.delete(*keys)

            # Also invalidate memory cache
            memory_keys_to_delete = [
                k
                for k in self.memory_cache.keys()
                if self._matches_pattern(k, full_pattern)
            ]

            for key in memory_keys_to_delete:
                del self.memory_cache[key]
                invalidated += 1

            self.cache_stats["invalidations"] += invalidated
            logger.info("Pattern invalidation", pattern=full_pattern, count=invalidated)
            return invalidated

        except Exception as e:
            logger.warning(
                "Pattern invalidation error", pattern=full_pattern, error=str(e)
            )
            return 0

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if a key matches a pattern (simple wildcard matching)."""
        # Convert glob-style pattern to simple matching
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                return key.startswith(parts[0]) and key.endswith(parts[1])
        return key == pattern

    async def get_file_data(self, file_path: str) -> Any:
        """Get file data from cache with file modification checking."""
        cache_key = self._get_cache_key(f"file:{file_path}")

        try:
            # Check if file has been modified
            if await self._is_file_modified(file_path):
                await self.delete(cache_key)
                return None

            result = await self.get(cache_key)
            return result

        except Exception as e:
            logger.warning("File cache get error", file_path=file_path, error=str(e))
            return None

    async def set_file_data(self, file_path: str, value: Any) -> bool:
        """Set file data in cache with modification time tracking."""
        cache_key = self._get_cache_key(f"file:{file_path}")

        try:
            success = await self.set(cache_key, value, self.file_data_ttl)
            if success:
                # Track file modification time
                await self._update_file_mtime(file_path)
            return success

        except Exception as e:
            logger.warning("File cache set error", file_path=file_path, error=str(e))
            return False

    async def set_query_result(self, query_hash: str, result: Any) -> bool:
        """Cache database query results."""
        cache_key = self._get_cache_key(f"query:{query_hash}")
        return await self.set(cache_key, result, self.query_result_ttl)

    async def get_query_result(self, query_hash: str) -> Any:
        """Get cached database query results."""
        cache_key = self._get_cache_key(f"query:{query_hash}")
        return await self.get(cache_key)

    async def invalidate_file_pattern(self, file_pattern: str) -> int:
        """Invalidate all cache entries related to files matching pattern."""
        pattern = self._get_cache_key(f"file:*{file_pattern}*")
        return await self.invalidate_pattern(pattern)

    async def invalidate_project_data(self) -> int:
        """Invalidate all project-level cached data."""
        patterns = [
            self._get_cache_key("stats:*"),
            self._get_cache_key("project:*"),
            self._get_cache_key("complexity:*"),
        ]

        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += await self.invalidate_pattern(pattern)

        return total_invalidated

    async def _is_file_modified(self, file_path: str) -> bool:
        """Check if file has been modified since last cache."""
        try:
            path = Path(file_path)
            if not path.exists():
                return True

            current_mtime = path.stat().st_mtime
            cached_mtime = self._file_mtimes.get(file_path)

            if cached_mtime is None:
                return True

            return current_mtime > cached_mtime

        except Exception as e:
            logger.warning(
                "File modification check error", file_path=file_path, error=str(e)
            )
            return True  # Assume modified on error

    async def _update_file_mtime(self, file_path: str) -> None:
        """Update the cached modification time for a file."""
        try:
            path = Path(file_path)
            if path.exists():
                self._file_mtimes[file_path] = path.stat().st_mtime
        except Exception as e:
            logger.warning("File mtime update error", file_path=file_path, error=str(e))

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            stats = self.cache_stats.copy()

            # Add hit rate
            total_ops = stats["hits"] + stats["misses"]
            stats["hit_rate"] = stats["hits"] / total_ops if total_ops > 0 else 0

            # Add cache sizes
            stats["memory_cache_size"] = len(self.memory_cache)
            stats["file_mtimes_tracked"] = len(self._file_mtimes)
            stats["redis_connected"] = self.redis_connected

            # Redis-specific stats
            if self.redis_connected and self.redis_client:
                try:
                    redis_info = await self.redis_client.info("keyspace")
                    db_key = f"db{self.redis_db}"
                    if db_key in redis_info:
                        db_info = redis_info[db_key]
                        stats["redis_keys"] = db_info["keys"]
                        stats["redis_expires"] = db_info["expires"]
                except Exception:
                    pass

            stats["timestamp"] = datetime.utcnow().isoformat()
            return stats

        except Exception as e:
            logger.warning("Cache stats error", error=str(e))
            return {"error": str(e)}

    async def cleanup(self):
        """Clean up cache connections."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_connected = False

        # Clear memory caches
        self.memory_cache.clear()
        self._file_mtimes.clear()


def enhanced_cache_tool(
    ttl: Optional[int] = None,
    cache_type: str = "default",
    key_prefix: str = "",
    exclude_args: Optional[List[str]] = None,
    invalidate_on: Optional[List[str]] = None,
):
    """Enhanced decorator for caching tool results with intelligent invalidation.

    Args:
        ttl: Time to live for cache entry
        cache_type: Type of cache to use ('default', 'file_data', 'project_stats', 'query_result')
        key_prefix: Prefix for cache key
        exclude_args: List of argument names to exclude from cache key generation
        invalidate_on: List of file patterns that should invalidate this cache
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager instance
            cache_manager = getattr(wrapper, "_cache_manager", None)
            if not cache_manager:
                # No cache manager, execute function normally
                return await func(*args, **kwargs)

            # Generate cache key
            exclude_set = set(exclude_args or [])
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in exclude_set}

            key_data = {"func": func.__name__, "args": args, "kwargs": filtered_kwargs}
            cache_key_data = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = (
                f"{key_prefix}{hashlib.md5(cache_key_data.encode()).hexdigest()}"
            )

            # Try to get from cache
            cached_result = None
            if cache_type == "file_data":
                file_path = kwargs.get("file_path") or (args[0] if args else None)
                if file_path:
                    cached_result = await cache_manager.get_file_data(str(file_path))
            elif cache_type == "query_result":
                cached_result = await cache_manager.get_query_result(cache_key)
            else:
                cached_result = await cache_manager.get(cache_key)

            if cached_result is not None:
                logger.debug(
                    "Enhanced cache hit", func=func.__name__, cache_type=cache_type
                )
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Store in appropriate cache
            if cache_type == "file_data":
                file_path = kwargs.get("file_path") or (args[0] if args else None)
                if file_path:
                    await cache_manager.set_file_data(str(file_path), result)
            elif cache_type == "query_result":
                await cache_manager.set_query_result(cache_key, result)
            else:
                await cache_manager.set(cache_key, result, ttl)

            logger.debug(
                "Enhanced cache set", func=func.__name__, cache_type=cache_type
            )
            return result

        return wrapper

    return decorator


def set_enhanced_cache_manager(
    func: Callable, cache_manager: EnhancedCacheManager
) -> None:
    """Attach enhanced cache manager to a decorated function."""
    func._cache_manager = cache_manager


# Global instance
enhanced_cache_manager: Optional[EnhancedCacheManager] = None


async def get_enhanced_cache() -> EnhancedCacheManager:
    """Get the global enhanced cache manager instance."""
    global enhanced_cache_manager
    if not enhanced_cache_manager:
        enhanced_cache_manager = EnhancedCacheManager()
        await enhanced_cache_manager.initialize()
    return enhanced_cache_manager
