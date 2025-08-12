"""
Integration tests for Flask routes.
"""
import os
import pytest
from app import create_app


# Use a test client and monkeypatch API client for reliability
class DummyWeatherAPIClient:
    def __init__(self, api_key: str, timeout: int = 5):
        pass

    def get_weather_by_city(self, city: str) -> dict:
        if city.lower() == "london":
            return {
                "city": "London",
                "country": "GB",
                "temperature": 19,
                "conditions": "light rain",
                "humidity": 62,
                "wind_speed": 5,
                "icon": "10d",
            }
        raise Exception("City not found")


@pytest.fixture
def client(monkeypatch):
    os.environ["OPENWEATHER_API_KEY"] = "test"
    app = create_app()
    app.config["TESTING"] = True
    # Patch WeatherAPIClient in app.routes
    import app.routes as routes

    routes.WeatherAPIClient = DummyWeatherAPIClient
    return app.test_client()


def test_index_get(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Weather Search" in resp.data


def test_city_weather_success(client):
    resp = client.post(
        "/", data={"city": "London", "submit": "Get Weather"}, follow_redirects=True
    )
    assert b"London" in resp.data
    assert b"19&#8451;" in resp.data
    assert b"light rain" in resp.data


def test_city_weather_invalid(client):
    resp = client.post(
        "/", data={"city": "", "submit": "Get Weather"}, follow_redirects=True
    )
    assert (
        b"Invalid city name" in resp.data or b"Please enter a city name." in resp.data
    )
