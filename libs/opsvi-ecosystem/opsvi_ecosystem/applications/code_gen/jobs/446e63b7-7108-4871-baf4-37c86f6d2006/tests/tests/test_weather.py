import pytest
from unittest.mock import MagicMock, patch
from app.weather import WeatherService


@pytest.fixture
def weather_service(app):
    cache = MagicMock()
    ws = WeatherService(app, cache)
    return ws


@pytest.fixture
def sample_weather_api_response():
    return {
        "location": {"name": "New York", "region": "NY", "country": "USA"},
        "current": {"temp_c": 25, "condition": {"text": "Sunny"}},
    }


def test_weatherservice_init_sets_attributes_correctly(weather_service, app):
    assert weather_service.app == app
    assert weather_service.cache is not None


@patch("app.weather.requests.get")
def test_fetch_weather_returns_parsed_data_with_mocked_api_call(
    mock_get, weather_service, sample_weather_api_response
):
    mock_response = MagicMock()
    mock_response.json.return_value = sample_weather_api_response
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    weather_service.parse_weather = MagicMock(
        return_value={
            "temperature": 25,
            "condition": "Sunny",
            "location": "New York, NY, USA",
        }
    )

    result = weather_service.fetch_weather("New York")

    mock_get.assert_called_once()
    weather_service.parse_weather.assert_called_once_with(sample_weather_api_response)
    assert result["temperature"] == 25
    assert result["condition"] == "Sunny"
    assert result["location"] == "New York, NY, USA"
    weather_service.cache.set.assert_called_once()


@patch("app.weather.requests.get")
def test_fetch_weather_handles_api_failure_and_returns_none(mock_get, weather_service):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    result = weather_service.fetch_weather("Nowhere")
    assert result is None


def test_parse_weather_extracts_correct_data(sample_weather_api_response):
    ws = WeatherService(None, None)
    data = sample_weather_api_response
    parsed = ws.parse_weather(data)

    assert parsed["temperature"] == 25
    assert parsed["condition"] == "Sunny"
    assert parsed["location"] == "New York, NY, USA"


def test_parse_weather_returns_none_when_data_missing_or_malformed():
    ws = WeatherService(None, None)
    assert ws.parse_weather(None) is None
    assert ws.parse_weather({}) is None
    assert ws.parse_weather({"location": {}, "current": {}}) is None
