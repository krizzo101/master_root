"""
Redis Caching Layer for Real-time Collaboration Data
High-performance caching with pub/sub for real-time updates
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    value: Any
    ttl: int
    created_at: datetime
    hit_count: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


class CollaborationCache:
    """High-performance Redis-based caching for collaboration data"""

    def __init__(self, redis_pool: aioredis.ConnectionPool, namespace: str = "collab"):
        self.redis_pool = redis_pool
        self.namespace = namespace
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._pubsub_client: Optional[aioredis.Redis] = None
        self._listening = False

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with hit tracking"""
        cache_key = self._make_key(key)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                # Get value and increment hit counter
                pipe = redis.pipeline()
                pipe.get(cache_key)
                pipe.hincrby(f"{cache_key}:meta", "hit_count", 1)
                results = await pipe.execute()

                value = results[0]
                if value is not None:
                    return json.loads(value)

                return default

            except Exception as e:
                logger.warning(f"Cache get failed for {key}: {e}")
                return default

    async def set(
        self, key: str, value: Any, ttl: int = 300, notify: bool = True
    ) -> bool:
        """Set value in cache with metadata"""
        cache_key = self._make_key(key)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                # Store value and metadata
                pipe = redis.pipeline()
                pipe.setex(cache_key, ttl, json.dumps(value, default=str))
                pipe.hset(
                    f"{cache_key}:meta",
                    mapping={
                        "created_at": datetime.utcnow().isoformat(),
                        "ttl": ttl,
                        "hit_count": 0,
                    },
                )
                pipe.expire(f"{cache_key}:meta", ttl)
                await pipe.execute()

                # Publish cache update notification
                if notify:
                    await self._publish_cache_event("set", key, value)

                return True

            except Exception as e:
                logger.error(f"Cache set failed for {key}: {e}")
                return False

    async def delete(self, key: str, notify: bool = True) -> bool:
        """Delete value from cache"""
        cache_key = self._make_key(key)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                pipe = redis.pipeline()
                pipe.delete(cache_key)
                pipe.delete(f"{cache_key}:meta")
                result = await pipe.execute()

                deleted = result[0] > 0

                # Publish cache delete notification
                if deleted and notify:
                    await self._publish_cache_event("delete", key, None)

                return deleted

            except Exception as e:
                logger.error(f"Cache delete failed for {key}: {e}")
                return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._make_key(key)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                return await redis.exists(cache_key) > 0
            except Exception as e:
                logger.warning(f"Cache exists check failed for {key}: {e}")
                return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set new TTL for existing key"""
        cache_key = self._make_key(key)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                pipe = redis.pipeline()
                pipe.expire(cache_key, ttl)
                pipe.hset(f"{cache_key}:meta", "ttl", ttl)
                pipe.expire(f"{cache_key}:meta", ttl)
                result = await pipe.execute()

                return result[0] > 0

            except Exception as e:
                logger.error(f"Cache expire failed for {key}: {e}")
                return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values efficiently"""
        if not keys:
            return {}

        cache_keys = [self._make_key(key) for key in keys]

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                values = await redis.mget(cache_keys)
                result = {}

                for original_key, value in zip(keys, values):
                    if value is not None:
                        try:
                            result[original_key] = json.loads(value)
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in cache for {original_key}")

                return result

            except Exception as e:
                logger.error(f"Cache get_many failed: {e}")
                return {}

    async def set_many(self, data: Dict[str, Any], ttl: int = 300) -> int:
        """Set multiple values efficiently"""
        if not data:
            return 0

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                pipe = redis.pipeline()

                for key, value in data.items():
                    cache_key = self._make_key(key)
                    pipe.setex(cache_key, ttl, json.dumps(value, default=str))

                results = await pipe.execute()
                return sum(1 for r in results if r)

            except Exception as e:
                logger.error(f"Cache set_many failed: {e}")
                return 0

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        full_pattern = self._make_key(pattern)

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                keys = []
                async for key in redis.scan_iter(match=full_pattern):
                    keys.append(key)

                if keys:
                    return await redis.delete(*keys)
                return 0

            except Exception as e:
                logger.error(f"Cache delete_pattern failed for {pattern}: {e}")
                return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                # Get Redis info
                info = await redis.info("memory")
                keyspace = await redis.info("keyspace")

                # Count our namespace keys
                our_keys = 0
                async for key in redis.scan_iter(match=f"{self.namespace}:*"):
                    our_keys += 1

                # Get hit rates from metadata
                hit_stats = []
                async for key in redis.scan_iter(match=f"{self.namespace}:*:meta"):
                    meta = await redis.hgetall(key)
                    if meta:
                        hit_stats.append(
                            {
                                "key": key.decode()
                                .replace(f"{self.namespace}:", "")
                                .replace(":meta", ""),
                                "hit_count": int(meta.get(b"hit_count", 0)),
                                "created_at": meta.get(b"created_at", b"").decode(),
                            }
                        )

                return {
                    "namespace_keys": our_keys,
                    "memory_usage_mb": info.get("used_memory", 0) / (1024 * 1024),
                    "total_keys": sum(db.get("keys", 0) for db in keyspace.values()),
                    "hit_stats": sorted(
                        hit_stats, key=lambda x: x["hit_count"], reverse=True
                    )[:20],
                }

            except Exception as e:
                logger.error(f"Cache stats failed: {e}")
                return {}


class RealTimeCollaborationCache(CollaborationCache):
    """Extended cache with real-time pub/sub capabilities"""

    async def start_listening(self):
        """Start listening for real-time updates"""
        if self._listening:
            return

        self._pubsub_client = aioredis.Redis(connection_pool=self.redis_pool)
        pubsub = self._pubsub_client.pubsub()

        # Subscribe to cache events
        await pubsub.subscribe(f"{self.namespace}:events")
        self._listening = True

        # Start listening task
        import asyncio

        asyncio.create_task(self._listen_for_updates(pubsub))

    async def stop_listening(self):
        """Stop listening for real-time updates"""
        self._listening = False
        if self._pubsub_client:
            await self._pubsub_client.close()
            self._pubsub_client = None

    async def subscribe_to_pattern(self, pattern: str, callback: Callable):
        """Subscribe to cache events matching pattern"""
        if pattern not in self._subscribers:
            self._subscribers[pattern] = set()

        self._subscribers[pattern].add(callback)

        if not self._listening:
            await self.start_listening()

    async def unsubscribe_from_pattern(self, pattern: str, callback: Callable):
        """Unsubscribe from cache events"""
        if pattern in self._subscribers:
            self._subscribers[pattern].discard(callback)

            if not self._subscribers[pattern]:
                del self._subscribers[pattern]

    async def _publish_cache_event(self, event_type: str, key: str, value: Any):
        """Publish cache event for real-time updates"""
        if not self._listening:
            return

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            try:
                event_data = {
                    "type": event_type,
                    "key": key,
                    "value": value,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                await redis.publish(
                    f"{self.namespace}:events", json.dumps(event_data, default=str)
                )

            except Exception as e:
                logger.error(f"Failed to publish cache event: {e}")

    async def _listen_for_updates(self, pubsub):
        """Listen for cache update events and notify subscribers"""
        try:
            while self._listening:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    continue

                try:
                    event_data = json.loads(message["data"])
                    key = event_data["key"]

                    # Notify matching subscribers
                    for pattern, callbacks in self._subscribers.items():
                        if self._pattern_matches(key, pattern):
                            for callback in callbacks:
                                try:
                                    await callback(event_data)
                                except Exception as e:
                                    logger.error(f"Subscriber callback failed: {e}")

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid event data: {e}")

        except Exception as e:
            logger.error(f"Cache listener error: {e}")

        finally:
            await pubsub.unsubscribe()
            await pubsub.close()

    def _pattern_matches(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys"""
        if "*" not in pattern:
            return key == pattern

        import re

        regex_pattern = pattern.replace("*", ".*")
        return re.match(f"^{regex_pattern}$", key) is not None


class DistributedLock:
    """Distributed locking using Redis"""

    def __init__(
        self, redis_pool: aioredis.ConnectionPool, lock_key: str, timeout: int = 30
    ):
        self.redis_pool = redis_pool
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout
        self.identifier = None

    async def __aenter__(self):
        """Acquire distributed lock"""
        import uuid

        self.identifier = str(uuid.uuid4())

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            # Try to acquire lock with timeout
            end_time = datetime.utcnow() + timedelta(seconds=self.timeout)

            while datetime.utcnow() < end_time:
                if await redis.set(
                    self.lock_key, self.identifier, nx=True, ex=self.timeout
                ):
                    return self

                # Wait a bit before retrying
                await asyncio.sleep(0.01)

            raise TimeoutError(f"Failed to acquire lock {self.lock_key}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release distributed lock"""
        if self.identifier is None:
            return

        async with aioredis.Redis(connection_pool=self.redis_pool) as redis:
            # Only release if we own the lock
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """

            await redis.eval(lua_script, 1, self.lock_key, self.identifier)


class CollaborationCacheManager:
    """High-level cache management for collaboration features"""

    def __init__(self, redis_pool: aioredis.ConnectionPool):
        self.agent_cache = RealTimeCollaborationCache(redis_pool, "agents")
        self.session_cache = RealTimeCollaborationCache(redis_pool, "sessions")
        self.message_cache = RealTimeCollaborationCache(redis_pool, "messages")
        self.analytics_cache = CollaborationCache(redis_pool, "analytics")

    async def cache_agent_status(self, agent_id: str, status_data: Dict, ttl: int = 30):
        """Cache agent status with real-time updates"""
        await self.agent_cache.set(f"status:{agent_id}", status_data, ttl=ttl)

    async def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get cached agent status"""
        return await self.agent_cache.get(f"status:{agent_id}")

    async def cache_session_state(
        self, session_id: str, session_data: Dict, ttl: int = 300
    ):
        """Cache session state"""
        await self.session_cache.set(f"state:{session_id}", session_data, ttl=ttl)

    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs from cache"""
        sessions = await self.session_cache.get("active_sessions", [])
        return sessions

    async def add_active_session(self, session_id: str):
        """Add session to active sessions list"""
        async with DistributedLock(
            self.session_cache.redis_pool, "active_sessions_lock"
        ):
            sessions = await self.get_active_sessions()
            if session_id not in sessions:
                sessions.append(session_id)
                await self.session_cache.set("active_sessions", sessions, ttl=3600)

    async def remove_active_session(self, session_id: str):
        """Remove session from active sessions list"""
        async with DistributedLock(
            self.session_cache.redis_pool, "active_sessions_lock"
        ):
            sessions = await self.get_active_sessions()
            if session_id in sessions:
                sessions.remove(session_id)
                await self.session_cache.set("active_sessions", sessions, ttl=3600)

    async def cache_recent_messages(
        self, session_id: str, messages: List[Dict], ttl: int = 600
    ):
        """Cache recent messages for quick access"""
        await self.message_cache.set(f"recent:{session_id}", messages, ttl=ttl)

    async def get_recent_messages(self, session_id: str) -> List[Dict]:
        """Get cached recent messages"""
        return await self.message_cache.get(f"recent:{session_id}", [])

    async def cache_analytics_result(
        self, query_hash: str, result: Dict, ttl: int = 1800
    ):
        """Cache analytics query results"""
        await self.analytics_cache.set(f"query:{query_hash}", result, ttl=ttl)

    async def get_cached_analytics(self, query_hash: str) -> Optional[Dict]:
        """Get cached analytics results"""
        return await self.analytics_cache.get(f"query:{query_hash}")

    async def invalidate_session_cache(self, session_id: str):
        """Invalidate all cache entries for a session"""
        await self.session_cache.delete_pattern(f"*{session_id}*")
        await self.message_cache.delete_pattern(f"*{session_id}*")

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get overall cache health metrics"""
        health = {}

        for name, cache in [
            ("agents", self.agent_cache),
            ("sessions", self.session_cache),
            ("messages", self.message_cache),
            ("analytics", self.analytics_cache),
        ]:
            health[name] = await cache.get_stats()

        return health
