import pytest
from backend.models import MetricType, User, Threshold, MetricSample, AlertEvent


def test_metrictype_enum_values():
    types = [e.value for e in MetricType]
    assert "cpu" in types
    assert "memory" in types
    assert "disk" in types
    assert "network" in types


def test_user_model_creation_and_fields():
    user = User(
        id=1, username="user1", hashed_password="hash", email="user@example.com"
    )
    assert user.username == "user1"
    assert user.email == "user@example.com"


def test_threshold_model_fields_and_str():
    threshold = Threshold(id=1, metric_type="cpu", threshold=90)
    assert threshold.threshold == 90
    assert str(threshold) is not None


def test_metric_sample_creation_and_properties():
    sample = MetricSample(id=1, metric_type="memory", timestamp=1234567890, value=50.5)
    assert sample.metric_type == "memory"
    assert sample.value == 50.5


def test_alert_event_creation_and_status():
    alert = AlertEvent(
        id=1,
        metric_type="disk",
        triggered_at=1234567890,
        cleared_at=None,
        threshold=80,
        current_value=85,
    )
    assert alert.metric_type == "disk"
    assert alert.cleared_at is None
