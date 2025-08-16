import pytest
from app.database import init_db
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_client():
    # Initialize the database before tests
    init_db()
    with TestClient(app) as client:
        yield client


def test_create_todo_endpoint_successful(test_client):
    todo_data = {
        "title": "API Test",
        "description": "Create via API",
        "completed": False,
    }
    response = test_client.post("/todos", json=todo_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == todo_data["title"]
    assert data["description"] == todo_data["description"]
    assert data["completed"] == todo_data["completed"]


def test_get_all_todos_endpoint(test_client):
    # Ensure there is at least one todo
    todo_data = {"title": "List Test", "description": "List desc"}
    test_client.post("/todos", json=todo_data)
    response = test_client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(todo["title"] == "List Test" for todo in data)


def test_get_todo_by_id_endpoint_existing_and_missing(test_client):
    todo_data = {"title": "GetById", "description": "Test desc"}
    post_resp = test_client.post("/todos", json=todo_data)
    todo_id = post_resp.json()["id"]
    # Existing
    resp = test_client.get(f"/todos/{todo_id}")
    assert resp.status_code == 200
    # Not existing
    resp_missing = test_client.get("/todos/999999")
    assert resp_missing.status_code == 404


def test_update_todo_endpoint_success_and_fail(test_client):
    todo_data = {"title": "UpdateTest", "description": "Desc"}
    post_resp = test_client.post("/todos", json=todo_data)
    todo_id = post_resp.json()["id"]

    update_data = {"title": "Updated Title", "completed": True}
    put_resp = test_client.put(f"/todos/{todo_id}", json=update_data)
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["title"] == "Updated Title"
    assert data["completed"] is True

    put_fail_resp = test_client.put("/todos/999999", json=update_data)
    assert put_fail_resp.status_code == 404


def test_delete_todo_endpoint_success_and_fail(test_client):
    # Create one
    todo_data = {"title": "DeleteTest"}
    post_resp = test_client.post("/todos", json=todo_data)
    todo_id = post_resp.json()["id"]
    del_resp = test_client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code == 204
    # Ensure deleted
    get_resp = test_client.get(f"/todos/{todo_id}")
    assert get_resp.status_code == 404

    del_fail_resp = test_client.delete("/todos/999999")
    assert del_fail_resp.status_code == 404
