"""
App factory for the Weather Flask web application.
Sets up extensions, blueprints, error handlers, and configuration.
"""
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_apscheduler import APScheduler
import logging
import os
from .weather_service import WeatherService

csrf = CSRFProtect()
scheduler = APScheduler()
weather_service = WeatherService()

# Content Security Policy
CSP = {
    "default-src": [
        "'self'",
        "cdnjs.cloudflare.com",
        "cdn.jsdelivr.net",
        "stackpath.bootstrapcdn.com",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
    ],
    "img-src": "'self' data:",
}


def create_app(config_object=None) -> Flask:
    """
    Application factory to create Flask app with extensions and blueprints.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("app.config.DefaultConfig")
    if config_object:
        app.config.from_object(config_object)
    if "WEATHER_API_KEY" in os.environ:
        app.config["WEATHER_API_KEY"] = os.environ["WEATHER_API_KEY"]
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize extensions
    csrf.init_app(app)
    Talisman(app, content_security_policy=CSP)
    scheduler.init_app(app)
    scheduler.start()

    # Store weather service globally (for DI in tests)
    app.weather_service = weather_service
    weather_service.init_app(app)

    # Register blueprints
    from .routes import main as main_blueprint

    app.register_blueprint(main_blueprint)

    # Register error handlers
    from .errors import register_error_handlers

    register_error_handlers(app)

    # Schedule periodic cache job
    scheduler.add_job(
        id="refresh_weather_cache",
        func=weather_service.refresh_cache,
        trigger="interval",
        seconds=app.config["WEATHER_REFRESH_INTERVAL"],
        replace_existing=True,
    )

    return app
