import pytest
from app import create_app
import os
from flask import url_for
from unittest.mock import patch


@pytest.fixture
def app():
    # Provide a valid API key for test context
    os.environ["WEATHER_API_KEY"] = "dummykey"
    app = create_app()
    app.testing = True
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def mock_fetch_weather(self, location=None):
    return {
        "location": "TestCity",
        "country": "TC",
        "temperature": 22.2,
        "conditions": "Sunny",
        "icon": "01d",
        "humidity": 33,
        "wind_speed": 3.2,
    }


def test_home_get(client):
    with patch("app.weather.WeatherService.fetch_weather", mock_fetch_weather):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"TestCity" in resp.data


def test_home_post_valid(client):
    with patch("app.weather.WeatherService.fetch_weather", mock_fetch_weather):
        resp = client.post("/", data={"location": "Somewhere"})
        assert resp.status_code == 200
        assert b"TestCity" in resp.data


def test_home_post_invalid(client):
    resp = client.post("/", data={"location": ""})
    assert b"Please enter a location." in resp.data


def test_api_weather_success(client):
    with patch("app.weather.WeatherService.fetch_weather", mock_fetch_weather):
        resp = client.get("/api/weather?location=TestCity")
        j = resp.get_json()
        assert resp.status_code == 200
        assert j["success"] is True
        assert j["data"]["location"] == "TestCity"


def test_api_weather_failure(client):
    # Patch fetch_weather to raise
    def fail_fetch(*a, **k):
        raise RuntimeError("boom")

    with patch("app.weather.WeatherService.fetch_weather", fail_fetch):
        resp = client.get("/api/weather?location=Whatever")
        j = resp.get_json()
        assert not j["success"]
        assert "boom" in j["error"]


def test_404(client):
    resp = client.get("/doesnotexist")
    assert resp.status_code == 404
    assert b"404" in resp.data
