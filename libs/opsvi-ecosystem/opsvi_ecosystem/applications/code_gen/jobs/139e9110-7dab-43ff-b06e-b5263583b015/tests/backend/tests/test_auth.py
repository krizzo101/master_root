"""
Unit tests for authentication module
"""
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_registration_and_login():
    r = client.post(
        "/auth/register",
        json={
            "email": "test@test.co",
            "password": "Pa$$w0rd",
            "full_name": "Test User",
        },
    )
    assert r.status_code == 200
    login = client.post(
        "/auth/login", data={"username": "test@test.co", "password": "Pa$$w0rd"}
    )
    assert login.status_code == 200
    data = login.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@test.co"
