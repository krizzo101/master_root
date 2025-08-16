"""
Weather Data Service for Flask Weather App: Fetches, caches, and transforms weather data.
"""
import logging
import requests
from typing import Optional, Dict, Any
from flask import current_app
from cachelib.base import BaseCache


class WeatherService:
    """
    A service for fetching and caching weather data from an external weather API.
    """

    def __init__(self, app, cache: BaseCache):
        """
        Initialize WeatherService with Flask app context and a cache backend.
        """
        self.app = app
        self.cache = cache
        self.api_key = app.config["WEATHER_API_KEY"]
        self.api_url = app.config["WEATHER_API_URL"]
        self.units = app.config["WEATHER_UNITS"]
        self.cache_timeout = app.config["WEATHER_CACHE_TIMEOUT"]

    def fetch_weather(self, location: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches current weather data for a given location (city name).
        Uses a short-lived cache to avoid excessive API calls.
        :param location: City name or "City,CountryCode"
        :return: A dict with weather info (location, temperature, conditions, etc)
        :raises: RuntimeError, ValueError on error or malformed results
        """
        if not location:
            location = self.app.config["WEATHER_DEFAULT_LOCATION"]
        cache_key = f"weather::{location.lower()}"
        data = self.cache.get(cache_key)
        if data:
            logging.debug(f"WeatherService: Returning cached weather for {location}")
            return data
        params = {"q": location, "appid": self.api_key, "units": self.units}
        try:
            logging.info(f"WeatherService: Fetching weather from API for {location}")
            resp = requests.get(self.api_url, params=params, timeout=3)
            resp.raise_for_status()
            result = resp.json()
            parsed = self.parse_weather(result)
            # Cache result
            self.cache.set(cache_key, parsed, timeout=self.cache_timeout)
            return parsed
        except requests.RequestException as e:
            logging.error(f"WeatherService: Error fetching weather data: {e}")
            raise RuntimeError(f"Error fetching weather data: {e}")
        except Exception as ex:
            logging.error(f"WeatherService: Unexpected error: {ex}")
            raise RuntimeError(f"Error parsing weather data: {ex}")

    @staticmethod
    def parse_weather(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses weather data from OpenWeatherMap API.
        :param data: Raw JSON response
        :return: Dict with keys: location, country, temperature, conditions, icon, humidity, wind_speed
        :raises: ValueError if expected keys are missing
        """
        try:
            location = data["name"]
            country = data["sys"]["country"]
            temperature = data["main"]["temp"]
            conditions = data["weather"][0]["description"]
            icon = data["weather"][0]["icon"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            return {
                "location": location,
                "country": country,
                "temperature": temperature,
                "conditions": conditions.title(),
                "icon": icon,
                "humidity": humidity,
                "wind_speed": wind_speed,
            }
        except (KeyError, IndexError) as e:
            raise ValueError(f"Malformed weather API response: {e}")
