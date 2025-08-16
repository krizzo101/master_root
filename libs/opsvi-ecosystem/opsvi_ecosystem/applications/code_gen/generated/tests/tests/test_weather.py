from unittest.mock import MagicMock, patch

import pytest
from app.weather import WeatherAPIError, fetch_weather, kelvin_to_celsius


@pytest.mark.parametrize(
    "kelvin,expected_celsius",
    [(0, -273.15), (273.15, 0), (300, 26.85), (310.15, 37), (1000, 726.85)],
)
def test_kelvin_to_celsius_normal_values(kelvin, expected_celsius):
    result = kelvin_to_celsius(kelvin)
    assert (
        abs(result - expected_celsius) < 0.01
    ), f"Expected {expected_celsius} but got {result}"


@pytest.mark.parametrize("invalid_value", [-10, -273.16])
def test_kelvin_to_celsius_negative_and_invalid(invalid_value):
    # kelvin_to_celsius should still convert negative kelvin (even if physically invalid), verify formula
    result = kelvin_to_celsius(invalid_value)
    assert isinstance(result, float)
    # Check correct conversion
    assert result == invalid_value - 273.15


@patch("app.weather.requests.get")
def test_fetch_weather_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {"temp": 295.15},
        "weather": [{"main": "Clear"}],
        "name": "TestCity",
    }
    mock_get.return_value = mock_response

    result = fetch_weather("TestCity")

    assert isinstance(result, dict), "Result should be a dict"
    assert "temp_celsius" in result
    assert abs(result["temp_celsius"] - 22.0) < 0.1
    assert result["condition"] == "Clear"
    assert result["location"] == "TestCity"


@patch("app.weather.requests.get")
def test_fetch_weather_raises_weatherapierror_on_bad_status(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not found"
    mock_get.return_value = mock_response

    with pytest.raises(WeatherAPIError) as exc_info:
        fetch_weather("InvalidLocation")
    assert "Failed to fetch weather" in str(exc_info.value)


@patch("app.weather.requests.get", side_effect=Exception("Connection error"))
def test_fetch_weather_raises_weatherapierror_on_request_exception(mock_get):
    with pytest.raises(WeatherAPIError) as exc_info:
        fetch_weather("City")
    assert "Failed to fetch weather" in str(exc_info.value)


def test_weatherapierror_exception_class():
    exc = WeatherAPIError("test message")
    assert isinstance(exc, Exception)
    assert str(exc) == "test message"
