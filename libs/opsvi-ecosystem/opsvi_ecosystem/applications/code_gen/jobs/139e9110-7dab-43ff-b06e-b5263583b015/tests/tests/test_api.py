import pytest
from backend.api import (
    list_projects,
    create_project,
    list_tasks,
    create_task,
    schedule_suggest,
    add_comment,
)
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
def test_list_projects_returns_projects_for_user():
    fake_db = MagicMock()
    user = MagicMock()
    projects = await list_projects(fake_db, user)
    assert isinstance(projects, list)


@pytest.mark.asyncio
def test_create_project_creates_and_returns_project():
    fake_db = MagicMock()
    user = MagicMock()
    data = {"name": "New Project"}
    project = await create_project(data, fake_db, user)
    assert project["name"] == data["name"]


@pytest.mark.asyncio
def test_list_tasks_returns_tasks_for_project():
    fake_db = MagicMock()
    user = MagicMock()
    project_id = "proj1"
    tasks = await list_tasks(project_id, fake_db, user)
    assert isinstance(tasks, list)


@pytest.mark.asyncio
def test_create_task_adds_task_successfully():
    fake_db = MagicMock()
    user = MagicMock()
    project_id = "proj1"
    data = {"title": "New Task", "description": "Do something"}
    task = await create_task(project_id, data, fake_db, user)
    assert task["title"] == data["title"]


@pytest.mark.asyncio
def test_schedule_suggest_returns_schedule_for_project():
    fake_db = MagicMock()
    user = MagicMock()
    project_id = "proj1"
    schedule = await schedule_suggest(project_id, fake_db, user)
    assert isinstance(schedule, list)


@pytest.mark.asyncio
def test_add_comment_adds_comment_and_returns_it():
    fake_db = MagicMock()
    user = MagicMock()
    task_id = "task1"
    data = {"content": "This is a test comment"}
    comment = await add_comment(task_id, data, fake_db, user)
    assert comment["content"] == data["content"]
