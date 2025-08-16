"""
UI routes (Jinja2 views) for Flask Weather App
"""
import logging
from flask import Blueprint, render_template, request, current_app, flash

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def home():
    """
    Home page. Allows user to view or request weather info for a location.
    POST to enter new city name.
    """
    weather_service = current_app.weather_service
    location = current_app.config["WEATHER_DEFAULT_LOCATION"]
    weather = None
    error = None
    if request.method == "POST":
        location = request.form.get("location", "").strip()
        if not location:
            error = "Please enter a location."
        else:
            try:
                weather = weather_service.fetch_weather(location)
            except Exception as ex:
                logging.exception("Failed to get weather for user input")
                error = str(ex)
    else:
        # GET: default location
        try:
            weather = weather_service.fetch_weather(location)
        except Exception as ex:
            logging.exception("Failed to get weather for default location")
            error = str(ex)
    return render_template(
        "index.html", weather=weather, location=location, error=error
    )
