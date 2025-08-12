import os

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_env():
    # Set dummy API keys for testing
    os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
    os.environ["HF_API_KEY"] = "DUMMY_KEY"


def test_healthz():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_summarize_short():
    payload = {"content": "Too short"}
    resp = client.post("/summarize", json=payload)
    assert resp.status_code == 422  # Fails validation due to min length


def test_summarize_success(monkeypatch):
    def mock_summarize_with_openai(content, language):
        return "summary here"

    monkeypatch.setattr("main.summarize_with_openai", lambda x, y: "summary here")
    payload = {"content": "This is a sufficiently long document for summarization."}
    resp = client.post("/summarize", json=payload)
    assert resp.status_code == 200
    assert resp.json()["summary"] == "summary here"


def test_suggest_success(monkeypatch):
    monkeypatch.setattr("main.suggest_with_openai", lambda x, y: "suggestion here")
    payload = {"content": "This document could be improved."}
    resp = client.post("/suggest", json=payload)
    assert resp.status_code == 200
    assert resp.json()["suggestions"] == "suggestion here"


def test_summarize_fallback(monkeypatch):
    # Remove OpenAI key, fallback to HuggingFace (simulate)
    os.environ["OPENAI_API_KEY"] = ""

    def mock_post(*args, **kwargs):
        class DummyResp:
            def raise_for_status(self):
                pass

            def json(self):
                return [{"summary_text": "fake summary"}]

        return DummyResp()

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    payload = {"content": "This is a sufficiently long document for summarization."}
    resp = client.post("/summarize", json=payload)
    assert resp.status_code == 200
    assert isinstance(resp.json()["summary"], str)
