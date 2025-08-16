"""Redis persistence backend."""

import json
import logging
from typing import Any, Dict, List, Optional

from .base import PersistenceBackend, PersistenceError

logger = logging.getLogger(__name__)

# Try to import redis, but make it optional
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis library not available, RedisBackend will be stubbed")


class RedisBackend(PersistenceBackend):
    """Redis persistence backend."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Redis backend.

        Args:
            config: Configuration with 'host', 'port', 'db', 'password' etc.
        """
        super().__init__(config)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 6379)
        self.db = self.config.get("db", 0)
        self.password = self.config.get("password")
        self.key_prefix = self.config.get("key_prefix", "opsvi:")
        self.client = None

    async def _initialize_impl(self) -> None:
        """Initialize Redis backend."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using stub implementation")
            return
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                encoding="utf-8",
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}/{self.db}")
        except Exception as e:
            raise PersistenceError(f"Failed to connect to Redis: {e}")

    async def _shutdown_impl(self) -> None:
        """Shutdown Redis backend."""
        if self.client:
            await self.client.aclose()
            logger.info("Disconnected from Redis")

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    def _strip_prefix(self, key: str) -> str:
        """Remove prefix from key."""
        if key.startswith(self.key_prefix):
            return key[len(self.key_prefix):]
        return key

    def _serialize(self, value: Any) -> str:
        """Serialize value to string."""
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from string."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value by key."""
        if not self.client:
            return default
        
        try:
            value = await self.client.get(self._make_key(key))
            if value is None:
                return default
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return default

    async def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        if not self.client:
            return
        
        try:
            serialized = self._serialize(value)
            ttl = self.config.get("ttl")
            
            if ttl:
                await self.client.setex(self._make_key(key), ttl, serialized)
            else:
                await self.client.set(self._make_key(key), serialized)
        except Exception as e:
            raise PersistenceError(f"Failed to set key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value by key."""
        if not self.client:
            return False
        
        try:
            result = await self.client.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.client:
            return False
        
        try:
            return await self.client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.error(f"Failed to check key {key}: {e}")
            return False

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        if not self.client:
            return []
        
        try:
            search_pattern = self._make_key(pattern or "*")
            keys = await self.client.keys(search_pattern)
            return [self._strip_prefix(k) for k in keys]
        except Exception as e:
            logger.error(f"Failed to get keys: {e}")
            return []

    async def clear(self) -> None:
        """Clear all stored data."""
        if not self.client:
            return
        
        try:
            keys = await self.client.keys(self._make_key("*"))
            if keys:
                await self.client.delete(*keys)
            logger.info(f"Cleared {len(keys)} keys from Redis")
        except Exception as e:
            raise PersistenceError(f"Failed to clear data: {e}")

    async def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs."""
        if not self.client:
            return {}
        
        try:
            result = {}
            keys = await self.keys()
            
            if keys:
                # Use pipeline for efficiency
                pipe = self.client.pipeline()
                for key in keys:
                    pipe.get(self._make_key(key))
                values = await pipe.execute()
                
                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = self._deserialize(value)
            
            return result
        except Exception as e:
            logger.error(f"Failed to get all data: {e}")
            return {}

    async def set_many(self, data: Dict[str, Any]) -> None:
        """Set multiple key-value pairs."""
        if not self.client:
            return
        
        try:
            # Use pipeline for efficiency
            pipe = self.client.pipeline()
            ttl = self.config.get("ttl")
            
            for key, value in data.items():
                serialized = self._serialize(value)
                if ttl:
                    pipe.setex(self._make_key(key), ttl, serialized)
                else:
                    pipe.set(self._make_key(key), serialized)
            
            await pipe.execute()
        except Exception as e:
            raise PersistenceError(f"Failed to set multiple keys: {e}")

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key."""
        if not self.client:
            return False
        
        try:
            return await self.client.expire(self._make_key(key), seconds)
        except Exception as e:
            logger.error(f"Failed to set expiration for {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self.client:
            return -1
        
        try:
            return await self.client.ttl(self._make_key(key))
        except Exception as e:
            logger.error(f"Failed to get TTL for {key}: {e}")
            return -1


# Stub implementation when Redis is not available
class RedisBackendStub(PersistenceBackend):
    """Stub Redis backend when redis library is not available."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._data: Dict[str, Any] = {}
    
    async def _initialize_impl(self) -> None:
        logger.warning("Using Redis stub - install redis library for actual Redis support")
    
    async def _shutdown_impl(self) -> None:
        pass
    
    async def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
    
    async def set(self, key: str, value: Any) -> None:
        self._data[key] = value
    
    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return key in self._data
    
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        if pattern:
            import fnmatch
            return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]
        return list(self._data.keys())
    
    async def clear(self) -> None:
        self._data.clear()
    
    async def get_all(self) -> Dict[str, Any]:
        return self._data.copy()
    
    async def set_many(self, data: Dict[str, Any]) -> None:
        self._data.update(data)


# Export the appropriate class
if not REDIS_AVAILABLE:
    RedisBackend = RedisBackendStub


__all__ = ["RedisBackend"]