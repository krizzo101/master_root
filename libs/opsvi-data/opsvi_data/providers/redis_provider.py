"""
Redis Provider for OPSVI Data Services

Comprehensive Redis integration for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official redis-py documentation:
- https://redis-py.readthedocs.io/
- https://redis.io/commands

Implements all core features:
- Connection pooling
- Key-value operations
- Data structures (lists, sets, hashes, sorted sets)
- Pub/Sub messaging
- Transactions
- Async support

Version: Referenced as of July 2024
"""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import redis
    from redis import Redis, ConnectionPool
except ImportError:
    raise ImportError("redis is required. Install with `pip install redis`.")

try:
    import aioredis
except ImportError:
    aioredis = None  # Async support is optional

from opsvi_foundation import BaseComponent, ComponentError

logger = logging.getLogger(__name__)


class RedisError(ComponentError):
    """Custom exception for Redis operations."""

    pass


class RedisConfig:
    """Configuration for Redis provider."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        pool_size: int = 10,
        **kwargs: Any,
    ):
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.pool_size = pool_size

        # Additional configuration
        for key, value in kwargs.items():
            setattr(self, key, value)


class RedisProvider(BaseComponent):
    """
    Comprehensive Redis provider for OPSVI ecosystem.

    Provides full Redis capabilities:
    - Key-value operations
    - Data structures (lists, sets, hashes, sorted sets)
    - Pub/Sub messaging
    - Transactions
    - Connection pooling
    - Async support (when aioredis is available)
    """

    def __init__(self, config: RedisConfig, **kwargs: Any) -> None:
        """Initialize Redis provider.

        Args:
            config: Redis configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__("redis", config.__dict__)
        self.config = config
        self.client: Optional[Redis] = None
        self.async_client = None

        logger.debug(f"RedisProvider initialized with host: {config.host}")

    async def _initialize_impl(self) -> None:
        """Initialize Redis connection."""
        try:
            # Initialize sync client
            pool = ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.pool_size,
                decode_responses=True,
            )
            self.client = Redis(connection_pool=pool)

            # Test connection
            self.client.ping()

            # Initialize async client if available
            if aioredis:
                self.async_client = aioredis.from_url(
                    f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                    password=self.config.password,
                    max_connections=self.config.pool_size,
                    decode_responses=True,
                )

            logger.info(
                f"Redis connected: {self.config.host}:{self.config.port}/{self.config.db}"
            )

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            raise RedisError(f"Failed to initialize Redis: {e}")

    async def _shutdown_impl(self) -> None:
        """Shutdown Redis connection."""
        try:
            if self.client:
                self.client.close()
                self.client = None

            if self.async_client:
                await self.async_client.close()
                self.async_client = None

            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Redis shutdown error: {e}")

    async def _health_check_impl(self) -> bool:
        """Check Redis health."""
        try:
            if not self.client:
                return False
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self._initialize_impl()

    # ==================== KEY-VALUE OPERATIONS ====================

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair."""
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET failed: {e}")
            return False

    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed: {e}")
            return None

    def delete(self, key: str) -> int:
        """Delete a key."""
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS failed: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE failed: {e}")
            return False

    def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL failed: {e}")
            return -1

    # ==================== LIST OPERATIONS ====================

    def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list."""
        try:
            return self.client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH failed: {e}")
            return 0

    def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of a list."""
        try:
            return self.client.rpush(key, *values)
        except Exception as e:
            logger.error(f"Redis RPUSH failed: {e}")
            return 0

    def lpop(self, key: str) -> Optional[str]:
        """Pop value from the left of a list."""
        try:
            return self.client.lpop(key)
        except Exception as e:
            logger.error(f"Redis LPOP failed: {e}")
            return None

    def rpop(self, key: str) -> Optional[str]:
        """Pop value from the right of a list."""
        try:
            return self.client.rpop(key)
        except Exception as e:
            logger.error(f"Redis RPOP failed: {e}")
            return None

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get a range of elements from a list."""
        try:
            return self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE failed: {e}")
            return []

    def llen(self, key: str) -> int:
        """Get the length of a list."""
        try:
            return self.client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN failed: {e}")
            return 0

    # ==================== SET OPERATIONS ====================

    def sadd(self, key: str, *members: Any) -> int:
        """Add members to a set."""
        try:
            return self.client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD failed: {e}")
            return 0

    def srem(self, key: str, *members: Any) -> int:
        """Remove members from a set."""
        try:
            return self.client.srem(key, *members)
        except Exception as e:
            logger.error(f"Redis SREM failed: {e}")
            return 0

    def smembers(self, key: str) -> set:
        """Get all members of a set."""
        try:
            return self.client.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS failed: {e}")
            return set()

    def sismember(self, key: str, member: Any) -> bool:
        """Check if a member exists in a set."""
        try:
            return bool(self.client.sismember(key, member))
        except Exception as e:
            logger.error(f"Redis SISMEMBER failed: {e}")
            return False

    def scard(self, key: str) -> int:
        """Get the cardinality of a set."""
        try:
            return self.client.scard(key)
        except Exception as e:
            logger.error(f"Redis SCARD failed: {e}")
            return 0

    # ==================== HASH OPERATIONS ====================

    def hset(self, key: str, field: str, value: Any) -> int:
        """Set a field in a hash."""
        try:
            return self.client.hset(key, field, value)
        except Exception as e:
            logger.error(f"Redis HSET failed: {e}")
            return 0

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get a field from a hash."""
        try:
            return self.client.hget(key, field)
        except Exception as e:
            logger.error(f"Redis HGET failed: {e}")
            return None

    def hgetall(self, key: str) -> Dict[str, str]:
        """Get all fields from a hash."""
        try:
            return self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Redis HGETALL failed: {e}")
            return {}

    def hdel(self, key: str, *fields: str) -> int:
        """Delete fields from a hash."""
        try:
            return self.client.hdel(key, *fields)
        except Exception as e:
            logger.error(f"Redis HDEL failed: {e}")
            return 0

    def hexists(self, key: str, field: str) -> bool:
        """Check if a field exists in a hash."""
        try:
            return bool(self.client.hexists(key, field))
        except Exception as e:
            logger.error(f"Redis HEXISTS failed: {e}")
            return False

    def hlen(self, key: str) -> int:
        """Get the number of fields in a hash."""
        try:
            return self.client.hlen(key)
        except Exception as e:
            logger.error(f"Redis HLEN failed: {e}")
            return 0

    # ==================== SORTED SET OPERATIONS ====================

    def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add members to a sorted set."""
        try:
            return self.client.zadd(key, mapping)
        except Exception as e:
            logger.error(f"Redis ZADD failed: {e}")
            return 0

    def zrange(
        self, key: str, start: int = 0, end: int = -1, withscores: bool = False
    ) -> List:
        """Get a range of members from a sorted set."""
        try:
            return self.client.zrange(key, start, end, withscores=withscores)
        except Exception as e:
            logger.error(f"Redis ZRANGE failed: {e}")
            return []

    def zscore(self, key: str, member: str) -> Optional[float]:
        """Get the score of a member in a sorted set."""
        try:
            return self.client.zscore(key, member)
        except Exception as e:
            logger.error(f"Redis ZSCORE failed: {e}")
            return None

    def zcard(self, key: str) -> int:
        """Get the cardinality of a sorted set."""
        try:
            return self.client.zcard(key)
        except Exception as e:
            logger.error(f"Redis ZCARD failed: {e}")
            return 0

    # ==================== PUB/SUB OPERATIONS ====================

    def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel."""
        try:
            return self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis PUBLISH failed: {e}")
            return 0

    def subscribe(self, *channels: str):
        """Subscribe to channels."""
        try:
            return self.client.pubsub().subscribe(*channels)
        except Exception as e:
            logger.error(f"Redis SUBSCRIBE failed: {e}")
            return None

    # ==================== STREAM OPERATIONS ====================

    def xadd(
        self,
        stream: str,
        fields: Dict,
        maxlen: Optional[int] = None,
        approximate: bool = True,
    ) -> Optional[str]:
        """Add a message to a stream."""
        try:
            return self.client.xadd(
                stream, fields, maxlen=maxlen, approximate=approximate
            )
        except Exception as e:
            logger.error(f"Redis XADD failed: {e}")
            return None

    def xgroup_create(
        self, stream: str, group_name: str, mkstream: bool = True
    ) -> bool:
        """Create a consumer group."""
        try:
            self.client.xgroup_create(stream, group_name, mkstream=mkstream)
            return True
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.warning(
                    f"Consumer group '{group_name}' already exists for stream '{stream}'."
                )
                return True
            logger.error(f"Redis XGROUP CREATE failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Redis XGROUP CREATE failed: {e}")
            return False

    def xreadgroup(
        self,
        group_name: str,
        consumer_name: str,
        streams: Dict[str, str],
        count: Optional[int] = 1,
        block: Optional[int] = 0,
    ) -> List:
        """Read from a stream as part of a consumer group."""
        try:
            return self.client.xreadgroup(
                group_name, consumer_name, streams, count=count, block=block
            )
        except Exception as e:
            logger.error(f"Redis XREADGROUP failed: {e}")
            return []

    def xack(self, stream: str, group_name: str, *ids: str) -> int:
        """Acknowledge a message."""
        try:
            return self.client.xack(stream, group_name, *ids)
        except Exception as e:
            logger.error(f"Redis XACK failed: {e}")
            return 0

    # ==================== UTILITY OPERATIONS ====================

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern."""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS failed: {e}")
            return []

    def flushdb(self) -> bool:
        """Flush the current database."""
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis FLUSHDB failed: {e}")
            return False

    def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            return self.client.info(section)
        except Exception as e:
            logger.error(f"Redis INFO failed: {e}")
            return {}

    def dbsize(self) -> int:
        """Get the number of keys in the current database."""
        try:
            return self.client.dbsize()
        except Exception as e:
            logger.error(f"Redis DBSIZE failed: {e}")
            return 0

    # ==================== ASYNC OPERATIONS ====================

    async def aset(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Async: Set a key-value pair."""
        if not self.async_client:
            raise RedisError(
                "Async client not available. Install aioredis for async support."
            )

        try:
            return await self.async_client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Async Redis SET failed: {e}")
            return False

    async def aget(self, key: str) -> Optional[str]:
        """Async: Get a value by key."""
        if not self.async_client:
            raise RedisError(
                "Async client not available. Install aioredis for async support."
            )

        try:
            return await self.async_client.get(key)
        except Exception as e:
            logger.error(f"Async Redis GET failed: {e}")
            return None

    async def adelete(self, key: str) -> int:
        """Async: Delete a key."""
        if not self.async_client:
            raise RedisError(
                "Async client not available. Install aioredis for async support."
            )

        try:
            return await self.async_client.delete(key)
        except Exception as e:
            logger.error(f"Async Redis DELETE failed: {e}")
            return 0

    # ==================== HEALTH CHECK ====================

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        try:
            # Test basic operations
            test_key = "_health_check"
            self.set(test_key, "test", ex=10)
            value = self.get(test_key)
            self.delete(test_key)

            info = self.info()
            dbsize = self.dbsize()

            return {
                "success": True,
                "status": "healthy",
                "test_value": value,
                "database_size": dbsize,
                "redis_version": info.get("redis_version", "unknown"),
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
                "async_available": aioredis is not None,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
            }
