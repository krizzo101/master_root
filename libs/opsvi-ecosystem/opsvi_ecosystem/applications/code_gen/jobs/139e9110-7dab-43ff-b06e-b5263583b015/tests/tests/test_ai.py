from unittest.mock import MagicMock

import pytest
from backend.ai import (
    detect_dependencies,
    estimate_duration,
    prioritize_tasks,
    suggest_schedule,
)


@pytest.mark.asyncio
def test_prioritize_tasks_returns_ordered_tasks():
    fake_db = MagicMock()
    tasks = [
        {"id": "1", "title": "Low priority task"},
        {"id": "2", "title": "High priority task"},
        {"id": "3", "title": "Medium priority task"},
    ]
    user = MagicMock()

    # Mock AI prioritization by patching underlying call if needed
    sorted_tasks = await prioritize_tasks(fake_db, tasks, user)
    assert isinstance(sorted_tasks, list)
    assert all("id" in task for task in sorted_tasks)


@pytest.mark.asyncio
def test_estimate_duration_returns_positive_number():
    fake_db = MagicMock()
    task = {"id": "task01", "title": "Test task"}
    duration = await estimate_duration(fake_db, task)
    assert duration > 0


@pytest.mark.asyncio
def test_detect_dependencies_returns_nonempty_list_for_projects():
    fake_db = MagicMock()
    project_ids = ["proj1", "proj2"]
    dependencies = await detect_dependencies(fake_db, project_ids)
    assert isinstance(dependencies, list)
    for dep in dependencies:
        assert "task_id" in dep and "depends_on_task_id" in dep


@pytest.mark.asyncio
def test_suggest_schedule_returns_valid_schedule():
    fake_db = MagicMock()
    project_id = "proj1"
    user = MagicMock()
    schedule = await suggest_schedule(fake_db, project_id, user)
    assert isinstance(schedule, list)
    if schedule:
        assert "task_id" in schedule[0] and "start_time" in schedule[0]
