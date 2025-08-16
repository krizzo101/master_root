import pytest
from backend.schemas import (
    MetricsHistoryQuery,
    ThresholdUpdate,
    UserCreate,
)
from pydantic import ValidationError


def test_user_create_schema_validation():
    user = UserCreate(username="user1", password="pass123")
    assert user.username == "user1"
    with pytest.raises(ValidationError):
        UserCreate(password="pass123")  # missing username
    with pytest.raises(ValidationError):
        UserCreate(username="user1")  # missing password


import time


def test_metrics_history_query_valid_and_invalid():
    import pytest

    current_time = int(time.time())
    query = MetricsHistoryQuery(
        metric_type="cpu", start_ts=current_time - 100, end_ts=current_time
    )
    assert query.metric_type == "cpu"

    with pytest.raises(ValidationError):
        MetricsHistoryQuery(
            metric_type="invalid_metric",
            start_ts=current_time - 100,
            end_ts=current_time,
        )


def test_threshold_update_schema_accepts_thresholds():
    update = ThresholdUpdate(thresholds=[{"metric_type": "cpu", "threshold": 85}])
    assert len(update.thresholds) == 1
    assert update.thresholds[0].metric_type == "cpu"
