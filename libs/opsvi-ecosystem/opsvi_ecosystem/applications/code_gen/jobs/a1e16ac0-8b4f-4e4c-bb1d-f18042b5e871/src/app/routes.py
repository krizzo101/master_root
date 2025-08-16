"""
Main blueprint containing the app's routes for weather display, refresh API, index, and favicon.
"""
import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import generate_csrf
from wtforms import SubmitField

from .weather_service import WeatherService

main = Blueprint("main", __name__)


class RefreshWeatherForm(FlaskForm):
    refresh = SubmitField("Refresh")


@main.route("/", methods=["GET", "POST"])
def index():
    weather_service: WeatherService = current_app.weather_service
    form = RefreshWeatherForm()
    error_msg = None
    if form.validate_on_submit():
        try:
            weather_service.refresh_cache()
            flash("Weather data manually refreshed.", "success")
            return redirect(url_for("main.index"))
        except Exception as e:
            logging.error(f"Manual refresh failed: {e}")
            error_msg = "Failed to refresh weather data. Please try again."

    weather = weather_service.get_cached_weather()
    if not weather:
        error_msg = "Could not retrieve weather data at this time."
    return render_template(
        "index.html",
        weather=weather,
        form=form,
        error_msg=error_msg,
        csrf_token=generate_csrf(),
    )


@main.route("/api/weather", methods=["GET"])
def api_weather():
    weather_service: WeatherService = current_app.weather_service
    weather = weather_service.get_cached_weather()
    if not weather:
        return (
            jsonify({"success": False, "message": "Unable to fetch weather data."}),
            503,
        )
    return jsonify({"success": True, "weather": weather})


@main.route("/favicon.ico")
def favicon():
    import os

    from flask import send_from_directory

    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
