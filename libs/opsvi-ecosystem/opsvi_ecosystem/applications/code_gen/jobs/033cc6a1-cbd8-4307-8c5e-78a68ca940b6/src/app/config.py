"""
Application configuration using environment variables (dotenv).
"""
import os

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class Config:
    """
    App configuration class. Loaded from environment variables.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-default-key")
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
    WEATHER_API_BASE_URL = os.environ.get(
        "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5/weather"
    )
    # Example: https://api.openweathermap.org/data/2.5/weather
    DEFAULT_LOCATION = os.environ.get("DEFAULT_LOCATION", "London")
    WEATHER_UNITS = os.environ.get("WEATHER_UNITS", "metric")
    # Set max query timeout in seconds
    WEATHER_API_TIMEOUT = int(os.environ.get("WEATHER_API_TIMEOUT", "4"))
