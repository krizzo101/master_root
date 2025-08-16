from unittest.mock import patch

from app.weather_service import WeatherService

MOCK_API_RESPONSE = {
    "name": "Testville",
    "main": {"temp": 19.1, "humidity": 52},
    "weather": [{"description": "clear sky", "icon": "01d"}],
    "wind": {"speed": 2.3},
}


def test_parse_weather_data():
    ws = WeatherService()
    parsed = ws.parse_weather_data(MOCK_API_RESPONSE)
    assert parsed["city"] == "Testville"
    assert parsed["temperature"] == 19.1
    assert parsed["humidity"] == 52
    assert parsed["description"] == "Clear sky"
    assert parsed["icon"] == "01d"
    assert parsed["wind_speed"] == 2.3


@patch("app.weather_service.WeatherService.fetch_weather")
def test_get_cached_weather(mock_fetch):
    mock_fetch.return_value = {
        "city": "Testville",
        "temperature": 19.1,
        "humidity": 52,
        "description": "Clear sky",
        "icon": "01d",
        "wind_speed": 2.3,
    }
    ws = WeatherService()
    out = ws.get_cached_weather()
    assert out["city"] == "Testville"
