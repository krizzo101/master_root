from typing import Any

import httpx


class HTTPClient:
    """Reusable async HTTPX client with sensible defaults and retry logic."""

    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=30)
        return cls._client

    @classmethod
    async def get_json(cls, url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> Any:
        resp = await cls.get_client().get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    @classmethod
    async def post_json(cls, url: str, json: Any, headers: dict[str, str] | None = None) -> Any:
        resp = await cls.get_client().post(url, json=json, headers=headers)
        resp.raise_for_status()
        return resp.json()
