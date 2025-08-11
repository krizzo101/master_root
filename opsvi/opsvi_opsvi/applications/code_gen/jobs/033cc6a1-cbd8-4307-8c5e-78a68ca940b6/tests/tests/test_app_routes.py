import pytest
from app import create_app
from unittest.mock import patch

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def mock_weather_client_get_weather(city):
    return {
        'city': city or 'London',
        'country': 'UK',
        'description': 'Clear sky',
        'icon': '01d',
        'temperature': 22,
        'humidity': 55,
        'pressure': 1012,
        'wind_speed': 4.2...
    }

def test_index_get_success(client, monkeypatch):
    monkeypatch.setattr(
        'app.weather_client.WeatherClient.get_weather',
        lambda self, city=None: mock_weather_client_get_weather(city or 'London')
    )
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"Weather in" in resp.data


def test_index_post_search_success(client, monkeypatch):
    monkeypatch.setattr(
        'app.weather_client.WeatherClient.get_weather',
        lambda self, city=None: mock_weather_client_get_weather(city or 'Paris')
    )
    resp = client.post('/', data={'city': 'Paris'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Paris" in resp.data


def test_index_post_empty_city(client):
    resp = client.post('/', data={'city': ''}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please enter a city name" in resp.data
