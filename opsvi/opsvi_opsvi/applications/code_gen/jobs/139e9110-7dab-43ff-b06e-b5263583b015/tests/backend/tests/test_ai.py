"""
Mocked AI tests for prioritization and estimation.
"""
import pytest
from unittest.mock import patch
from backend.ai import prioritize_tasks, estimate_duration


@patch("backend.ai.openai.ChatCompletion.create")
def test_prioritize_tasks(mock_chat_create):
    class FakeTask:
        id = "1"
        title = "A"
        description = "desc"
        priority = 0

    mock_chat_create.return_value = type(
        "obj", (), {"choices": [type("obj", (), {"message": {"content": '{"1":0}'}})]}
    )
    tasks = [FakeTask()]
    prioritize_tasks(None, tasks, None)
    assert tasks[0].priority == 0


@patch("backend.ai.openai.ChatCompletion.create")
def test_estimate_duration(mock_chat_create):
    class FakeTask:
        title = "A"
        description = "desc"
        estimated_duration = None

    mock_chat_create.return_value = type(
        "obj", (), {"choices": [type("obj", (), {"message": {"content": "1.5"}})]}
    )
    t = FakeTask()
    estimate_duration(None, t)
    assert t.estimated_duration == 1.5
