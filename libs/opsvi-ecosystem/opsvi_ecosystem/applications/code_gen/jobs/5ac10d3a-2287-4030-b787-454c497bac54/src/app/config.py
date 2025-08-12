"""
Configuration settings for Flask Weather Information Web App.
"""
import os
from typing import Final


class Config:
    """
    Base configuration class for the Flask application.
    Reads API key and relevant configs from environment variables.
    """

    SECRET_KEY: Final[str] = os.environ.get("SECRET_KEY", "change-this-secret-key")
    WEATHER_API_KEY: Final[str] = os.environ.get(
        "WEATHER_API_KEY", ""
    )  # OpenWeatherMap API key
    WEATHER_API_URL: Final[str] = os.environ.get(
        "WEATHER_API_URL", "https://api.openweathermap.org/data/2.5/weather"
    )
    DEFAULT_LOCATION: Final[str] = os.environ.get("DEFAULT_LOCATION", "London")
    # Timeout for HTTP requests to weather API (seconds)
    WEATHER_API_TIMEOUT: Final[int] = int(os.environ.get("WEATHER_API_TIMEOUT", "5"))
