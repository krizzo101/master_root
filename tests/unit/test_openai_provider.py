import os

import pytest

os.environ["OFFLINE_MODE"] = "true"
from src.providers.openai_provider import OpenAIProvider  # noqa: E402


@pytest.mark.asyncio
async def test_openai_provider_offline():
    provider = OpenAIProvider()
    emb = await provider.embed_texts(["hello world"])
    assert len(emb.embeddings) == 1
    assert len(emb.embeddings[0]) == 3072
