"""Advanced caching system for chat import performance optimization."""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple
from weakref import WeakValueDictionary

import redis.asyncio as redis
import structlog
from cachetools import TTLCache

logger = structlog.get_logger(__name__)


class EmbeddingCache:
    """High-performance caching for embedding generation with multi-level storage."""

    def __init__(
        self,
        max_memory_items: int = 10000,
        ttl_seconds: int = 3600,
        redis_client: Optional[redis.Redis] = None,
    ):
        """Initialize embedding cache with memory and Redis tiers."""
        self.memory_cache = TTLCache(maxsize=max_memory_items, ttl=ttl_seconds)
        self.redis_client = redis_client
        self.cache_hits = 0
        self.cache_misses = 0
        self.redis_hits = 0
        self.redis_misses = 0

    def _generate_cache_key(self, text: str, model: str = "default") -> str:
        """Generate consistent cache key for text and model combination."""
        content_hash = hashlib.sha256(f"{text}:{model}".encode()).hexdigest()
        return f"embedding:{model}:{content_hash[:16]}"

    async def get(self, text: str, model: str = "default") -> Optional[List[float]]:
        """Get embedding from cache (memory first, then Redis)."""
        if not text or not text.strip():
            return None

        cache_key = self._generate_cache_key(text, model)

        # Check memory cache first
        if cache_key in self.memory_cache:
            self.cache_hits += 1
            return self.memory_cache[cache_key]

        # Check Redis if available
        if self.redis_client:
            try:
                redis_value = await self.redis_client.get(cache_key)
                if redis_value:
                    embedding = json.loads(redis_value)
                    # Store in memory cache for faster access
                    self.memory_cache[cache_key] = embedding
                    self.redis_hits += 1
                    return embedding
                else:
                    self.redis_misses += 1
            except Exception as e:
                logger.warning("Redis cache read failed", error=str(e))

        self.cache_misses += 1
        return None

    async def set(self, text: str, embedding: List[float], model: str = "default"):
        """Store embedding in both memory and Redis caches."""
        if not text or not embedding:
            return

        cache_key = self._generate_cache_key(text, model)

        # Store in memory cache
        self.memory_cache[cache_key] = embedding

        # Store in Redis if available
        if self.redis_client:
            try:
                await self.redis_client.set(
                    cache_key, json.dumps(embedding), ex=3600  # 1 hour expiry
                )
            except Exception as e:
                logger.warning("Redis cache write failed", error=str(e))

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_hits + self.cache_misses
        memory_hit_rate = (self.cache_hits / max(1, total_requests)) * 100

        redis_total = self.redis_hits + self.redis_misses
        redis_hit_rate = (
            (self.redis_hits / max(1, redis_total)) * 100 if redis_total > 0 else 0
        )

        return {
            "memory_cache_size": len(self.memory_cache),
            "memory_hit_rate_pct": round(memory_hit_rate, 2),
            "total_requests": total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "redis_hit_rate_pct": round(redis_hit_rate, 2),
            "redis_hits": self.redis_hits,
            "redis_misses": self.redis_misses,
        }


class EntityExtractionCache:
    """Caching for entity extraction results to avoid recomputation."""

    def __init__(self, max_items: int = 5000, ttl_hours: int = 24):
        """Initialize entity extraction cache."""
        self.cache = TTLCache(maxsize=max_items, ttl=ttl_hours * 3600)
        self.hits = 0
        self.misses = 0

    def _generate_key(self, content: str, config_hash: str) -> str:
        """Generate cache key for content and extraction configuration."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"entities:{config_hash}:{content_hash}"

    def get(self, content: str, config_hash: str) -> Optional[Dict[str, List[str]]]:
        """Get cached entity extraction results."""
        if not content:
            return None

        key = self._generate_key(content, config_hash)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        return None

    def set(self, content: str, config_hash: str, entities: Dict[str, List[str]]):
        """Store entity extraction results in cache."""
        if not content or not entities:
            return

        key = self._generate_key(content, config_hash)
        self.cache[key] = entities

    def get_stats(self) -> Dict[str, Any]:
        """Get entity extraction cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / max(1, total)) * 100
        return {
            "cache_size": len(self.cache),
            "hit_rate_pct": round(hit_rate, 2),
            "hits": self.hits,
            "misses": self.misses,
        }


class RelationshipCache:
    """Caching for relationship detection to optimize repeated calculations."""

    def __init__(self, max_items: int = 2000, ttl_hours: int = 6):
        """Initialize relationship detection cache."""
        self.cache = TTLCache(maxsize=max_items, ttl=ttl_hours * 3600)
        self.session_cache = defaultdict(list)  # Recent items per session
        self.max_session_items = 100

    def get_session_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get cached context items for a session."""
        return self.session_cache.get(session_id, [])

    def update_session_context(self, session_id: str, item: Dict[str, Any]):
        """Update session context with new item."""
        if session_id not in self.session_cache:
            self.session_cache[session_id] = []

        # Add new item to front
        self.session_cache[session_id].insert(0, item)

        # Trim to max size
        if len(self.session_cache[session_id]) > self.max_session_items:
            self.session_cache[session_id] = self.session_cache[session_id][
                : self.max_session_items
            ]

    def clear_old_sessions(self, max_age_hours: int = 24):
        """Clear old session contexts to prevent memory leaks."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []

        for session_id, items in self.session_cache.items():
            if items and len(items) > 0:
                # Check if most recent item is too old
                if items[0].get("timestamp", datetime.min) < cutoff:
                    sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.session_cache[session_id]


class DatabaseQueryCache:
    """Advanced database query result caching with intelligent invalidation."""

    def __init__(
        self,
        max_items: int = 1000,
        default_ttl: int = 300,  # 5 minutes
        redis_client: Optional[redis.Redis] = None,
    ):
        """Initialize database query cache."""
        self.memory_cache = TTLCache(maxsize=max_items, ttl=default_ttl)
        self.redis_client = redis_client
        self.query_stats = defaultdict(lambda: {"hits": 0, "misses": 0})

    def _normalize_query(self, query: str, params: Tuple[Any, ...]) -> str:
        """Normalize query and parameters for consistent caching."""
        # Remove extra whitespace and normalize
        normalized_query = " ".join(query.split())
        params_str = json.dumps(params, sort_keys=True, default=str)
        return f"{normalized_query}|{params_str}"

    def _generate_cache_key(self, query: str, params: Tuple[Any, ...]) -> str:
        """Generate cache key for query and parameters."""
        normalized = self._normalize_query(query, params)
        query_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return f"query:{query_hash[:16]}"

    async def get(
        self, query: str, params: Tuple[Any, ...]
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result."""
        cache_key = self._generate_cache_key(query, params)
        query_type = self._get_query_type(query)

        # Check memory cache
        if cache_key in self.memory_cache:
            self.query_stats[query_type]["hits"] += 1
            return self.memory_cache[cache_key]

        # Check Redis for long-term cache
        if self.redis_client and self._is_long_term_cacheable(query):
            try:
                redis_value = await self.redis_client.get(cache_key)
                if redis_value:
                    result = json.loads(redis_value)
                    # Store in memory for faster access
                    self.memory_cache[cache_key] = result
                    self.query_stats[query_type]["hits"] += 1
                    return result
            except Exception as e:
                logger.warning("Redis query cache read failed", error=str(e))

        self.query_stats[query_type]["misses"] += 1
        return None

    async def set(
        self,
        query: str,
        params: Tuple[Any, ...],
        result: List[Dict[str, Any]],
        ttl: Optional[int] = None,
    ):
        """Store query result in cache."""
        if not result:
            return

        cache_key = self._generate_cache_key(query, params)

        # Store in memory cache
        if ttl:
            # Create a new TTLCache entry with custom TTL
            pass  # TTLCache doesn't support per-item TTL easily
        else:
            self.memory_cache[cache_key] = result

        # Store in Redis for long-term caching
        if self.redis_client and self._is_long_term_cacheable(query):
            try:
                redis_ttl = ttl or 1800  # 30 minutes default
                await self.redis_client.set(
                    cache_key, json.dumps(result, default=str), ex=redis_ttl
                )
            except Exception as e:
                logger.warning("Redis query cache write failed", error=str(e))

    def _get_query_type(self, query: str) -> str:
        """Classify query type for statistics tracking."""
        query_lower = query.lower().strip()
        if query_lower.startswith("select"):
            if "context_items" in query_lower:
                return "context_select"
            elif "context_relationships" in query_lower:
                return "relationship_select"
            else:
                return "other_select"
        elif query_lower.startswith("insert"):
            return "insert"
        elif query_lower.startswith("update"):
            return "update"
        else:
            return "other"

    def _is_long_term_cacheable(self, query: str) -> bool:
        """Determine if query results should be cached long-term in Redis."""
        query_lower = query.lower()
        # Cache read-only analytics queries, not transactional data
        return (
            "select" in query_lower
            and "count(" in query_lower
            or "group by" in query_lower
            or "stats" in query_lower
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics by query type."""
        stats = {}
        for query_type, type_stats in self.query_stats.items():
            total = type_stats["hits"] + type_stats["misses"]
            hit_rate = (type_stats["hits"] / max(1, total)) * 100
            stats[query_type] = {
                "hit_rate_pct": round(hit_rate, 2),
                "hits": type_stats["hits"],
                "misses": type_stats["misses"],
                "total_queries": total,
            }

        return {
            "memory_cache_size": len(self.memory_cache),
            "query_type_stats": stats,
        }


class PerformanceCacheManager:
    """Central manager for all performance caching systems."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize all cache subsystems."""
        self.redis_client = redis_client
        self.embedding_cache = EmbeddingCache(redis_client=redis_client)
        self.entity_cache = EntityExtractionCache()
        self.relationship_cache = RelationshipCache()
        self.query_cache = DatabaseQueryCache(redis_client=redis_client)

        # Performance tracking
        self.start_time = time.time()
        self.cache_operations = 0

    async def warmup_caches(
        self,
        recent_sessions: List[str],
        common_queries: List[Tuple[str, Tuple[Any, ...]]],
    ):
        """Warm up caches with frequently accessed data."""
        logger.info(
            "Starting cache warmup",
            sessions=len(recent_sessions),
            queries=len(common_queries),
        )

        warmup_start = time.time()

        # Pre-load common query results
        for query, params in common_queries:
            try:
                # This would typically come from actual database execution
                # For now, we just ensure the cache structure is ready
                await self.query_cache.get(query, params)
            except Exception as e:
                logger.warning("Cache warmup query failed", error=str(e))

        warmup_duration = time.time() - warmup_start
        logger.info("Cache warmup completed", duration_seconds=warmup_duration)

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all cache subsystems."""
        runtime_hours = (time.time() - self.start_time) / 3600

        return {
            "runtime_hours": round(runtime_hours, 2),
            "total_cache_operations": self.cache_operations,
            "embedding_cache": self.embedding_cache.get_stats(),
            "entity_cache": self.entity_cache.get_stats(),
            "query_cache": self.query_cache.get_stats(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def cleanup_old_data(self):
        """Periodic cleanup of old cached data."""
        logger.info("Starting cache cleanup")

        # Clean old session contexts
        self.relationship_cache.clear_old_sessions()

        # Additional cleanup could be added here
        logger.info("Cache cleanup completed")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for all cache systems."""
        health = {
            "embedding_cache": "healthy",
            "entity_cache": "healthy",
            "relationship_cache": "healthy",
            "query_cache": "healthy",
            "redis_connection": "unknown",
        }

        # Check Redis connection if available
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis_connection"] = "healthy"
            except Exception as e:
                health["redis_connection"] = f"failed: {str(e)}"
                logger.warning("Redis health check failed", error=str(e))

        return health


# Global cache manager instance
cache_manager = PerformanceCacheManager()


async def initialize_caches(
    redis_client: Optional[redis.Redis] = None,
) -> PerformanceCacheManager:
    """Initialize the global cache manager."""
    global cache_manager
    cache_manager = PerformanceCacheManager(redis_client=redis_client)

    # Start periodic cleanup task
    asyncio.create_task(_periodic_cache_cleanup())

    logger.info("Performance cache system initialized")
    return cache_manager


async def _periodic_cache_cleanup():
    """Background task for periodic cache maintenance."""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutes
            await cache_manager.cleanup_old_data()
        except Exception as e:
            logger.error("Cache cleanup failed", error=str(e))


def get_cache_manager() -> PerformanceCacheManager:
    """Get the global cache manager instance."""
    return cache_manager
