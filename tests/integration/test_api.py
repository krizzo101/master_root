import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.mark.asyncio
async def test_ask_endpoint(monkeypatch):
    async def mock_handle(query: str):
        return {
            "query": query,
            "answer": "Mock answer",
            "citations": [],
            "generation_ts": "2025-01-01T00:00:00Z",
            "audit_id": "test",
            "model_signature": "test"
        }

    from src.core import research_service as rs_module
    monkeypatch.setattr(rs_module.ResearchService, "handle_query", staticmethod(mock_handle))

    client = TestClient(app)
    resp = client.post("/ask", json={"query": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Mock answer"
