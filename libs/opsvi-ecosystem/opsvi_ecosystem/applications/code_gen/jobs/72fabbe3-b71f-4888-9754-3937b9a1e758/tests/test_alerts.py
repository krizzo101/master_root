from backend.alerts import get_active_alerts


def test_get_active_alerts_returns_list():
    alerts = get_active_alerts()
    assert isinstance(alerts, list)
