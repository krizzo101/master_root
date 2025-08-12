import pytest
from app.main import health_check, shutdown_event, startup_event


def test_health_check_returns_ok_status():
    """Verify that health_check returns a dictionary with status 'ok'."""
    response = health_check()
    assert isinstance(response, dict)
    assert response.get("status") == "ok"


def test_startup_and_shutdown_event_run_without_error():
    """Ensure startup_event and shutdown_event functions execute without raising exceptions."""
    try:
        startup_event()
        shutdown_event()
    except Exception as e:
        pytest.fail(f"Startup or shutdown event raised an unexpected exception: {e}")
