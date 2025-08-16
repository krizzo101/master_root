import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Base
from app.database import get_db

# Use a separate in-memory SQLite database for tests
test_db_url = "sqlite:///:memory:"
engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override get_db dependency in FastAPI app
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_todo():
    payload = {"title": "Test Task", "description": "Test Desc", "completed": False}
    response = client.post("/api/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Desc"
    assert data["completed"] is False
    assert "id" in data
    global created_todo_id
    created_todo_id = data["id"]


def test_create_todo_with_min_fields():
    payload = {"title": "Only Title"}
    response = client.post("/api/todos/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Only Title"
    assert data["description"] is None
    assert data["completed"] is False


def test_get_all_todos():
    response = client.get("/api/todos/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_todo_by_id():
    response = client.get(f"/api/todos/{created_todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_todo_id
    assert data["title"] == "Test Task"


def test_update_todo():
    payload = {"description": "Updated Desc", "completed": True}
    response = client.put(f"/api/todos/{created_todo_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["description"] == "Updated Desc"


def test_update_nonexistent_todo():
    response = client.put("/api/todos/9999", json={"title": "X"})
    assert response.status_code == 404


def test_delete_todo():
    response = client.delete(f"/api/todos/{created_todo_id}")
    assert response.status_code == 204


def test_delete_nonexistent_todo():
    response = client.delete("/api/todos/9999")
    assert response.status_code == 404


def test_get_deleted_todo():
    response = client.get(f"/api/todos/{created_todo_id}")
    assert response.status_code == 404
