import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function", autouse=True)
def clear_db():
    # Clean up the DB before each test for isolation.
    from app.database import SessionLocal, Base, engine
    from sqlalchemy.orm import close_all_sessions

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    close_all_sessions()
    yield


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_todo():
    data = {"title": "Do homework", "description": "Math and Science"}
    response = client.post("/todos", json=data)
    assert response.status_code == 201
    json = response.json()
    assert json["title"] == "Do homework"
    assert json["description"] == "Math and Science"
    assert isinstance(json["id"], int)


def test_list_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_todos():
    # Add two todos
    client.post("/todos", json={"title": "A", "description": "D1"})
    client.post("/todos", json={"title": "B", "description": "D2"})
    response = client.get("/todos")
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 2
    assert todos[0]["title"] == "A"
    assert todos[1]["title"] == "B"


def test_get_todo_by_id():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "A"
    assert response.json()["description"] == "B"


def test_get_todo_not_found():
    response = client.get("/todos/999")
    assert response.status_code == 404


def test_update_todo_patch():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    patch = client.patch(f"/todos/{todo_id}", json={"title": "Z"})
    assert patch.status_code == 200
    assert patch.json()["title"] == "Z"
    assert patch.json()["description"] == "B"


def test_update_todo_patch_not_found():
    response = client.patch("/todos/11111", json={"title": "T"})
    assert response.status_code == 404


def test_replace_todo_put():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    put = client.put(f"/todos/{todo_id}", json={"title": "X", "description": "Y"})
    assert put.status_code == 200
    assert put.json()["title"] == "X"
    assert put.json()["description"] == "Y"


def test_replace_todo_not_found():
    response = client.put("/todos/98765", json={"title": "Z", "description": "Q"})
    assert response.status_code == 404


def test_delete_todo():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    delete = client.delete(f"/todos/{todo_id}")
    assert delete.status_code == 204
    # Should be gone now
    getagain = client.get(f"/todos/{todo_id}")
    assert getagain.status_code == 404


def test_delete_todo_not_found():
    response = client.delete("/todos/99999")
    assert response.status_code == 404


def test_create_invalid_payload():
    resp = client.post("/todos", json={"title": "", "description": "   "})
    assert resp.status_code == 422 or resp.status_code == 400


def test_patch_invalid_payload():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    # Empty title
    patch = client.patch(f"/todos/{todo_id}", json={"title": " ", "description": "C"})
    assert patch.status_code == 422 or patch.status_code == 400


def test_put_invalid_payload():
    create = client.post("/todos", json={"title": "A", "description": "B"})
    todo_id = create.json()["id"]
    put = client.put(f"/todos/{todo_id}", json={"title": "", "description": "D"})
    assert put.status_code == 422 or put.status_code == 400
