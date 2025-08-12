import pytest
from ai_service.models import TeamMember, Task, TaskInput, AIResponse


def test_team_member_creation_and_attributes():
    """Test TeamMember object creation and attribute values."""
    member = TeamMember(id=42, name="Dana", role="Tester", availability=0.75)
    assert member.id == 42
    assert member.name == "Dana"
    assert member.role == "Tester"
    assert isinstance(member.availability, float)
    assert 0 <= member.availability <= 1


def test_task_creation_and_default_status():
    """Check Task object instantiation and default values."""
    task = Task(
        id=101,
        name="Write Docs",
        estimated_hours=3,
        dependencies=[],
        priority=5,
        status="pending",
        assignee=None,
    )
    assert task.id == 101
    assert task.name == "Write Docs"
    assert task.estimated_hours == 3
    assert isinstance(task.dependencies, list)
    assert task.priority == 5
    assert task.status == "pending"
    assert task.assignee is None


def test_taskinput_data_integrity():
    """Validate TaskInput data is stored and accessible properly."""
    task_input = TaskInput(
        name="New Feature", estimated_hours=12, dependencies=[10], priority=None
    )
    assert task_input.name == "New Feature"
    assert task_input.estimated_hours == 12
    assert task_input.dependencies == [10]
    assert task_input.priority is None


def test_airesponse_attributes_and_behavior():
    """Test AIResponse model for property and data integrity."""
    response = AIResponse(
        priorities={"task1": 1},
        estimates={"task1": 5.5},
        dependencies={"task2": ["task1"]},
        schedule={"task1": "Alice"},
    )
    assert isinstance(response.priorities, dict)
    assert isinstance(response.estimates, dict)
    assert isinstance(response.dependencies, dict)
    assert isinstance(response.schedule, dict)

    # Check the correctness of stored data
    assert response.priorities.get("task1") == 1
    assert response.estimates.get("task1") == 5.5
    assert response.dependencies.get("task2") == ["task1"]
    assert response.schedule.get("task1") == "Alice"


@pytest.mark.parametrize("invalid_id", [None, -1, "abc"])
def test_team_member_invalid_id_raises(invalid_id):
    """Assuming id should be a positive integer, test invalid ids raise errors or are handled."""
    with pytest.raises(Exception):
        TeamMember(id=invalid_id, name="Invalid", role="Dev", availability=1.0)


@pytest.mark.parametrize("invalid_availability", [-0.1, 1.1, "full"])
def test_team_member_invalid_availability_raises(invalid_availability):
    """Test that invalid availability values raise exceptions or validation errors."""
    with pytest.raises(Exception):
        TeamMember(id=1, name="Tester", role="Dev", availability=invalid_availability)
