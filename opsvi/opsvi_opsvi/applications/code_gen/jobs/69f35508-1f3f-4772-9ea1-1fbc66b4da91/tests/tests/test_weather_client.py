"""
Unit tests for WeatherAPIClient (with mocking).
"""
import pytest
import requests
from app.weather_client import WeatherAPIClient, WeatherAPIError


class FakeResponse:
    def __init__(self, status_code, json_dct):
        self.status_code = status_code
        self._json = json_dct
        self.text = str(json_dct)

    def json(self):
        return self._json


def test_success(monkeypatch):
    """Test normal fetch."""

    def fake_get(url, params, timeout):
        assert "q" in params
        assert params["appid"] == "demo_key"
        return FakeResponse(
            200,
            {
                "name": "London",
                "sys": {"country": "GB"},
                "main": {"temp": 15, "humidity": 60},
                "weather": [{"description": "clear sky", "icon": "01d"}],
                "wind": {"speed": 2},
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)
    client = WeatherAPIClient(api_key="demo_key", timeout=3)
    res = client.get_weather_by_city("London")
    assert res["city"] == "London"
    assert res["temperature"] == 15
    assert res["conditions"] == "clear sky"


def test_not_found(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(404, {"message": "city not found"})

    monkeypatch.setattr(requests, "get", fake_get)
    client = WeatherAPIClient(api_key="demo_key")
    with pytest.raises(WeatherAPIError) as ex:
        client.get_weather_by_city("Atlantis")
    assert "not found" in str(ex.value)


def test_bad_response(monkeypatch):
    def fake_get(url, params, timeout):
        return FakeResponse(502, {"message": "server error"})

    monkeypatch.setattr(requests, "get", fake_get)
    client = WeatherAPIClient(api_key="demo_key")
    with pytest.raises(WeatherAPIError):
        client.get_weather_by_city("London")


def test_network_error(monkeypatch):
    def fake_get(url, params, timeout):
        raise requests.RequestException("oops")

    monkeypatch.setattr(requests, "get", fake_get)
    client = WeatherAPIClient(api_key="demo_key")
    with pytest.raises(WeatherAPIError) as ex:
        client.get_weather_by_city("Paris")
    assert "temporarily unavailable" in str(ex.value)
