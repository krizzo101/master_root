"""
Cache Manager with TTL-based expiration.

Provides async caching capabilities with time-to-live (TTL) support,
memory and disk persistence, and automatic cleanup.

Author: Autonomous Claude Agent
Created: 2025-08-15
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum

import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)


class CacheBackend(Enum):
    """Cache storage backend types."""

    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"  # Memory with disk persistence


class EvictionPolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time-based expiration only


@dataclass
class CacheConfig:
    """Configuration for cache manager."""

    backend: CacheBackend = CacheBackend.HYBRID
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_disk_size: int = 1024 * 1024 * 1024  # 1GB
    default_ttl: int = 3600  # 1 hour
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    cache_dir: Path = Path(".cache/research")
    enable_compression: bool = True
    cleanup_interval: int = 300  # 5 minutes
    serialize_format: str = "json"  # json or pickle
    enable_stats: bool = True


@dataclass
class CacheEntry:
    """Individual cache entry."""

    key: str
    value: Any
    size: int
    ttl: int
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.now() > self.expires_at

    def update_access(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "size": self.size,
            "ttl": self.ttl,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            size=data["size"],
            ttl=data["ttl"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(
                data.get("last_accessed", datetime.now().isoformat())
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired: int = 0
    total_size: int = 0
    entry_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expired": self.expired,
            "total_size": self.total_size,
            "entry_count": self.entry_count,
            "hit_rate": self.hit_rate,
        }


class CacheManager:
    """Async cache manager with TTL support."""

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_order: List[str] = []  # For LRU/FIFO
        self._access_counts: Dict[str, int] = {}  # For LFU
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized = False

        logger.info(f"CacheManager initialized with backend: {self.config.backend}")

    async def initialize(self) -> None:
        """Initialize cache manager and start cleanup task."""
        if self._initialized:
            return

        # Create cache directory if using disk backend
        if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)

            # Load existing cache from disk
            await self._load_from_disk()

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self._initialized = True
        logger.info("Cache manager initialized and cleanup task started")

    async def close(self) -> None:
        """Close cache manager and save state."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Save cache to disk if using hybrid backend
        if self.config.backend == CacheBackend.HYBRID:
            await self._save_to_disk()

        self._initialized = False
        logger.info("Cache manager closed")

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        async with self._lock:
            # Check memory cache
            if key in self._memory_cache:
                entry = self._memory_cache[key]

                if entry.is_expired():
                    # Remove expired entry
                    await self._remove_entry(key)
                    self._stats.expired += 1
                    self._stats.misses += 1
                    return default

                # Update access statistics
                entry.update_access()
                self._update_access_order(key)

                if self.config.enable_stats:
                    self._stats.hits += 1

                logger.debug(f"Cache hit for key: {key}")
                return entry.value

            # Check disk cache if using disk/hybrid backend
            if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
                entry = await self._load_from_disk_entry(key)
                if entry and not entry.is_expired():
                    # Add to memory cache
                    self._memory_cache[key] = entry
                    self._update_access_order(key)

                    if self.config.enable_stats:
                        self._stats.hits += 1

                    logger.debug(f"Disk cache hit for key: {key}")
                    return entry.value

            if self.config.enable_stats:
                self._stats.misses += 1

            logger.debug(f"Cache miss for key: {key}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
            metadata: Optional metadata

        Returns:
            True if successfully cached
        """
        if not self._initialized:
            await self.initialize()

        ttl = ttl or self.config.default_ttl

        # Calculate size
        size = self._calculate_size(value)

        # Check size limits
        if size > self.config.max_memory_size:
            logger.warning(f"Value too large to cache: {size} bytes")
            return False

        async with self._lock:
            # Check if we need to evict entries
            await self._evict_if_needed(size)

            # Create cache entry
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                ttl=ttl,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
                metadata=metadata or {},
            )

            # Add to memory cache
            self._memory_cache[key] = entry
            self._update_access_order(key)

            # Update stats
            if self.config.enable_stats:
                self._stats.total_size += size
                self._stats.entry_count = len(self._memory_cache)

            # Save to disk if using disk/hybrid backend
            if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
                await self._save_to_disk_entry(key, entry)

            logger.debug(f"Cached key: {key} (size: {size} bytes, ttl: {ttl}s)")
            return True

    async def delete(self, key: str) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted
        """
        async with self._lock:
            if key in self._memory_cache:
                await self._remove_entry(key)
                logger.debug(f"Deleted cache key: {key}")
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._memory_cache.clear()
            self._cache_order.clear()
            self._access_counts.clear()

            # Clear disk cache
            if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
                await self._clear_disk_cache()

            # Reset stats
            self._stats = CacheStats()

            logger.info("Cache cleared")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        async with self._lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired():
                    return True
                else:
                    await self._remove_entry(key)

            # Check disk
            if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
                entry = await self._load_from_disk_entry(key)
                return entry is not None and not entry.is_expired()

            return False

    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        async with self._lock:
            return self._stats

    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        Get list of cache keys.

        Args:
            pattern: Optional pattern to filter keys

        Returns:
            List of matching keys
        """
        async with self._lock:
            keys = list(self._memory_cache.keys())

            if pattern:
                import fnmatch

                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]

            return keys

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes."""
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        elif isinstance(value, bytes):
            return len(value)
        elif isinstance(value, (dict, list)):
            # Serialize to estimate size
            try:
                serialized = json.dumps(value)
                return len(serialized.encode("utf-8"))
            except (TypeError, ValueError):
                # Fall back to pickle for complex objects
                serialized = pickle.dumps(value)
                return len(serialized)
        else:
            # Use pickle for other types
            try:
                serialized = pickle.dumps(value)
                return len(serialized)
            except Exception:
                return 1000  # Default size estimate

    def _update_access_order(self, key: str) -> None:
        """Update access order for eviction policies."""
        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Move to end (most recently used)
            if key in self._cache_order:
                self._cache_order.remove(key)
            self._cache_order.append(key)

        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Update access count
            self._access_counts[key] = self._access_counts.get(key, 0) + 1

        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Add to end if new
            if key not in self._cache_order:
                self._cache_order.append(key)

    async def _evict_if_needed(self, required_size: int) -> None:
        """Evict entries if needed to make space."""
        current_size = sum(e.size for e in self._memory_cache.values())

        while current_size + required_size > self.config.max_memory_size:
            # Select entry to evict based on policy
            evict_key = self._select_eviction_candidate()

            if evict_key:
                entry = self._memory_cache[evict_key]
                current_size -= entry.size
                await self._remove_entry(evict_key)

                if self.config.enable_stats:
                    self._stats.evictions += 1

                logger.debug(f"Evicted cache key: {evict_key}")
            else:
                break

    def _select_eviction_candidate(self) -> Optional[str]:
        """Select entry to evict based on policy."""
        if not self._memory_cache:
            return None

        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Evict least recently used
            if self._cache_order:
                return self._cache_order[0]

        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Evict least frequently used
            if self._access_counts:
                return min(self._access_counts, key=self._access_counts.get)

        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Evict oldest
            if self._cache_order:
                return self._cache_order[0]

        elif self.config.eviction_policy == EvictionPolicy.TTL:
            # Evict closest to expiration
            return min(self._memory_cache.keys(), key=lambda k: self._memory_cache[k].expires_at)

        # Fallback: evict any entry
        return next(iter(self._memory_cache.keys()))

    async def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._memory_cache:
            entry = self._memory_cache[key]

            # Update stats
            if self.config.enable_stats:
                self._stats.total_size -= entry.size
                self._stats.entry_count = len(self._memory_cache) - 1

            # Remove from memory
            del self._memory_cache[key]

            # Remove from tracking structures
            if key in self._cache_order:
                self._cache_order.remove(key)
            if key in self._access_counts:
                del self._access_counts[key]

            # Remove from disk
            if self.config.backend in [CacheBackend.DISK, CacheBackend.HYBRID]:
                await self._delete_disk_entry(key)

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        async with self._lock:
            expired_keys = [key for key, entry in self._memory_cache.items() if entry.is_expired()]

            for key in expired_keys:
                await self._remove_entry(key)
                if self.config.enable_stats:
                    self._stats.expired += 1

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")

    def _get_disk_path(self, key: str) -> Path:
        """Get disk path for cache key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.config.cache_dir / f"{key_hash}.cache"

    async def _save_to_disk_entry(self, key: str, entry: CacheEntry) -> None:
        """Save single entry to disk."""
        path = self._get_disk_path(key)

        try:
            data = entry.to_dict()

            if self.config.serialize_format == "json":
                async with aiofiles.open(path, "w") as f:
                    await f.write(json.dumps(data))
            else:  # pickle
                async with aiofiles.open(path, "wb") as f:
                    await f.write(pickle.dumps(data))

        except Exception as e:
            logger.error(f"Failed to save cache entry to disk: {e}")

    async def _load_from_disk_entry(self, key: str) -> Optional[CacheEntry]:
        """Load single entry from disk."""
        path = self._get_disk_path(key)

        if not path.exists():
            return None

        try:
            if self.config.serialize_format == "json":
                async with aiofiles.open(path, "r") as f:
                    data = json.loads(await f.read())
            else:  # pickle
                async with aiofiles.open(path, "rb") as f:
                    data = pickle.loads(await f.read())

            return CacheEntry.from_dict(data)

        except Exception as e:
            logger.error(f"Failed to load cache entry from disk: {e}")
            return None

    async def _delete_disk_entry(self, key: str) -> None:
        """Delete entry from disk."""
        path = self._get_disk_path(key)

        try:
            if path.exists():
                await aiofiles.os.remove(path)
        except Exception as e:
            logger.error(f"Failed to delete cache entry from disk: {e}")

    async def _save_to_disk(self) -> None:
        """Save entire cache to disk."""
        for key, entry in self._memory_cache.items():
            await self._save_to_disk_entry(key, entry)

    async def _load_from_disk(self) -> None:
        """Load cache from disk."""
        if not self.config.cache_dir.exists():
            return

        for cache_file in self.config.cache_dir.glob("*.cache"):
            try:
                if self.config.serialize_format == "json":
                    async with aiofiles.open(cache_file, "r") as f:
                        data = json.loads(await f.read())
                else:  # pickle
                    async with aiofiles.open(cache_file, "rb") as f:
                        data = pickle.loads(await f.read())

                entry = CacheEntry.from_dict(data)

                if not entry.is_expired():
                    self._memory_cache[entry.key] = entry
                    self._update_access_order(entry.key)
                else:
                    # Remove expired entry from disk
                    await aiofiles.os.remove(cache_file)

            except Exception as e:
                logger.error(f"Failed to load cache file {cache_file}: {e}")

    async def _clear_disk_cache(self) -> None:
        """Clear all disk cache files."""
        if not self.config.cache_dir.exists():
            return

        for cache_file in self.config.cache_dir.glob("*.cache"):
            try:
                await aiofiles.os.remove(cache_file)
            except Exception as e:
                logger.error(f"Failed to remove cache file {cache_file}: {e}")
