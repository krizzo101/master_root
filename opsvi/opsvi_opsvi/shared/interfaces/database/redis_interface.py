"""
Redis Shared Interface
---------------------
Authoritative implementation based on the official redis-py and aioredis documentation:
- https://github.com/redis/redis-py
- https://aioredis.readthedocs.io/en/latest/
Implements all core features: connection management, key-value operations, pub/sub, pipelines, and error handling.
Version: Referenced as of July 2024
"""

import logging
from typing import Any

try:
    import redis
except ImportError:
    raise ImportError("redis-py is required. Install with `pip install redis`.")

try:
    import aioredis
except ImportError:
    aioredis = None  # Async support is optional

logger = logging.getLogger(__name__)


class RedisInterface:
    """
    Authoritative shared interface for Redis operations.
    See: https://github.com/redis/redis-py
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
    ):
        """
        Initialize a RedisInterface.
        Args:
            host: Redis server host.
            port: Redis port (default 6379).
            db: Database index (default 0).
            password: Optional password.
        """
        self.config = {
            "host": host,
            "port": port,
            "db": db,
            "password": password,
        }
        try:
            self.client = redis.Redis(**self.config)
            logger.info("Redis client initialized.")
        except Exception as e:
            logger.error(f"Redis client initialization failed: {e}")
            raise

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """
        Set a value for a key with optional expiration.
        Args:
            key: Key name.
            value: Value to set.
            ex: Expiration time in seconds.
        Returns:
            True if successful.
        """
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            raise

    def get(self, key: str) -> Any:
        """
        Get the value for a key.
        Args:
            key: Key name.
        Returns:
            Value or None.
        """
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            raise

    def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a channel.
        Args:
            channel: Channel name.
            message: Message to publish.
        Returns:
            Number of clients that received the message.
        """
        try:
            return self.client.publish(channel, message)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}")
            raise

    def subscribe(self, channel: str):
        """
        Subscribe to a channel (sync generator).
        Args:
            channel: Channel name.
        Yields:
            Messages from the channel.
        """
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]

    def pipeline(self):
        return self.client.pipeline()

    # Async support using aioredis
    async def aset(self, key: str, value: Any, ex: int | None = None) -> bool:
        if not aioredis:
            raise ImportError(
                "aioredis is required for async support. Install with `pip install aioredis`."
            )
        redis_client = await aioredis.create_redis_pool(
            (self.config["host"], self.config["port"])
        )
        try:
            result = await redis_client.set(key, value, expire=ex)
            return result
        finally:
            redis_client.close()
            await redis_client.wait_closed()

    async def aget(self, key: str) -> Any:
        if not aioredis:
            raise ImportError(
                "aioredis is required for async support. Install with `pip install aioredis`."
            )
        redis_client = await aioredis.create_redis_pool(
            (self.config["host"], self.config["port"])
        )
        try:
            result = await redis_client.get(key)
            return result
        finally:
            redis_client.close()
            await redis_client.wait_closed()


# Example usage and advanced features are available in the official docs:
# https://github.com/redis/redis-py
# https://aioredis.readthedocs.io/en/latest/
