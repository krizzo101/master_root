import pytest
from app import ai


@pytest.mark.asyncio
async def test_ai_summary():
    body = "The sky is blue. The sun is bright."
    res = await ai.summarize(body)
    assert "Summary" in res["summary"]
    assert "sky is blue" in res["summary"]


@pytest.mark.asyncio
async def test_ai_suggestion():
    body = "This is some text."
    res = await ai.suggest(body)
    assert isinstance(res["suggestion"], str) and len(res["suggestion"]) > 0
