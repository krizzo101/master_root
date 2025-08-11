"""
Test suite for the FastAPI backend
"""
import os
import pytest
from fastapi.testclient import TestClient
from backend.app import app, issue_jwt, User
from unittest.mock import patch

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@patch("backend.app.get_db_connection")
def test_create_and_get_document(mock_db):
    # Setup fake user and JWT
    user = User(id="demo-uuid", email="demo@example.com")
    token = issue_jwt(user)
    # Mock DB connection/cursor
    mock_conn = mock_db.return_value
    mock_cursor = (
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value
    )
    # Simulate insert and fetch
    # Insert document
    mock_cursor.fetchone.return_value = [
        "demo-doc-id",
        "Test",
        "Some content",
        user.id,
        "2024-01-01T00:00:00Z",
        "2024-01-01T00:00:00Z",
        1,
    ]
    resp = client.post(
        "/api/documents",
        data={"title": "Test", "content": "Some content"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test"


@patch("backend.app.get_db_connection")
def test_document_list(mock_db):
    user = User(id="demo-uuid", email="demo@example.com")
    token = issue_jwt(user)
    mock_conn = mock_db.return_value
    mock_cursor = (
        mock_conn.__enter__.return_value.cursor.return_value.__enter__.return_value
    )
    mock_cursor.fetchall.return_value = [
        [
            "doc-1",
            "Doc 1",
            "abc",
            user.id,
            "2024-01-01T00:00:00Z",
            "2024-01-02T00:00:00Z",
            1,
        ]
    ]
    resp = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    docs = resp.json()
    assert isinstance(docs, list)
    assert docs[0]["title"] == "Doc 1"


def test_jwt_unauthorized():
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Not authenticated."
