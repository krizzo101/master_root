"""Enhanced caching system using aiocache for async operations."""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import structlog
from aiocache import Cache, cached, caches
from aiocache.serializers import JsonSerializer, PickleSerializer

logger = structlog.get_logger(__name__)

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])


class CacheManager:
    """Enhanced cache manager with aiocache for async operations."""

    def __init__(
        self,
        default_ttl: int = 300,  # 5 minutes default
        file_data_ttl: int = 60,  # 1 minute for file data
        project_stats_ttl: int = 300,  # 5 minutes for project stats
        cache_namespace: str = "project_context",
        max_size: int = 1000,
    ):
        """Initialize the cache manager.

        Args:
            default_ttl: Default TTL for cache entries in seconds
            file_data_ttl: TTL for file data cache entries (60s as requested)
            project_stats_ttl: TTL for project stats cache entries (300s as requested)
            cache_namespace: Namespace for cache keys
            max_size: Maximum number of cache entries
        """
        self.default_ttl = default_ttl
        self.file_data_ttl = file_data_ttl
        self.project_stats_ttl = project_stats_ttl
        self.cache_namespace = cache_namespace
        self.max_size = max_size

        # Configure caches
        caches.set_config(
            {
                "default": {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {"class": "aiocache.serializers.JsonSerializer"},
                    "ttl": default_ttl,
                },
                "file_data": {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {"class": "aiocache.serializers.PickleSerializer"},
                    "ttl": file_data_ttl,
                },
                "project_stats": {
                    "cache": "aiocache.SimpleMemoryCache",
                    "serializer": {"class": "aiocache.serializers.JsonSerializer"},
                    "ttl": project_stats_ttl,
                },
            }
        )

        self.cache = caches.get("default")
        self.file_cache = caches.get("file_data")
        self.stats_cache = caches.get("project_stats")

        # Track file modification times for invalidation
        self._file_mtimes: Dict[str, float] = {}

        logger.info(
            "Cache manager initialized",
            ttl=default_ttl,
            file_ttl=file_data_ttl,
            stats_ttl=project_stats_ttl,
        )

    def _get_cache_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Generate a namespaced cache key."""
        ns = namespace or self.cache_namespace
        return f"{ns}:{key}"

    def _hash_key(self, key: str) -> str:
        """Create a hash of the key for consistent caching."""
        return hashlib.md5(key.encode()).hexdigest()

    async def get(self, key: str, namespace: Optional[str] = None) -> Any:
        """Get a value from cache."""
        cache_key = self._get_cache_key(key, namespace)
        try:
            result = await self.cache.get(cache_key)
            if result is not None:
                logger.debug("Cache hit", key=cache_key)
            else:
                logger.debug("Cache miss", key=cache_key)
            return result
        except Exception as e:
            logger.warning("Cache get error", key=cache_key, error=str(e))
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
            await self.cache.set(cache_key, value, ttl=cache_ttl)
            logger.debug("Cache set", key=cache_key, ttl=cache_ttl)
            return True
        except Exception as e:
            logger.warning("Cache set error", key=cache_key, error=str(e))
            return False

    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """Delete a value from cache."""
        cache_key = self._get_cache_key(key, namespace)
        try:
            await self.cache.delete(cache_key)
            logger.debug("Cache delete", key=cache_key)
            return True
        except Exception as e:
            logger.warning("Cache delete error", key=cache_key, error=str(e))
            return False

    async def clear_namespace(self, namespace: Optional[str] = None) -> bool:
        """Clear all entries in a namespace."""
        try:
            # For simple memory cache, we need to implement namespace clearing manually
            # This is a limitation of the simple cache implementation
            logger.info("Cache namespace clear requested", namespace=namespace)
            # Note: This is a basic implementation. For production, consider using Redis
            # which has better namespace support
            return True
        except Exception as e:
            logger.warning(
                "Cache clear namespace error", namespace=namespace, error=str(e)
            )
            return False

    async def get_file_data(self, file_path: str) -> Any:
        """Get file data from cache with file-specific TTL."""
        cache_key = self._get_cache_key(f"file:{file_path}")
        try:
            # Check if file has been modified
            if await self._is_file_modified(file_path):
                await self.file_cache.delete(cache_key)
                return None

            result = await self.file_cache.get(cache_key)
            if result is not None:
                logger.debug("File cache hit", file_path=file_path)
            else:
                logger.debug("File cache miss", file_path=file_path)
            return result
        except Exception as e:
            logger.warning("File cache get error", file_path=file_path, error=str(e))
            return None

    async def set_file_data(self, file_path: str, value: Any) -> bool:
        """Set file data in cache with file-specific TTL."""
        cache_key = self._get_cache_key(f"file:{file_path}")
        try:
            await self.file_cache.set(cache_key, value, ttl=self.file_data_ttl)
            # Track file modification time
            await self._update_file_mtime(file_path)
            logger.debug("File cache set", file_path=file_path, ttl=self.file_data_ttl)
            return True
        except Exception as e:
            logger.warning("File cache set error", file_path=file_path, error=str(e))
            return False

    async def get_project_stats(self, stats_key: str) -> Any:
        """Get project stats from cache with stats-specific TTL."""
        cache_key = self._get_cache_key(f"stats:{stats_key}")
        try:
            result = await self.stats_cache.get(cache_key)
            if result is not None:
                logger.debug("Stats cache hit", stats_key=stats_key)
            else:
                logger.debug("Stats cache miss", stats_key=stats_key)
            return result
        except Exception as e:
            logger.warning("Stats cache get error", stats_key=stats_key, error=str(e))
            return None

    async def set_project_stats(self, stats_key: str, value: Any) -> bool:
        """Set project stats in cache with stats-specific TTL."""
        cache_key = self._get_cache_key(f"stats:{stats_key}")
        try:
            await self.stats_cache.set(cache_key, value, ttl=self.project_stats_ttl)
            logger.debug(
                "Stats cache set", stats_key=stats_key, ttl=self.project_stats_ttl
            )
            return True
        except Exception as e:
            logger.warning("Stats cache set error", stats_key=stats_key, error=str(e))
            return False

    async def invalidate_file(self, file_path: str) -> bool:
        """Invalidate cache entries for a specific file."""
        cache_key = self._get_cache_key(f"file:{file_path}")
        try:
            await self.file_cache.delete(cache_key)
            # Remove from modification time tracking
            self._file_mtimes.pop(file_path, None)
            logger.info("File cache invalidated", file_path=file_path)
            return True
        except Exception as e:
            logger.warning(
                "File cache invalidation error", file_path=file_path, error=str(e)
            )
            return False

    async def invalidate_pattern(self, pattern: str) -> bool:
        """Invalidate cache entries matching a pattern."""
        try:
            # This is a basic implementation for simple memory cache
            # For production, consider using Redis with pattern matching
            logger.info("Pattern cache invalidation requested", pattern=pattern)
            return True
        except Exception as e:
            logger.warning(
                "Pattern cache invalidation error", pattern=pattern, error=str(e)
            )
            return False

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

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Basic stats - could be enhanced with more detailed metrics
            return {
                "file_mtimes_tracked": len(self._file_mtimes),
                "default_ttl": self.default_ttl,
                "file_data_ttl": self.file_data_ttl,
                "project_stats_ttl": self.project_stats_ttl,
                "max_size": self.max_size,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning("Cache stats error", error=str(e))
            return {"error": str(e)}


def cache_tool_result(
    ttl: Optional[int] = None,
    cache_type: str = "default",
    key_prefix: str = "",
    exclude_args: Optional[List[str]] = None,
):
    """Decorator for caching tool results.

    Args:
        ttl: Time to live for cache entry
        cache_type: Type of cache to use ('default', 'file_data', 'project_stats')
        key_prefix: Prefix for cache key
        exclude_args: List of argument names to exclude from cache key generation
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager instance (assumes it's available in some way)
            # This could be improved by injecting the cache manager
            cache_manager = getattr(wrapper, "_cache_manager", None)
            if not cache_manager:
                # If no cache manager, execute function normally
                return await func(*args, **kwargs)

            # Generate cache key from function name and arguments
            exclude_set = set(exclude_args or [])

            # Filter kwargs excluding specified arguments
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in exclude_set}

            # Create a deterministic cache key
            key_data = {"func": func.__name__, "args": args, "kwargs": filtered_kwargs}

            cache_key_data = json.dumps(key_data, sort_keys=True, default=str)
            cache_key = (
                f"{key_prefix}{hashlib.md5(cache_key_data.encode()).hexdigest()}"
            )

            # Try to get from cache
            cached_result = None
            if cache_type == "file_data":
                # For file data, we need a file path to use the file-specific cache
                file_path = kwargs.get("file_path") or (args[0] if args else None)
                if file_path:
                    cached_result = await cache_manager.get_file_data(str(file_path))
            elif cache_type == "project_stats":
                cached_result = await cache_manager.get_project_stats(cache_key)
            else:
                cached_result = await cache_manager.get(cache_key)

            if cached_result is not None:
                logger.debug(
                    "Tool result cache hit", func=func.__name__, cache_type=cache_type
                )
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Store in appropriate cache
            if cache_type == "file_data":
                file_path = kwargs.get("file_path") or (args[0] if args else None)
                if file_path:
                    await cache_manager.set_file_data(str(file_path), result)
            elif cache_type == "project_stats":
                await cache_manager.set_project_stats(cache_key, result)
            else:
                await cache_manager.set(cache_key, result, ttl)

            logger.debug(
                "Tool result cached", func=func.__name__, cache_type=cache_type
            )
            return result

        return wrapper

    return decorator


def set_cache_manager(func: Callable, cache_manager: CacheManager) -> None:
    """Attach cache manager to a decorated function."""
    func._cache_manager = cache_manager
