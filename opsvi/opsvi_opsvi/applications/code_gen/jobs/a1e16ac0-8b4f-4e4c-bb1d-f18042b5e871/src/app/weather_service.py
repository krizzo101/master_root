"""
WeatherService provides an abstraction for fetching, caching, and parsing weather data
from a remote API. It includes error handling and supports periodic cache refresh.
"""
import logging
from typing import Optional, Dict, Any
import requests
from cachetools import TTLCache, cached
from flask import current_app
from threading import Lock


class WeatherService:
    """
    WeatherService: Fetches and caches weather data from a remote API.
    """

    def __init__(self) -> None:
        self.cache = TTLCache(maxsize=1, ttl=900)  # 15 minutes by default
        self.cache_lock = Lock()
        self.config: Optional[dict] = None

    def init_app(self, app):
        self.config = {
            "API_KEY": app.config["WEATHER_API_KEY"],
            "API_URL": app.config["WEATHER_API_URL"],
            "REFRESH_INTERVAL": app.config["WEATHER_REFRESH_INTERVAL"],
        }
        self.cache.ttl = app.config["WEATHER_REFRESH_INTERVAL"]

    def _build_api_url(self) -> str:
        """Constructs the OpenWeatherMap API URL."""
        if not self.config:
            raise RuntimeError("WeatherService not configured")
        return self.config["API_URL"].format(api_key=self.config["API_KEY"])

    def fetch_weather(self) -> Optional[Dict[str, Any]]:
        """Fetch latest weather data from the API."""
        url = self._build_api_url()
        try:
            logging.info(f"Fetching weather data from: {url}")
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return self.parse_weather_data(data)
        except requests.RequestException as e:
            logging.error(f"Failed to fetch weather data: {e}")
            return None
        except Exception as e:
            logging.error(f"WeatherService unexpected error: {e}")
            return None

    def parse_weather_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parses external API response to our internal format.
        Expected fields: city, temp, description, icon, humidity, wind
        """
        try:
            city = data.get("name")
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"].capitalize()
            icon = data["weather"][0]["icon"]
            wind_speed = data["wind"]["speed"]
            return {
                "city": city,
                "temperature": temp,
                "humidity": humidity,
                "description": description,
                "icon": icon,
                "wind_speed": wind_speed,
            }
        except Exception as e:
            logging.error(f"Error parsing weather data: {e}")
            return None

    @cached(cache=lambda self: self.cache)
    def get_weather(self) -> Optional[Dict[str, Any]]:
        """
        Returns the cached weather data or fetches new data if expired.
        Thread-safe access is enforced with self.cache_lock.
        """
        with self.cache_lock:
            data = self.fetch_weather()
            if data:
                self.cache["weather"] = data
            return data

    def refresh_cache(self):
        """Manually refreshes the weather cache (used by scheduler or on demand)."""
        with self.cache_lock:
            logging.info("Refreshing weather cache...")
            data = self.fetch_weather()
            if data:
                self.cache["weather"] = data
                logging.info("Weather cache refreshed.")
            else:
                logging.warning("Could not refresh weather cache; using stale data.")

    def get_cached_weather(self) -> Optional[Dict[str, Any]]:
        """Returns cached weather if available, or fetches if missing."""
        with self.cache_lock:
            data = self.cache.get("weather")
            if data:
                return data
            return self.get_weather()
