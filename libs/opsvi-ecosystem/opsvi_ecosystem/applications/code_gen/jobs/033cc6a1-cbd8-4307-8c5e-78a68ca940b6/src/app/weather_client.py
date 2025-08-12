"""
Weather API Service Client: Handles external weather API communications.
"""
import logging
from typing import Any

import requests

from .config import Config


class WeatherAPIError(Exception):
    """
    Custom exception for WeatherAPI related errors.
    """

    pass


class WeatherClient:
    """
    Client for getting current weather data from a public weather API.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_location: str,
        units: str,
        timeout: int = 4,
    ) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = api_key
        self.base_url = base_url
        self.default_location = default_location
        self.units = units
        self.timeout = timeout

    def get_weather(self, city: str | None = None) -> dict[str, Any]:
        """
        Fetch current weather data for the specified city.
        :param city: City name (string).
        :return: Parsed weather info dict.
        :raises WeatherAPIError: On request or parsing failure.
        """
        location = city if city else self.default_location
        params = {"q": location, "appid": self.api_key, "units": self.units}
        self.logger.info(f"Requesting weather for city: {location}")
        try:
            resp = requests.get(self.base_url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error contacting weather API: {e}")
            raise WeatherAPIError(f"Error contacting weather service: {e}") from e

        try:
            data = resp.json()
            if data.get("cod") != 200:
                msg = data.get("message", "Unknown error")
                self.logger.error(f"Weather API error: {msg}")
                raise WeatherAPIError(f"Weather API error: {msg}")
            # Parse out relevant fields
            weather_info = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "description": data["weather"][0]["description"].capitalize(),
                "icon": data["weather"][0]["icon"],
                "temperature": round(data["main"]["temp"]),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data["wind"]["speed"],
            }
            return weather_info
        except (ValueError, KeyError, IndexError) as e:
            self.logger.error(f"Failed to parse weather data: {e}")
            raise WeatherAPIError(f"Invalid response from weather service: {e}") from e


def get_weather_client() -> WeatherClient:
    """
    Helper to instantiate the WeatherClient using app config.
    :return: Configured WeatherClient
    """
    if not Config.WEATHER_API_KEY:
        raise WeatherAPIError("Weather API key is missing in configuration.")
    return WeatherClient(
        api_key=Config.WEATHER_API_KEY,
        base_url=Config.WEATHER_API_BASE_URL,
        default_location=Config.DEFAULT_LOCATION,
        units=Config.WEATHER_UNITS,
        timeout=Config.WEATHER_API_TIMEOUT,
    )
