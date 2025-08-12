"""
Flask view routes for the main application functions.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import logging
from .weather_client import get_weather_client, WeatherAPIError
from .config import Config
from werkzeug.exceptions import abort

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/", methods=["GET", "POST"])
def index() -> str:
    """
    Home page: Displays weather info. Handles search form submissions.
    """
    error = None
    weather = None
    last_city = session.get("last_city", Config.DEFAULT_LOCATION)

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            flash("Please enter a city name.", "danger")
            return redirect(url_for("main.index"))
        # Save to session for UX
        session["last_city"] = city
        return redirect(url_for("main.index"))

    # GET: show weather for city in session (or default)
    city_query = last_city

    try:
        client = get_weather_client()
        weather = client.get_weather(city_query)
    except WeatherAPIError as exc:
        error = str(exc)
        weather = None
        logger.error(f"Weather fetch failed: {exc}")
    except Exception as exc:
        error = "Internal server error. Please try again later."
        weather = None
        logger.exception("Unexpected error in weather endpoint.")

    return render_template("index.html", weather=weather, city=city_query, error=error)
