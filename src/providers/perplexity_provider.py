# mypy: ignore-errors
"""PerplexityProvider with offline stub capability."""
from __future__ import annotations

import os
import json

from pydantic import BaseModel

from src.utils.config import get_settings
from src.utils.http_client import HTTPClient

OFFLINE = os.getenv("OFFLINE_MODE", "false").lower() == "true"


class SearchResult(BaseModel):
    url: str
    snippet: str | None = None
    title: str | None = None


class PerplexityProvider:
    BASE_URL = "https://api.perplexity.ai/chat/completions"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def search(self, query: str, k: int = 10) -> list[SearchResult]:  # noqa: D401
        if OFFLINE:
            return [
                SearchResult(
                    url="https://example.com",
                    snippet="Example snippet",
                    title="Example",
                )
            ]

        headers = {
            "Authorization": f"Bearer {self.settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 1000,
        }

        print(
            f"Making request to Perplexity API with data: {json.dumps(data, indent=2)}"
        )

        try:
            response = await HTTPClient.post_json(
                self.BASE_URL, headers=headers, json=data
            )
            print(f"Perplexity API response: {json.dumps(response, indent=2)}")

            # Extract content from the response
            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )

            # For now, return a single result with the content
            return [
                SearchResult(
                    url="https://perplexity.ai",
                    snippet=content,
                    title="Perplexity Research Result",
                )
            ]
        except Exception as e:
            print(f"Error calling Perplexity API: {e}")
            # Return offline result as fallback
            return [
                SearchResult(
                    url="https://example.com",
                    snippet=f"Research query: {query}. API call failed, using offline mode.",
                    title="Offline Research Result",
                )
            ]
