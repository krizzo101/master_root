import time
from unittest.mock import MagicMock, patch

from app.weather import fetch_weather


@patch("app.weather.requests.get")
def test_performance_fetch_weather_api_response_time(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "main": {"temp": 295.15},
        "weather": [{"main": "Clear"}],
        "name": "SpeedCity",
    }
    mock_get.return_value = mock_response

    start = time.time()
    fetch_weather("SpeedCity")
    end = time.time()

    assert (end - start) < 2, f"fetch_weather took too long: {end - start} seconds"
