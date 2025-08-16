"""
Test API endpoints for collaborative editor backend.
"""
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_success():
    r = client.post(
        "/auth/token", data={"username": "testuser", "password": "password123"}
    )
    assert r.status_code == 200
    assert "access_token" in r.json()
    token = r.json()["access_token"]
    return token


def test_create_and_get_document():
    token = test_login_success()
    headers = {"Authorization": f"Bearer {token}"}
    cr = client.post(
        "/documents", data={"title": "Demo doc", "body": "Sample text"}, headers=headers
    )
    assert cr.status_code == 200
    doc = cr.json()
    gr = client.get(f"/documents/{doc['id']}", headers=headers)
    assert gr.status_code == 200
    assert gr.json()["body"] == "Sample text"


def test_search():
    token = test_login_success()
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/documents", data={"title": "UniqueSearchDoc", "body": "blah"}, headers=headers
    )
    res = client.get("/search?query=UniqueSearchDoc", headers=headers)
    assert res.status_code == 200
    results = res.json()
    assert any("UniqueSearchDoc" in d["title"] for d in results)
