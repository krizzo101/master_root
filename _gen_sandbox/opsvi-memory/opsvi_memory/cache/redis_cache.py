"""Redis cache provider for opsvi-memory using redis.asyncio."""
from typing import Optional
import os
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
        self._client: Optional[Redis] = None

    async def connect(self) -> bool:
        self._client = Redis.from_url(self.url, encoding="utf-8", decode_responses=True)
        try:
            await self._client.ping()
            return True
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Optional[str]:
        if self._client is None:
            ok = await self.connect()
            if not ok:
                return None
        return await self._client.get(key)  # type: ignore

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self._client is None:
            ok = await self.connect()
            if not ok:
                return False
        return bool(await self._client.set(key, value, ex=ex))  # type: ignore
