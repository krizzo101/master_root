"""
App routes and view logic for Flask Weather Information Web App.
"""
from flask import Blueprint, render_template, request, current_app, flash
from .weather import fetch_weather, WeatherAPIError
from .config import Config
from werkzeug.exceptions import BadRequest

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET", "POST"])
def index():
    """
    Home page: Shows current weather for a location (default or user-input).
    On GET: Shows default weather (from config).
    On POST: Shows weather for user-input location.
    """
    weather = None
    location = ""
    if request.method == "POST":
        # Validate user input
        location = request.form.get("location", "").strip()
        if not location:
            flash("Please enter a location.", "warning")
        else:
            try:
                weather = fetch_weather(location)
            except WeatherAPIError as exc:
                current_app.logger.warning(f"WeatherAPIError: {exc}")
                flash(str(exc), "danger")
            except Exception as exc:
                current_app.logger.error(f"Unexpected error: {exc}")
                flash(
                    "An unexpected error occurred while retrieving weather information.",
                    "danger",
                )
    else:
        # Default page load: show default city weather
        location = Config.DEFAULT_LOCATION
        try:
            weather = fetch_weather(location)
        except WeatherAPIError as exc:
            current_app.logger.warning(f"WeatherAPIError: {exc}")
            flash(str(exc), "danger")
        except Exception as exc:
            current_app.logger.error(f"Unexpected error: {exc}")
            flash(
                "An unexpected error occurred while retrieving weather information.",
                "danger",
            )

    return render_template("index.html", weather=weather, location=location)
