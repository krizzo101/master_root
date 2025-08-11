"""
Main application routes.
"""
import logging
from flask import Blueprint, render_template, request, current_app, flash
from .forms import CitySearchForm
from .weather_client import WeatherAPIClient, WeatherAPIError

main_bp = Blueprint("main", __name__)
logger = logging.getLogger("app.routes")


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """
    Main page: shows city search form and, if available, weather info.
    """
    form = CitySearchForm()
    weather = None
    error = None

    if form.validate_on_submit():
        city = form.city.data.strip()
        logger.info(f"User requested weather for city: {city}")

        client = WeatherAPIClient(
            api_key=current_app.config["OPENWEATHER_API_KEY"],
            timeout=current_app.config["WEATHER_API_TIMEOUT"],
        )
        try:
            weather = client.get_weather_by_city(city)
        except WeatherAPIError as ex:
            error = str(ex)
            logger.warning(f"WeatherAPIError for city\u003d{city}: {error}")
    elif request.method == "POST":
        error = "Invalid city name. Please try again."

    return render_template("index.html", form=form, weather=weather, error=error)
