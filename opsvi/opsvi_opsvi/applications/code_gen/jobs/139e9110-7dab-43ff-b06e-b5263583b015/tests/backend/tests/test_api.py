"""
API CRUD smoke tests - project and task
"""
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_project_and_task():
    # Register a user
    r = client.post(
        "/auth/register",
        json={
            "email": "api@test.me",
            "password": "apiAPI123",
            "full_name": "API Tester",
        },
    )
    assert r.status_code == 200
    login = client.post(
        "/auth/login", data={"username": "api@test.me", "password": "apiAPI123"}
    )
    token = login.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    pr = client.post(
        "/api/projects", json={"name": "Proj1", "description": "desc"}, headers=h
    )
    assert pr.status_code == 200
    pid = pr.json()["id"]
    ta = client.post(
        f"/api/projects/{pid}/tasks", json={"title": "T1", "description": ""}, headers=h
    )
    assert ta.status_code == 200
    assert "id" in ta.json()
