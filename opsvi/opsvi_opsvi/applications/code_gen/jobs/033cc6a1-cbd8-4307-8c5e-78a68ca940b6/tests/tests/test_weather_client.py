import pytest
from unittest.mock import patch, MagicMock
from app.weather_client import WeatherClient, WeatherAPIError


def test_weatherclient_initialization_sets_attributes_correctly():
    api_key = "dummy_key"
    base_url = "https://api.example.com/weather"
    default_location = "London"
    units = "metric"
    timeout = 5

    client = WeatherClient(api_key, base_url, default_location, units, timeout)

    assert client.api_key == api_key
    assert client.base_url == base_url
    assert client.default_location == default_location
    assert client.units == units
    assert client.timeout == timeout


@patch("app.weather_client.requests.get")
def test_get_weather_successful_response_returns_data(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "weather": [{"description": "clear sky"}],
        "main": {"temp": 20},
        "name": "London",
    }
    mock_get.return_value = mock_response

    client = WeatherClient("key", "http://fakeurl", "London", "metric", 3)
    data = client.get_weather("London")
    assert isinstance(data, dict)
    assert "weather" in data
    assert data["name"] == "London"


@patch("app.weather_client.requests.get")
def test_get_weather_raises_weather_api_error_on_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_get.return_value = mock_response

    client = WeatherClient("key", "http://fakeurl", "London", "metric", 3)
    with pytest.raises(WeatherAPIError) as excinfo:
        client.get_weather("UnknownCity")
    assert "Failed to get weather data" in str(excinfo.value)


@patch("app.weather_client.requests.get", side_effect=TimeoutError)
def test_get_weather_raises_on_timeout(mock_get):
    client = WeatherClient("key", "http://fakeurl", "London", "metric", 1)
    with pytest.raises(WeatherAPIError) as excinfo:
        client.get_weather("London")
    assert "Timeout" in str(excinfo.value) or "Failed to get weather data" in str(
        excinfo.value
    )
