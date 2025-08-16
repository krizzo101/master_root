"""
Unit and integration tests for the AI FastAPI service.
"""
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_summarize_success(monkeypatch):
    class DummySummarizer:
        def __call__(self, text, max_length, min_length, do_sample):
            # Return a mock summary
            return [{"summary_text": "Mock summary."}]

    app.state.summarizer = DummySummarizer()
    resp = client.post(
        "/summarize",
        json={
            "text": "A" * 100,  # 100 chars
            "max_summary_length": 40,
            "min_summary_length": 10,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Mock summary."


def test_summarize_validation():
    # Text too short for summarization
    resp = client.post("/summarize", json={"text": "Too short text."})
    assert resp.status_code == 422


def test_suggest_success(monkeypatch):
    class DummySuggester:
        def __call__(self, prompt, max_length, num_return_sequences):
            return [
                {"generated_text": prompt + " suggestion 1"},
                {"generated_text": prompt + " suggestion 2"},
            ]

    app.state.suggester = DummySuggester()
    resp = client.post("/suggest", json={"prompt": "Sample prompt"})
    assert resp.status_code == 200
    suggestions = resp.json()["suggestions"]
    assert any("suggestion 1" in s for s in suggestions)
    assert any("suggestion 2" in s for s in suggestions)


def test_suggest_validation():
    # Empty prompt
    resp = client.post("/suggest", json={"prompt": ""})
    assert resp.status_code == 422
