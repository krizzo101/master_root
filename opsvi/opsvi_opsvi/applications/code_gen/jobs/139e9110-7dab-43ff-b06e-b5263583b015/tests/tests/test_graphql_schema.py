import pytest
from backend.graphql_schema import (
    resolve_projects,
    resolve_tasks,
    resolve_create_project,
    resolve_create_task,
)
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
def test_resolve_projects_returns_list_of_projects():
    projects = await resolve_projects()
    assert isinstance(projects, list)
    for project in projects:
        assert "id" in project


@pytest.mark.asyncio
def test_resolve_tasks_returns_list_of_tasks():
    tasks = await resolve_tasks()
    assert isinstance(tasks, list)
    if tasks:
        assert "id" in tasks[0]


@pytest.mark.asyncio
def test_resolve_create_project_creates_project():
    data = {"name": "GraphQL Project"}
    project = await resolve_create_project(data)
    assert "id" in project
    assert project["name"] == data["name"]


@pytest.mark.asyncio
def test_resolve_create_task_creates_task_under_project():
    data = {"title": "GraphQL Task", "project_id": "proj123"}
    task = await resolve_create_task(data)
    assert "id" in task
    assert task["title"] == data["title"]
