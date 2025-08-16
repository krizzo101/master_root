"""
Tests for Todo List REST API endpoints and input validation.
"""
import pytest
from app.main import app
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_lifecycle():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        item_data = {
            "title": "Test Task",
            "description": "Make coffee",
            "completed": False,
        }
        # Create
        create_resp = await ac.post("/todos", json=item_data)
        assert create_resp.status_code == 201
        created = create_resp.json()["data"]
        assert created["title"] == "Test Task"
        assert created["description"] == "Make coffee"
        assert not created["completed"]
        todo_id = created["id"]

        # Get by ID
        get_resp = await ac.get(f"/todos/{todo_id}")
        assert get_resp.status_code == 200
        got = get_resp.json()
        assert got["id"] == todo_id
        assert got["title"] == "Test Task"

        # Partial update (patch)
        patch_resp = await ac.patch(f"/todos/{todo_id}", json={"completed": True})
        assert patch_resp.status_code == 200
        patched = patch_resp.json()
        assert patched["completed"]
        assert patched["title"] == "Test Task"

        # Update (put)
        update_resp = await ac.put(
            f"/todos/{todo_id}",
            json={
                "title": "Updated title",
                "description": "Updated desc",
                "completed": False,
            },
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["title"] == "Updated title"
        assert updated["description"] == "Updated desc"
        assert not updated["completed"]

        # List
        list_resp = await ac.get("/todos")
        assert list_resp.status_code == 200
        todos = list_resp.json()
        assert isinstance(todos, list)
        assert any(t["id"] == todo_id for t in todos)

        # Delete
        del_resp = await ac.delete(f"/todos/{todo_id}")
        assert del_resp.status_code == 200
        msg = del_resp.json()
        assert "deleted" in msg["message"].lower()

        # Get deleted -> 404
        get_del_resp = await ac.get(f"/todos/{todo_id}")
        assert get_del_resp.status_code == 404
        err = get_del_resp.json()
        assert "not found" in err["message"].lower()


@pytest.mark.asyncio
async def test_validation_and_errors():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Title required
        resp = await ac.post("/todos", json={"description": "xyz"})
        assert resp.status_code == 400
        body = resp.json()
        assert "validation error" in body["message"].lower()
        assert any("title" in detail for detail in body["details"])

        # Title must not be blank
        resp = await ac.post("/todos", json={"title": "   ", "description": "foo"})
        assert resp.status_code == 400
        assert "validation error" in resp.json()["message"].lower()

        # ID in path must be >0
        resp = await ac.get("/todos/0")
        assert resp.status_code == 422 or resp.status_code == 400

        # Update non-existent
        resp = await ac.put(
            "/todos/9999",
            json={"title": "foo", "description": "bar", "completed": False},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
