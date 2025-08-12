import pytest
from ai_collab_task_manager.ai_service import AIService
from ai_collab_task_manager.models import Task


@pytest.fixture
def ai_service():
    return AIService(api_key="testkey")


@pytest.fixture
def sample_task_obj():
    return Task(id=1, title="Test task", description="Task description")


def test_ai_service_init(ai_service):
    assert ai_service.api_key == "testkey"


from ai_collab_task_manager.ai_service import anonymize_task_data


def test_anonymize_task_data(sample_task_obj):
    task = sample_task_obj
    task.title = "Confidential Task"
    task.description = "Secret details"
    anonymized = anonymize_task_data(task)
    assert "Confidential" not in anonymized["title"]
    assert "Secret" not in anonymized["description"]
    assert "title" in anonymized
    assert "description" in anonymized


def test_schedule_ai_prio_and_estimate(monkeypatch, ai_service):
    monkeypatch.setattr(
        ai_service, "_invoke_ai_for_task", lambda task_id: "response text"
    )
    monkeypatch.setattr(
        ai_service, "_parse_ai_response", lambda text: {"priority": 1, "estimate": 10}
    )
    result = ai_service.schedule_ai_prio_and_estimate(1)
    assert "priority" in result
    assert "estimate" in result


def test__parse_ai_response(ai_service):
    sample_response = "Priority:High\nEstimate: 2 hours"
    result = ai_service._parse_ai_response(sample_response)
    # Depending on implementation, assume returns dict
    assert isinstance(result, dict)
    assert "priority" in result
    assert "estimate" in result
