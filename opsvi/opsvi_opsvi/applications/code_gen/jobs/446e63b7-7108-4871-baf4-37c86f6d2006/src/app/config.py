"""
Config class for Flask Weather Application
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Application configuration
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "REPLACE_ME_CHANGE_THIS_SECRET")
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
    WEATHER_API_URL = os.environ.get(
        "WEATHER_API_URL", "https://api.openweathermap.org/data/2.5/weather"
    )
    WEATHER_UNITS = os.environ.get("WEATHER_UNITS", "metric")
    WEATHER_DEFAULT_LOCATION = os.environ.get("WEATHER_DEFAULT_LOCATION", "London")
    WEATHER_CACHE_TIMEOUT = int(os.environ.get("WEATHER_CACHE_TIMEOUT", 300))  # seconds
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
