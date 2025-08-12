"""
External OpenWeatherMap API Client module.
"""
import logging
from typing import Any

import requests


class WeatherAPIError(Exception):
    """
    Custom exception for weather API errors.
    """

    pass


class WeatherAPIClient:
    """
    Client for OpenWeatherMap Current Weather Data API.
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, timeout: int = 5):
        """
        Args:
            api_key (str): OpenWeatherMap API key.
            timeout (int): Seconds to wait for API response.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Missing or invalid API key.")
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger("app.weather_client")

    def get_weather_by_city(self, city: str) -> dict[str, Any]:
        """
        Fetch current weather data for a city.
        Args:
            city (str): City name.
        Returns:
            dict: Weather details (main, weather, wind, etc.).
        Raises:
            WeatherAPIError: If API call fails or returns error.
        """
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        except requests.RequestException as ex:
            self.logger.error(f"Network error fetching weather: {ex}")
            raise WeatherAPIError("Weather service is temporarily unavailable.") from ex
        if resp.status_code == 404:
            raise WeatherAPIError(f'City "{city}" not found.')
        if resp.status_code != 200:
            self.logger.error(f"API error ({resp.status_code}): {resp.text}")
            raise WeatherAPIError("Error fetching weather information.")
        data = resp.json()
        # Only passed with 'metric'; can safely parse
        result = {
            "city": data.get("name"),
            "country": data.get("sys", {}).get("country"),
            "temperature": data.get("main", {}).get("temp"),
            "conditions": data.get("weather", [{}])[0].get("description", "Unknown"),
            "humidity": data.get("main", {}).get("humidity"),
            "wind_speed": data.get("wind", {}).get("speed"),
            "icon": data.get("weather", [{}])[0].get("icon", ""),
        }
        if None in [result["temperature"], result["city"]]:
            self.logger.error("Malformed weather API response.")
            raise WeatherAPIError("Malformed weather data.")
        return result
