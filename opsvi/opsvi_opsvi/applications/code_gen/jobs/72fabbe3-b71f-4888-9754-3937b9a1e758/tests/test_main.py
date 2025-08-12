from unittest.mock import MagicMock, patch

import pytest
from backend.main import (
    api_get_active_alerts,
    api_get_historical_metrics,
    api_get_realtime_metrics,
    api_get_thresholds,
    api_update_thresholds,
    app,
    login,
    register,
    setup_logging,
    startup_event,
)
from backend.models import User
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fake_db_session():
    class FakeDB:
        def query(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

        def add(self, obj):
            self.obj_added = obj

        def commit(self):
            pass

        def refresh(self, obj):
            pass

    return FakeDB()


def test_setup_logging_initializes_properly():
    # Just ensure the call does not raise exceptions
    setup_logging()


@pytest.mark.asyncio
def test_startup_event_runs_successfully():
    # As startup_event is likely async, run it and assert no exceptions
    import asyncio

    try:
        asyncio.run(startup_event())
    except Exception as e:
        pytest.fail(f"startup_event raised exception: {e}")


def test_login_success_and_failure(fake_db_session):
    form_data = MagicMock()
    form_data.username = "testuser"
    form_data.password = "correctpass"

    fake_db_session.query().filter().first = MagicMock(
        return_value=User(
            username="testuser",
            hashed_password="$2b$12$KIXmT./Lj2Qh5paj1LZka.6aAFxaNTX6R.1kaOA7Pl1/WdyOFGIRQ",
        )
    )

    # Patch verify_password to simulate correct password
    with patch("backend.main.verify_password", return_value=True):
        token_response = login(form_data, fake_db_session)
        assert "access_token" in token_response

    # Patch verify_password to simulate incorrect password
    with patch("backend.main.verify_password", return_value=False):
        with pytest.raises(Exception):
            login(form_data, fake_db_session)


def test_register_creates_new_user_and_fails_on_duplicate(fake_db_session):
    user_create = MagicMock()
    user_create.username = "newuser"
    user_create.password = "pass123"

    # Case: user does not exist, registration succeeds
    fake_db_session.query().filter().first = MagicMock(return_value=None)
    result = register(user_create, fake_db_session)
    assert hasattr(result, "username")

    # Case: user already exists, register raises Exception
    fake_db_session.query().filter().first = MagicMock(
        return_value=User(username="newuser")
    )
    with pytest.raises(Exception):
        register(user_create, fake_db_session)


def test_api_get_realtime_metrics_returns_data():
    user = MagicMock()
    data = api_get_realtime_metrics(user)
    assert isinstance(data, dict)
    # Should contain keys representing metrics
    assert any(key in data for key in ["cpu", "memory", "disk", "network"])


def test_api_get_historical_metrics_returns_data():
    user = MagicMock()
    query = MagicMock()
    query.metric_type = "cpu"
    query.start_ts = 0
    query.end_ts = 1000000
    data = api_get_historical_metrics(query, user)
    assert isinstance(data, list)

    # Invalid metric_type should raise Exception
    query.metric_type = "invalid_metric"
    with pytest.raises(Exception):
        api_get_historical_metrics(query, user)


def test_api_get_and_update_thresholds(fake_db_session):
    user = MagicMock()
    user.id = 1

    # Setup initial thresholds in db mock
    fake_db_session.query().filter().all = MagicMock(
        return_value=[MagicMock(metric_type="cpu", threshold=90)]
    )
    # Test get thresholds
    thresholds = api_get_thresholds(user, fake_db_session)
    assert isinstance(thresholds, list)

    # Test update thresholds
    # Construct a mock update object
    update_mock = MagicMock()
    update_mock.thresholds = [{"metric_type": "cpu", "threshold": 80}]

    updated = api_update_thresholds(update_mock, user, fake_db_session)
    assert isinstance(updated, list)
    assert updated[0].threshold == 80


def test_api_get_active_alerts_returns_list():
    user = MagicMock()
    alerts = api_get_active_alerts(user)
    assert isinstance(alerts, list)
