# mypy: ignore-errors
"""OpenAIProvider with offline stub capability."""
from __future__ import annotations

import os
import random

from pydantic import BaseModel

OFFLINE = os.getenv("OFFLINE_MODE", "false").lower() == "true"

if not OFFLINE:
    from openai import AsyncOpenAI

from src.utils.config import get_settings  # noqa: E402


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]


class OpenAIProvider:
    def __init__(self) -> None:
        settings = get_settings()
        self.embedding_model = settings.model_embeddings
        if not OFFLINE:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_texts(self, texts: list[str]) -> EmbeddingResponse:  # noqa: D401
        """Return embeddings; offline mode returns random vectors for tests."""
        if OFFLINE:
            dim = 3072
            rng = random.Random(42)
            return EmbeddingResponse(embeddings=[[rng.random() for _ in range(dim)] for _ in texts])
        resp = await self.client.embeddings.create(model=self.embedding_model, input=texts)
        return EmbeddingResponse(embeddings=[d.embedding for d in resp.data])
