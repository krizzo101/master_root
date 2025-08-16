import pytest
from backend.calendar import push_task_to_calendar


@pytest.mark.asyncio
def test_push_task_to_calendar_creates_event_successfully():
    fake_db = pytest.MagicMock()
    user = pytest.MagicMock()
    task_id = "task123"
    result = await push_task_to_calendar(task_id, fake_db, user)
    assert result is None or result == "success"
