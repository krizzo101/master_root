import pytest
from fastapi.testclient import TestClient
from app.main import app


def get_token(client):
    client.post(
        "/auth/signup",
        json={
            "username": "testp1",
            "email": "tp1@test.com",
            "password": "passw0rdpass",
        },
    )
    resp = client.post(
        "/auth/token", data={"username": "tp1@test.com", "password": "passw0rdpass"}
    )
    return resp.json()["access_token"]


def test_create_and_list_projects():
    client = TestClient(app)
    token = get_token(client)
    hdrs = {"Authorization": f"Bearer {token}"}
    # Create
    p = {"name": "Test Project", "description": "First"}
    resp = client.post("/api/projects", json=p, headers=hdrs)
    assert resp.status_code == 200
    pid = resp.json()["id"]
    # List
    resp = client.get("/api/projects", headers=hdrs)
    assert resp.status_code == 200
    found = [p for p in resp.json() if p["id"] == pid]
    assert found
    # Update
    up = {"name": "Updated Name"}
    resp = client.put(f"/api/projects/{pid}", json=up, headers=hdrs)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"
    # Delete
    resp = client.delete(f"/api/projects/{pid}", headers=hdrs)
    assert resp.status_code == 200
    # Confirm gone
    resp = client.get(f"/api/projects/{pid}", headers=hdrs)
    assert resp.status_code == 404
