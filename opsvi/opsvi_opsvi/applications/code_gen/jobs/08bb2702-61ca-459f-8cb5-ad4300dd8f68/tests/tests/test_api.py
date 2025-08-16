"""
Integration tests for Task Management API endpoints.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.database import init_db
import asyncio
import os


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """
    Overwrite pytest-asyncio event loop for session scope.
    """
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(autouse=True, scope="session")
async def setup_database():
    # Remove SQLite file to start fresh
    db_file = "tasks.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    await init_db()
    yield
    # After tests, cleanup
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_crud_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Create a new task
        payload = {"title": "Test Task", "description": "Test Description"}
        resp = await ac.post("/tasks/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == payload["title"]
        assert data["is_completed"] is False
        task_id = data["id"]

        # 2. List tasks
        resp = await ac.get("/tasks/")
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]
        assert len(tasks) == 1

        # 3. Get task by id
        resp = await ac.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        tdata = resp.json()
        assert tdata["id"] == task_id
        assert tdata["title"] == payload["title"]

        # 4. Update (PATCH) task
        patch_payload = {"description": "Updated Desc", "is_completed": True}
        resp = await ac.patch(f"/tasks/{task_id}", json=patch_payload)
        assert resp.status_code == 200
        tdata = resp.json()
        assert tdata["description"] == "Updated Desc"
        assert tdata["is_completed"] is True

        # 5. Update (PUT) task
        put_payload = {"title": "Replaced Task", "is_completed": False}
        resp = await ac.put(f"/tasks/{task_id}", json=put_payload)
        assert resp.status_code == 200
        tdata = resp.json()
        assert tdata["title"] == "Replaced Task"
        assert tdata["is_completed"] is False

        # 6. Delete task
        resp = await ac.delete(f"/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Task deleted successfully."

        # 7. Confirm deletion
        resp = await ac.get(f"/tasks/{task_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found."

        # 8. List tasks after deletion
        resp = await ac.get("/tasks/")
        assert resp.status_code == 200
        assert resp.json()["tasks"] == []


@pytest.mark.asyncio
async def test_validation_errors():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        bad_payload = {"title": ""}  # title can't be empty
        resp = await ac.post("/tasks/", json=bad_payload)
        assert resp.status_code == 422
        # Too short title, no description
        bad_payload2 = {"description": "no title present"}
        resp = await ac.post("/tasks/", json=bad_payload2)
        assert resp.status_code == 422
        # Update with invalid ID
        resp = await ac.patch("/tasks/9999", json={"title": "Shouldn't Work"})
        assert resp.status_code == 404
        # Delete with invalid ID
        resp = await ac.delete("/tasks/9999")
        assert resp.status_code == 404
