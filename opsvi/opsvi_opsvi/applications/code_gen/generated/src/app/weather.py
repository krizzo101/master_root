"""
Weather service client: Handles external API communication and data transformation for weather information.
"""
import requests
from typing import Any, Dict, Optional
from flask import current_app


class WeatherAPIError(Exception):
    """
    Raised when there is a failure to retrieve weather information from the API.
    """

    pass


def kelvin_to_celsius(kelvin: float) -> float:
    """
    Convert Kelvin temperature to Celsius.
    Args:
        kelvin (float): Temperature in Kelvin.
    Returns:
        float: Temperature in Celsius, rounded to one decimal.
    """
    return round(kelvin - 273.15, 1)


def fetch_weather(location: str) -> Dict[str, Any]:
    """
    Fetch current weather data for a given location from OpenWeatherMap API.
    Args:
        location (str): City name or city,country code (e.g., 'London', 'London,UK').
    Returns:
        Dict[str, Any]: Weather data as a normalized dictionary.
    Raises:
        WeatherAPIError: If any API or connection error occurs.
    """
    api_key: Optional[str] = current_app.config.get("WEATHER_API_KEY")
    base_url: str = current_app.config.get("WEATHER_API_URL")
    timeout: int = current_app.config.get("WEATHER_API_TIMEOUT", 5)

    if not api_key:
        raise WeatherAPIError("Weather API key is not configured.")

    params = {"q": location, "appid": api_key, "lang": "en"}
    try:
        resp = requests.get(base_url, params=params, timeout=timeout)
        resp.raise_for_status()
    except requests.Timeout:
        current_app.logger.error(
            f"Weather API request timed out for location '{location}'"
        )
        raise WeatherAPIError(
            "Weather service request timed out. Please try again later."
        )
    except requests.RequestException as exc:
        current_app.logger.error(f"Weather API request error: {exc}")
        raise WeatherAPIError(
            "Failed to connect to the weather service. Please try again later."
        ) from exc

    try:
        data = resp.json()
    except Exception as exc:
        current_app.logger.error(f"Error decoding weather API JSON: {exc}")
        raise WeatherAPIError("Invalid response from weather service.") from exc

    # Check for API-level errors
    if data.get("cod") != 200:
        message = data.get("message", "Unknown error.")
        current_app.logger.warning(
            f"Weather API returned error for location '{location}': {message}"
        )
        raise WeatherAPIError(
            f"Weather service error: {message.capitalize()} ({data.get('cod')})"
        )

    normalized = {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": kelvin_to_celsius(data["main"]["temp"]),
        "condition": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "icon": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
    }
    return normalized
