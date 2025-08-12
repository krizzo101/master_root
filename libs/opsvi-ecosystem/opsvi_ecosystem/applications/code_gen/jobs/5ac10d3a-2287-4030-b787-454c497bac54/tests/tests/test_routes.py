import pytest
from app import create_app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    app = create_app()
    # app.config['TESTING'] = True to activate testing mode
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("app.weather.fetch_weather")
def test_index_route_renders_weather_information(mock_fetch, client):
    mock_fetch.return_value = {
        "temp_celsius": 20.5,
        "condition": "Clear",
        "location": "TestCity",
    }
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "TestCity" in html
    assert "20.5" in html
    assert "Clear" in html


@patch("app.weather.fetch_weather", side_effect=Exception("API down"))
def test_index_route_handles_weatherapierror_gracefully(mock_fetch, client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # We expect an error message in html
    assert "Error fetching weather" in html or "error" in html.lower()


def test_index_route_default_methods_and_url(client):
    response = client.get("/")
    assert response.status_code == 200
