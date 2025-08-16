import pytest
from backend.db import engine
from backend.main import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    yield TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    # Ensure clean DB for each test
    from sqlmodel import SQLModel

    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


def test_register_and_login(client):
    response = client.post(
        "/api/users/", json={"username": "admin", "password": "pass1234"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "admin"

    response = client.post(
        "/api/token", data={"username": "admin", "password": "pass1234"}
    )
    assert response.status_code == 200, response.text
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

    # Auth fails for wrong user
    response = client.post(
        "/api/token", data={"username": "admin", "password": "badpass"}
    )
    assert response.status_code == 401


def test_registration_closed(client):
    client.post("/api/users/", json={"username": "admin", "password": "pw"})
    response = client.post("/api/users/", json={"username": "foo", "password": "pw2"})
    assert response.status_code == 400
