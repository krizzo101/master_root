from unittest.mock import MagicMock

import pytest
from app.api import WeatherResource


@pytest.fixture
def fake_weather_data():
    return {"temperature": 20, "condition": "Cloudy", "location": "Los Angeles"}


@pytest.fixture
def weather_resource(fake_weather_data):
    ws = MagicMock()
    ws.fetch_weather.return_value = fake_weather_data
    resource = WeatherResource(ws)
    return resource


class DummyRequest:
    args = {"location": "Los Angeles"}


def test_weatherresource_get_returns_weather_data_when_location_provided(
    weather_resource, monkeypatch
):
    # Patch flask request
    import app.api

    monkeypatch.setattr(app.api, "request", DummyRequest)
    response = weather_resource.get()
    assert response[1] == 200
    assert response[0]["location"] == "Los Angeles"
    weather_resource.weather_service.fetch_weather.assert_called_once_with(
        "Los Angeles"
    )


class DummyRequestMissing:
    args = {}


def test_weatherresource_get_returns_error_when_location_missing(
    weather_resource, monkeypatch
):
    import app.api

    monkeypatch.setattr(app.api, "request", DummyRequestMissing)
    response = weather_resource.get()
    assert response[1] == 400
    assert "error" in response[0]


class DummyRequestNoData:
    args = {"location": "Unknown Place"}


def test_weatherresource_get_handles_no_data_returned(weather_resource, monkeypatch):
    weather_resource.weather_service.fetch_weather.return_value = None
    import app.api

    monkeypatch.setattr(app.api, "request", DummyRequestNoData)
    response = weather_resource.get()
    assert response[1] == 404
    assert "error" in response[0]
