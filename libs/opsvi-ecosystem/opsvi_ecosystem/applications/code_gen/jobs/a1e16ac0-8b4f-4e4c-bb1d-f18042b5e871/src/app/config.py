"""
Configuration module for Weather Flask web app.
Secrets can be injected via environment variables.
"""
import os


class DefaultConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-me")
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", "csrf-secret-key")
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "demo-weather-api-key")
    WEATHER_API_URL = os.environ.get(
        "WEATHER_API_URL",
        "https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}&units=metric",
    )
    WEATHER_REFRESH_INTERVAL = int(
        os.environ.get("WEATHER_REFRESH_INTERVAL", 900)
    )  # seconds
    WTF_CSRF_TIME_LIMIT = 7200
    SCHEDULER_API_ENABLED = True
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set True in production
    REMEMBER_COOKIE_HTTPONLY = True
