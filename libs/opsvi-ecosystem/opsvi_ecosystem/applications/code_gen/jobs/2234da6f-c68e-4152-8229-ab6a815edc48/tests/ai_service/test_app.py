import pytest
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.mark.skipif(
    not app.openapi().get("info", {}).get("title"),
    reason="OpenAI API key must be set for tests to run.",
)
def test_summarize_success(monkeypatch):
    # Mock openai.ChatCompletion.create
    def mock_create(*args, **kwargs):
        class MockCompletion:
            @staticmethod
            def __getitem__(key):
                return (
                    [{"message": {"content": "Summary: hello world."}}][0]
                    if key == "choices"
                    else None
                )

        return MockCompletion()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_create)
    response = client.post(
        "/summarize", json={"text": "This is a long document. Hello world!"}
    )
    assert response.status_code == 200
    assert "summary" in response.json()
    assert response.json()["summary"].startswith("Summary")


def test_suggest_success(monkeypatch):
    # Mock openai.ChatCompletion.create
    def mock_create(*args, **kwargs):
        class MockCompletion:
            @staticmethod
            def __getitem__(key):
                return (
                    [
                        {
                            "message": {
                                "content": "- Suggestion A\n- Suggestion B\n- Suggestion C"
                            }
                        }
                    ][0]
                    if key == "choices"
                    else None
                )

        return MockCompletion()

    monkeypatch.setattr("openai.ChatCompletion.create", mock_create)
    response = client.post("/suggest", json={"text": "The document is about AI."})
    assert response.status_code == 200
    assert "suggestions" in response.json()
    assert len(response.json()["suggestions"]) == 3


def test_summarize_missing_key(monkeypatch):
    monkeypatch.setattr("openai.api_key", None)
    response = client.post("/summarize", json={"text": "Test."})
    assert response.status_code == 500


def test_suggest_missing_key(monkeypatch):
    monkeypatch.setattr("openai.api_key", None)
    response = client.post("/suggest", json={"text": "Test."})
    assert response.status_code == 500


def test_summarize_bad_request():
    response = client.post("/summarize", json={})
    assert response.status_code == 422


def test_suggest_bad_request():
    response = client.post("/suggest", json={})
    assert response.status_code == 422
