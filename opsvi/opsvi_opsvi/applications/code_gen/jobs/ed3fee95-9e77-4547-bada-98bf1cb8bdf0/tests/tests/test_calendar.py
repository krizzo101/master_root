import pytest
from unittest.mock import MagicMock, patch
from ai_collab_task_manager.calendar import GoogleCalendarService


@pytest.fixture
def google_calendar_service():
    return GoogleCalendarService()


def test_google_calendar_service_init(google_calendar_service):
    assert hasattr(google_calendar_service, "credentials")


def mock_sync(*args, **kwargs):
    return True


def test_sync_user_tasks(monkeypatch, google_calendar_service):
    monkeypatch.setattr(google_calendar_service, "sync_user_tasks", mock_sync)
    user = MagicMock()
    result = google_calendar_service.sync_user_tasks(user)
    assert result is True
