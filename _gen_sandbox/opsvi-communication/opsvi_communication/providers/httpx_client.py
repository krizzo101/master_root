"""HTTPX async client wrapper for opsvi-communication."""
from typing import Any, Optional
import httpx

class HTTPXClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.post(url, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()
"""User model for opsvi-communication."""
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
