import pytest
from app.weather import WeatherService
from unittest.mock import MagicMock
from cachelib import SimpleCache


class DummyApp:
    config = {
        "WEATHER_API_KEY": "dummy",
        "WEATHER_API_URL": "https://api.openweathermap.org/data/2.5/weather",
        "WEATHER_UNITS": "metric",
        "WEATHER_DEFAULT_LOCATION": "Testville",
        "WEATHER_CACHE_TIMEOUT": 300,
    }


def test_parse_weather_valid():
    raw = {
        "name": "London",
        "sys": {"country": "GB"},
        "main": {"temp": 12.0, "humidity": 70},
        "weather": [{"description": "cloudy", "icon": "03d"}],
        "wind": {"speed": 6.2},
    }
    parsed = WeatherService.parse_weather(raw)
    assert parsed["location"] == "London"
    assert parsed["country"] == "GB"
    assert parsed["temperature"] == 12.0
    assert parsed["conditions"] == "Cloudy"
    assert parsed["icon"] == "03d"
    assert parsed["humidity"] == 70
    assert parsed["wind_speed"] == 6.2


def test_parse_weather_invalid():
    bad = {"foo": "bar"}
    with pytest.raises(ValueError):
        WeatherService.parse_weather(bad)


def test_fetch_weather_caching(monkeypatch):
    # Prepare service and fake requests.get
    dummy_app = DummyApp()
    cache = SimpleCache()
    service = WeatherService(dummy_app, cache)
    sample_resp = {
        "name": "Berlin",
        "sys": {"country": "DE"},
        "main": {"temp": 5.5, "humidity": 80},
        "weather": [{"description": "fog", "icon": "50d"}],
        "wind": {"speed": 2.0},
    }

    class DummyResp:
        def raise_for_status(self):
            pass

        def json(self):
            return sample_resp

    def fake_requests_get(*args, **kwargs):
        return DummyResp()

    monkeypatch.setattr("requests.get", fake_requests_get)
    # Not in cache so request should be made
    result1 = service.fetch_weather("Berlin")
    assert result1["location"] == "Berlin"
    # Should now be cached (simulate fetch again)
    result2 = service.fetch_weather("Berlin")
    assert result2 is result1


def test_fetch_weather_error(monkeypatch):
    dummy_app = DummyApp()
    cache = SimpleCache()
    service = WeatherService(dummy_app, cache)

    def failing_requests_get(*args, **kwargs):
        raise Exception("fail!")

    monkeypatch.setattr("requests.get", failing_requests_get)
    with pytest.raises(RuntimeError):
        service.fetch_weather("Paris")
