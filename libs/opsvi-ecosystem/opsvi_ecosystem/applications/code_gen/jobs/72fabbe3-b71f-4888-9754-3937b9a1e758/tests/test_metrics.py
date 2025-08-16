import pytest
from backend.metrics import get_historical_metrics, get_realtime_metrics


def test_get_realtime_metrics_returns_all_metrics():
    data = get_realtime_metrics()
    assert isinstance(data, dict)
    for key in ["cpu", "memory", "disk", "network"]:
        assert key in data
        assert isinstance(data[key], (int, float))
        assert 0 <= data[key] <= 100


def test_get_historical_metrics_valid_and_invalid():
    import time

    current_time = int(time.time())
    metric_type = "cpu"
    results = get_historical_metrics(metric_type, current_time - 10, current_time)
    assert isinstance(results, list)

    with pytest.raises(Exception):
        get_historical_metrics("invalid_metric", current_time - 10, current_time)
