import pytest
from flask import url_for
from app.weather_service import WeatherService
from unittest.mock import patch


@pytest.fixture
def client(test_client):
    return test_client


@patch("app.weather_service.WeatherService.get_cached_weather")
def test_index_route(mock_weather, client):
    mock_weather.return_value = {
        "city": "Test Utopia",
        "temperature": 21.0,
        "humidity": 43,
        "description": "Partly cloudy",
        "icon": "02d",
        "wind_speed": 4.2,
    }
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test Utopia" in response.data
    assert b"21.0" in response.data


def test_favicon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert response.mimetype == "image/vnd.microsoft.icon"


@patch("app.weather_service.WeatherService.get_cached_weather")
def test_api_weather_success(mock_weather, client):
    mock_weather.return_value = {
        "city": "Mock City",
        "temperature": 99,
        "humidity": 0,
        "description": "Test",
        "icon": "01d",
        "wind_speed": 1,
    }
    resp = client.get("/api/weather")
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data["success"]
    assert json_data["weather"]["city"] == "Mock City"


@patch("app.weather_service.WeatherService.get_cached_weather")
def test_api_weather_failure(mock_weather, client):
    mock_weather.return_value = None
    resp = client.get("/api/weather")
    assert resp.status_code == 503
    json_data = resp.get_json()
    assert not json_data["success"]
