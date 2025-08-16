import pytest
from httpx import AsyncClient
from app.main import app
import asyncio


@pytest.mark.asyncio
async def test_task_crud():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Create a task
        res = await ac.post(
            "/tasks/", json={"title": "Test Task", "description": "Unit test task."}
        )
        assert res.status_code == 201
        created = res.json()
        assert created["title"] == "Test Task"
        assert created["description"] == "Unit test task."
        task_id = created["id"]

        # Get all tasks
        res = await ac.get("/tasks/")
        assert res.status_code == 200
        tasks = res.json()
        assert any(t["id"] == task_id for t in tasks)

        # Get task by id
        res = await ac.get(f"/tasks/{task_id}")
        assert res.status_code == 200
        task = res.json()
        assert task["id"] == task_id
        assert task["title"] == "Test Task"

        # Update task
        res = await ac.put(f"/tasks/{task_id}", json={"title": "Updated Title"})
        assert res.status_code == 200
        updated = res.json()
        assert updated["title"] == "Updated Title"

        # Delete task
        res = await ac.delete(f"/tasks/{task_id}")
        assert res.status_code == 204

        # Confirm deletion
        res = await ac.get(f"/tasks/{task_id}")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
