"""
Integration and unit tests for todo CRUD endpoints.
"""
import asyncio
import os

import pytest
from app.core.config import get_settings
from app.db.init_db import init_db
from app.main import app
from httpx import AsyncClient

# Use a separate test DB file
TEST_DB_PATH = "./test_todolist.db"
settings = get_settings()
settings.DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Ensure the test DB is created and clean
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    await init_db()
    yield
    # Remove the test DB after tests
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/healthz")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_todo():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"description": "Test todo 1", "is_completed": False}
        res = await ac.post("/api/todos/", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["description"] == payload["description"]
        assert data["is_completed"] == payload["is_completed"]
        assert "id" in data
        global TODO_ID
        TODO_ID = data["id"]


@pytest.mark.asyncio
async def test_get_todo():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get(f"/api/todos/{TODO_ID}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == TODO_ID
        assert data["description"] == "Test todo 1"
        assert data["is_completed"] is False


@pytest.mark.asyncio
async def test_list_todos():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/todos/")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert any(todo["id"] == TODO_ID for todo in data)


@pytest.mark.asyncio
async def test_update_todo():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"description": "Test todo 1 updated", "is_completed": True}
        res = await ac.put(f"/api/todos/{TODO_ID}", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == TODO_ID
        assert data["description"] == payload["description"]
        assert data["is_completed"] == payload["is_completed"]


@pytest.mark.asyncio
async def test_delete_todo():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.delete(f"/api/todos/{TODO_ID}")
        assert res.status_code == 204
        res2 = await ac.get(f"/api/todos/{TODO_ID}")
        assert res2.status_code == 404


@pytest.mark.asyncio
async def test_error_on_missing_todo():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/api/todos/123456789")
        assert res.status_code == 404
        res = await ac.delete("/api/todos/123456789")
        assert res.status_code == 404
        res = await ac.put("/api/todos/123456789", json={"description": "abc"})
        assert res.status_code == 404
