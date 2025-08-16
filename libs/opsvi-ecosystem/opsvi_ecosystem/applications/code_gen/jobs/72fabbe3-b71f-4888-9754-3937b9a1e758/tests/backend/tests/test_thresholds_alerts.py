import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import engine
from sqlmodel import Session
from backend.models import Threshold
from datetime import datetime
import time

@pytest.fixture()
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def get_token(client):
    client.post("/api/users/", json={"username": "test", "password": "p"})
    r = client.post("/api/token", data={"username": "test", "password": "p"})
    return r.json()["access_token"]

def test_get_update_thresholds(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    # Get
    resp = client.get("/api/thresholds", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for k in ("cpu", "memory", "disk", "network"):
        assert k in data
    # Update
data2 = {"cpu": 93.0, "network": 60000000.0}
    resp = client.put("/api/thresholds", json=data2, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["cpu"] == 93.0
    assert updated["network"] == 60000000.0

def test_alerts_api(client, get_token):
    headers = {"Authorization": f"Bearer {get_token}"}
    resp = client.get("/api/alerts", headers=headers)
    assert resp.status_code == 200
    # Just checks API reachable, real alerts need live system metric trigger
