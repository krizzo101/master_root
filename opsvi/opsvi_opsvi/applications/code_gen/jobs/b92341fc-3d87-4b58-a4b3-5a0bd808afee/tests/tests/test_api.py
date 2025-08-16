import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_task():
    # Create Task
    payload = {
        "title": "Test Task",
        "description": "Description of the test task",
        "completed": False,
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["completed"] == payload["completed"]

    # Retrieve Task by ID
    task_id = data["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    task_data = response.json()
    assert task_data == data


def test_get_nonexistent_task():
    response = client.get("/tasks/999999")
    assert response.status_code == 404
    assert "error" in response.json()


def test_list_tasks():
    # Ensure at least one task exists
    payload = {"title": "List Task Usage"}
    client.post("/tasks", json=payload)
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(task["title"] == payload["title"] for task in data)


def test_update_task():
    payload = {"title": "Original Task", "description": "", "completed": False}
    create_resp = client.post("/tasks", json=payload)
    task_id = create_resp.json()["id"]
    update_payload = {"title": "Updated Task", "completed": True}
    response = client.put(f"/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_payload["title"]
    assert data["completed"] is True
    assert data["id"] == task_id


def test_update_nonexistent_task():
    response = client.put("/tasks/999999", json={"title": "Doesn't Exist"})
    assert response.status_code == 404
    assert "error" in response.json()


def test_delete_task():
    create_resp = client.post("/tasks", json={"title": "Delete Me"})
    task_id = create_resp.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    # Ensure task is gone
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


def test_delete_nonexistent_task():
    response = client.delete("/tasks/123456789")
    assert response.status_code == 404
    assert "error" in response.json()


def test_create_invalid_task():
    # No title
    payload = {"description": "No title"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422 or response.status_code == 400

    # Title too long
    payload = {"title": "x" * 201}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422 or response.status_code == 400

    # Completed field invalid
    payload = {"title": "Valid title", "completed": "not_bool"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_update_task_invalid_fields():
    create_resp = client.post("/tasks", json={"title": "Will Update Invalid"})
    task_id = create_resp.json()["id"]
    # Try to update with invalid title length
    resp = client.put(f"/tasks/{task_id}", json={"title": "x" * 201})
    assert resp.status_code == 422 or resp.status_code == 400
