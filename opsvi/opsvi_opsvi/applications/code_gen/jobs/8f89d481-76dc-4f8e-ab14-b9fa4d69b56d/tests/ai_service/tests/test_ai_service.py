"""
Pytest-based test suite for AI service endpoints.
Mocks inference pipelines for speed and predictability.
"""
from unittest.mock import patch

import pytest
from ai_service.main import app
from fastapi.testclient import TestClient

DUMMY_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6MTk0MTA4Mzg5MH0.TD-7Df7Bn2Dkt4LnOA31jzR_VOXhxEDjvOLx28Lpvh8"


@pytest.fixture
def client():
    return TestClient(app)


@patch("ai_service.main.get_summarizer")
def test_summarize_success(mock_get_sum, client):
    mock_get_sum.return_value = lambda text, **kwargs: [
        {"summary_text": "Short summary."}
    ]
    resp = client.post(
        "/summarize",
        headers={"Authorization": f"Bearer {DUMMY_JWT}"},
        json={"text": "This is a long enough string to summarize." * 2},
    )
    assert resp.status_code == 200
    assert "summary" in resp.json()
    assert resp.json()["summary"] == "Short summary."


@patch("ai_service.main.get_suggestion_generator")
def test_suggest_success(mock_get_sugg, client):
    mock_get_sugg.return_value = lambda prompt, **kwargs: [
        {
            "generated_text": "• Revise the intro.\n• Fix grammar.\n• Clarify the conclusion."
        }
    ]
    resp = client.post(
        "/suggest",
        headers={"Authorization": f"Bearer {DUMMY_JWT}"},
        json={"text": "A meaningful document text that can receive AI suggestions."},
    )
    assert resp.status_code == 200
    js = resp.json()
    assert "suggestions" in js
    assert len(js["suggestions"]) >= 3


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("/summarize", {"text": "Too short"}),
        ("/suggest", {"text": "Tiny"}),
    ],
)
def test_input_too_short(client, endpoint, payload):
    resp = client.post(
        endpoint, headers={"Authorization": f"Bearer {DUMMY_JWT}"}, json=payload
    )
    assert resp.status_code == 422
    js = resp.json()
    assert "detail" in js


def test_unauthorized(client):
    resp = client.post("/summarize", json={"text": "x" * 80})
    assert resp.status_code == 403 or resp.status_code == 401


# Health check endpoint


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
