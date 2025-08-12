import pytest
from ai_collab_task_manager.reporting import ReportingService, minutes


@pytest.fixture
def reporting_service():
    return ReportingService()


from datetime import timedelta


def test_minutes():
    td = timedelta(hours=1, minutes=30)
    result = minutes(td)
    assert result == 90


def test_generate_user_report(reporting_service):
    class DummyUser:
        id = 1

    user = DummyUser()
    report = reporting_service.generate_user_report(user)
    assert isinstance(report, dict)
    assert "tasks_completed" in report
    assert "time_spent" in report
    assert "completion_percent" in report
