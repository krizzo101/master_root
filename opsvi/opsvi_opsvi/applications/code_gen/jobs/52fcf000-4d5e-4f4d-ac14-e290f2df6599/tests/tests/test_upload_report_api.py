from app.main import app
from fastapi.testclient import TestClient


def get_token_and_project(client):
    client.post(
        "/auth/signup",
        json={
            "username": "testup",
            "email": "testup@test.com",
            "password": "password12345",
        },
    )
    resp = client.post(
        "/auth/token", data={"username": "testup@test.com", "password": "password12345"}
    )
    token = resp.json()["access_token"]
    resp = client.post(
        "/api/projects",
        json={"name": "UpProj", "description": "Upload test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = resp.json()["id"]
    return token, pid


def test_upload_code_and_report():
    client = TestClient(app)
    token, pid = get_token_and_project(client)
    hdrs = {"Authorization": f"Bearer {token}"}
    py_content = b"def foo():\n  return 42\n"
    resp = client.post(
        f"/api/projects/{pid}/upload",
        files={"file": ("foo.py", py_content)},
        headers=hdrs,
    )
    assert resp.status_code == 200
    # List reports (should be at least one, status pending)
    resp = client.get(f"/api/projects/{pid}/reports", headers=hdrs)
    assert resp.status_code == 200
    reports = resp.json()
    assert any(r["status"] in ("pending", "in_progress", "completed") for r in reports)
