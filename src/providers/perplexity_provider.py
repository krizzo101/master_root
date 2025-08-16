# mypy: ignore-errors
"""PerplexityProvider with offline stub capability."""
from __future__ import annotations

import os

from pydantic import BaseModel

from src.utils.config import get_settings
from src.utils.http_client import HTTPClient

OFFLINE = os.getenv("OFFLINE_MODE", "false").lower() == "true"


class SearchResult(BaseModel):
    url: str
    snippet: str | None = None
    title: str | None = None


class PerplexityProvider:
    BASE_URL = "https://api.perplexity.ai/search"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, query: str, k: int = 10) -> list[SearchResult]:  # noqa: D401
        if OFFLINE:
            return [
                SearchResult(url="https://example.com", snippet="Example snippet", title="Example")
            ]
        headers = {"Authorization": f"Bearer {self.settings.perplexity_api_key}"}
        params = {"q": query, "num_results": k}
        data = await HTTPClient.get_json(self.BASE_URL, headers=headers, params=params)
        return [SearchResult(**item) for item in data.get("results", [])]
