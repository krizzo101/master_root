import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers import todo as todo_router
from app.services.todo_service import InMemoryTodoStore, TodoService
from app.models.todo import TodoItemCreate, TodoItemUpdate


@pytest.fixture
def test_app():
    app = FastAPI()
    store = InMemoryTodoStore()
    service = TodoService(store=store)
    app.include_router(todo_router.router)

    # Dependency override to inject our test service
    from app.routers import todo as todo_mod

    def override_get_todo_service():
        return service

    app.dependency_overrides[todo_mod.get_todo_service] = override_get_todo_service

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
def sample_todo_create():
    return {
        "title": "Test Todo API",
        "description": "API test item",
        "completed": False,
    }


def test_create_todo_item_endpoint_success(client, sample_todo_create):
    response = client.post("/todos", json=sample_todo_create)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == sample_todo_create["title"]


def test_get_all_todos_returns_list(client, sample_todo_create):
    client.post("/todos", json=sample_todo_create)
    response = client.get("/todos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(todo["title"] == sample_todo_create["title"] for todo in data)


def test_get_single_todo_by_id(client, sample_todo_create):
    post_resp = client.post("/todos", json=sample_todo_create)
    item_id = post_resp.json()["id"]

    get_resp = client.get(f"/todos/{item_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == item_id

    missing_resp = client.get("/todos/999999")
    assert missing_resp.status_code == 404


def test_update_todo_put_and_patch(client, sample_todo_create):
    post_resp = client.post("/todos", json=sample_todo_create)
    item_id = post_resp.json()["id"]

    # PUT with full data
    update_data = {
        "title": "Updated Title",
        "description": "Updated desc",
        "completed": True,
    }
    put_resp = client.put(f"/todos/{item_id}", json=update_data)
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["title"] == "Updated Title"
    assert data["completed"] is True

    # PATCH partial update
    patch_data = {"completed": False}
    patch_resp = client.patch(f"/todos/{item_id}", json=patch_data)
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert patched["completed"] is False


def test_delete_todo_item_success_and_404(client, sample_todo_create):
    post_resp = client.post("/todos", json=sample_todo_create)
    item_id = post_resp.json()["id"]

    delete_resp = client.delete(f"/todos/{item_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert "message" in data

    # Confirm deletion
    get_resp = client.get(f"/todos/{item_id}")
    assert get_resp.status_code == 404

    # Delete non-existent
    del_resp = client.delete("/todos/999999")
    assert del_resp.status_code == 404


def test_create_todo_invalid_blank_title(client):
    invalid_data = {"title": " ", "description": "desc", "completed": False}
    resp = client.post("/todos", json=invalid_data)
    assert resp.status_code == 422
    data = resp.json()
    # Should indicate validation error on title
    assert any(err["loc"][-1] == "title" for err in data["detail"])


def test_update_todo_invalid_title_returns_422(client, sample_todo_create):
    post_resp = client.post("/todos", json=sample_todo_create)
    item_id = post_resp.json()["id"]

    invalid_update = {"title": "  "}
    resp = client.put(f"/todos/{item_id}", json=invalid_update)
    assert resp.status_code == 422

    resp_patch = client.patch(f"/todos/{item_id}", json=invalid_update)
    assert resp_patch.status_code == 422
