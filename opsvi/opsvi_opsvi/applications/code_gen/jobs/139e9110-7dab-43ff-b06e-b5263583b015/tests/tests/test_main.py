import pytest
from backend.main import health


def test_health_endpoint_returns_ok():
    response = health()
    assert response == {"status": "ok"}
