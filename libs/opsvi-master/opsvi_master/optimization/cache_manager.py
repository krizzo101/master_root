"""
Intelligent Cache Manager for KG-DB Optimization System

Provides multi-tier caching with TTL management, intelligent invalidation,
and performance optimization for database and Knowledge Graph operations.
"""

from __future__ import annotations
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass
import json
import logging

from .exceptions import CacheError, PerformanceError


class CacheType(Enum):
    """Types of cached data with different TTL strategies."""

    DATABASE_QUERY = "database_query"
    KG_SEARCH = "kg_search"
    AGENT_CONFIG = "agent_config"
    PERFORMANCE_METRICS = "performance_metrics"
    FILE_CONTENTS = "file_contents"
    DIRECTORY_STRUCTURE = "directory_structure"


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""

    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)

    @property
    def age_seconds(self) -> int:
        """Age of cache entry in seconds."""
        return int((datetime.now() - self.created_at).total_seconds())

    def access(self) -> None:
        """Record access to this cache entry."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class CacheManager:
    """
    Intelligent cache manager with TTL, invalidation, and performance monitoring.

    Features:
    - Type-specific TTL strategies
    - LRU eviction with access tracking
    - Hit rate monitoring and optimization
    - Intelligent prefetching capabilities
    - Memory usage monitoring and cleanup
    """

    def __init__(self, max_entries: int = 1000, cleanup_interval: int = 300) -> None:
        self.max_entries = max_entries
        self.cleanup_interval = cleanup_interval
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "cleanups": 0}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(__name__)

        # TTL configurations by cache type (seconds)
        self._ttl_config = {
            CacheType.DATABASE_QUERY: 300,  # 5 minutes
            CacheType.KG_SEARCH: 600,  # 10 minutes
            CacheType.AGENT_CONFIG: 1800,  # 30 minutes
            CacheType.PERFORMANCE_METRICS: 60,  # 1 minute
            CacheType.FILE_CONTENTS: 900,  # 15 minutes
            CacheType.DIRECTORY_STRUCTURE: 1200,  # 20 minutes
        }

    async def start(self) -> None:
        """Start cache manager with background cleanup."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._logger.info(
                "Cache manager started with cleanup interval %ds", self.cleanup_interval
            )

    async def stop(self) -> None:
        """Stop cache manager and cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        self._logger.info("Cache manager stopped")

    async def get(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key
            cache_type: Type of cached data

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                self._stats["misses"] += 1
                self._logger.debug(
                    "Cache key %s expired (age: %ds)", key, entry.age_seconds
                )
                return None

            # Update access statistics
            entry.access()
            self._stats["hits"] += 1

            self._logger.debug(
                "Cache hit for key %s (type: %s, age: %ds)",
                key,
                cache_type.value,
                entry.age_seconds,
            )
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: CacheType,
        custom_ttl: Optional[int] = None,
    ) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cached data
            custom_ttl: Custom TTL in seconds (overrides default)
        """
        async with self._lock:
            ttl = custom_ttl or self._ttl_config.get(cache_type, 300)

            # Check if we need to evict entries
            if len(self._cache) >= self.max_entries:
                await self._evict_lru()

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                cache_type=cache_type,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl,
            )

            self._cache[key] = entry
            self._logger.debug(
                "Cached key %s (type: %s, TTL: %ds)", key, cache_type.value, ttl
            )

    async def invalidate(self, key: str) -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was found and removed
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._logger.debug("Invalidated cache key %s", key)
                return True
            return False

    async def invalidate_by_type(self, cache_type: CacheType) -> int:
        """
        Invalidate all entries of a specific type.

        Args:
            cache_type: Type of cache entries to invalidate

        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            keys_to_remove = [
                key
                for key, entry in self._cache.items()
                if entry.cache_type == cache_type
            ]

            for key in keys_to_remove:
                del self._cache[key]

            count = len(keys_to_remove)
            self._logger.debug(
                "Invalidated %d entries of type %s", count, cache_type.value
            )
            return count

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match against cache keys

        Returns:
            Number of entries invalidated
        """
        async with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]

            for key in keys_to_remove:
                del self._cache[key]

            count = len(keys_to_remove)
            self._logger.debug(
                "Invalidated %d entries matching pattern '%s'", count, pattern
            )
            return count

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            self._logger.info("Cleared all %d cache entries", entry_count)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0
            )

            # Group entries by type
            type_counts = {}
            total_memory_estimate = 0

            for entry in self._cache.values():
                cache_type = entry.cache_type.value
                type_counts[cache_type] = type_counts.get(cache_type, 0) + 1
                # Rough memory estimate
                total_memory_estimate += len(str(entry.value))

            return {
                "total_entries": len(self._cache),
                "max_entries": self.max_entries,
                "hit_rate": hit_rate,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "cleanups": self._stats["cleanups"],
                "entries_by_type": type_counts,
                "estimated_memory_bytes": total_memory_estimate,
            }

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)

        del self._cache[lru_key]
        self._stats["evictions"] += 1
        self._logger.debug("Evicted LRU cache entry: %s", lru_key)

    async def _cleanup_expired(self) -> int:
        """Clean up expired entries."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._logger.debug("Cleaned up %d expired cache entries", len(expired_keys))

        return len(expired_keys)

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                async with self._lock:
                    cleaned_count = await self._cleanup_expired()
                    if cleaned_count > 0:
                        self._stats["cleanups"] += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in cache cleanup loop: %s", e)
                await asyncio.sleep(60)  # Wait before retrying

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.

        Returns:
            Health status and recommendations
        """
        stats = await self.get_stats()
        health_status = "healthy"
        recommendations = []

        # Check hit rate
        if stats["hit_rate"] < 0.4:
            health_status = "warning"
            recommendations.append(
                "Low cache hit rate (<40%). Consider adjusting TTL or cache strategy."
            )

        # Check memory usage
        if stats["total_entries"] > self.max_entries * 0.9:
            health_status = "warning"
            recommendations.append(
                "Cache near capacity. Consider increasing max_entries or reducing TTL."
            )

        # Check eviction rate
        total_operations = stats["hits"] + stats["misses"]
        if total_operations > 0 and stats["evictions"] / total_operations > 0.1:
            health_status = "warning"
            recommendations.append(
                "High eviction rate (>10%). Consider increasing cache size."
            )

        return {
            "status": health_status,
            "statistics": stats,
            "recommendations": recommendations,
            "cleanup_task_running": self._cleanup_task is not None
            and not self._cleanup_task.done(),
        }
