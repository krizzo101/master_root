"""
App configuration classes.
"""
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    WTF_CSRF_ENABLED = True
    # OpenWeatherMap API Key must be set as env var in deployment
e = os.environ.get('OPENWEATHER_API_KEY')
    if not e:
        # In production, force it via environment variable
        raise RuntimeError(
            'OPENWEATHER_API_KEY environment variable must be set!'
        )
    OPENWEATHER_API_KEY = e
    # (Optional) default timeout for requests
    WEATHER_API_TIMEOUT = 5
