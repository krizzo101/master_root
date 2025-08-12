import pytest
from ai_service.ai_logic import (
    detect_dependencies,
    estimate_completion_times,
    prioritize_tasks,
    suggest_optimal_scheduling,
)
from ai_service.models import Task, TeamMember


@pytest.fixture
def sample_tasks():
    return [
        Task(
            id=1,
            name="Design Database Schema",
            estimated_hours=5,
            dependencies=[],
            priority=None,
            status="pending",
            assignee=None,
        ),
        Task(
            id=2,
            name="Develop API Endpoints",
            estimated_hours=8,
            dependencies=[1],
            priority=None,
            status="pending",
            assignee=None,
        ),
        Task(
            id=3,
            name="Frontend Implementation",
            estimated_hours=10,
            dependencies=[2],
            priority=None,
            status="pending",
            assignee=None,
        ),
        Task(
            id=4,
            name="Write Tests",
            estimated_hours=6,
            dependencies=[],
            priority=None,
            status="pending",
            assignee=None,
        ),
    ]


@pytest.fixture
def sample_members():
    return [
        TeamMember(id=1, name="Alice", role="Developer", availability=0.8),
        TeamMember(id=2, name="Bob", role="Developer", availability=0.5),
        TeamMember(id=3, name="Carol", role="Project Manager", availability=1.0),
    ]


def test_prioritize_tasks_with_valid_input(sample_tasks, sample_members):
    """Test that prioritize_tasks returns tasks in order of priority considering dependencies and member availability."""
    prioritized = prioritize_tasks(sample_tasks, sample_members)
    # Check that the output is a list with all tasks
    assert isinstance(prioritized, list), "Output should be a list"
    assert set(task.id for task in prioritized) == set(
        t.id for t in sample_tasks
    ), "All tasks must be present after prioritization"
    # Tasks with no dependencies or highest priority should come first
    first_task = prioritized[0]
    assert not first_task.dependencies, "First task should have no dependencies"


@pytest.mark.parametrize("invalid_tasks", [None, [], [{}]])
def test_prioritize_tasks_with_invalid_input(invalid_tasks, sample_members):
    """Test prioritize_tasks handling of invalid or empty task list."""
    with pytest.raises(Exception):
        prioritize_tasks(invalid_tasks, sample_members)


def test_estimate_completion_times_with_valid_tasks(sample_tasks):
    """Test that estimate_completion_times returns a dictionary with task IDs and estimated times."""
    estimates = estimate_completion_times(sample_tasks)
    assert isinstance(estimates, dict), "Estimates should be a dictionary"
    for task in sample_tasks:
        assert task.id in estimates, f"Task id {task.id} should be in estimate keys"
        assert isinstance(
            estimates[task.id], (int, float)
        ), "Estimate values should be numeric"
        assert estimates[task.id] > 0, "Estimated times should be positive"


def test_estimate_completion_times_with_empty_task_list():
    """Test estimate_completion_times gracefully handles empty task list."""
    estimates = estimate_completion_times([])
    assert estimates == {}, "Estimates for empty task list should be empty dict"


def test_detect_dependencies_correctly_identifies(sample_tasks):
    """Test detect_dependencies returns correct dependency mappings."""
    deps = detect_dependencies(sample_tasks)
    assert isinstance(deps, dict), "Dependencies should be returned as a dictionary"
    for task in sample_tasks:
        assert task.id in deps, f"Task id {task.id} should be in dependency dictionary"
        assert isinstance(
            deps[task.id], list
        ), "Dependencies for each task should be a list"
    # Check some known dependencies
    assert 1 not in deps[1], "Task should not depend on itself"
    assert deps[2] == [1], "Task 2 should depend on Task 1"


@pytest.mark.parametrize(
    "tasks,members",
    [
        ([], []),
        (
            [
                Task(
                    id=1,
                    name="Solo Task",
                    estimated_hours=1,
                    dependencies=[],
                    priority=1,
                    status="pending",
                    assignee=None,
                )
            ],
            [TeamMember(id=1, name="Solo Member", role="Developer", availability=1.0)],
        ),
    ],
)
def test_suggest_optimal_scheduling_various_inputs(tasks, members):
    """Test suggest_optimal_scheduling on empty and minimal input scenarios."""
    schedule = suggest_optimal_scheduling(tasks, members)
    assert isinstance(
        schedule, dict
    ), "Schedule should be returned as a dictionary mapping tasks to assigned members or times"
