"""
Initialize Flask app, extensions, and configuration
"""
import logging

from cachelib import SimpleCache
from flask import Flask
from flask_restful import Api

from .weather import WeatherService


def create_app() -> Flask:
    """
    Application factory for Flask Weather App.
    """
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # Setup logging
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    )

    # Initialize SimpleCache
    cache = SimpleCache()

    # Register WeatherService as app extension
    app.weather_service = WeatherService(app, cache)

    api = Api(app)

    # Import and register blueprints/routes
    from .api import WeatherResource
    from .views import main_bp

    app.register_blueprint(main_bp)
    api.add_resource(
        WeatherResource,
        "/api/weather",
        resource_class_kwargs={"weather_service": app.weather_service},
    )

    # Register error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask) -> None:
    """
    Register HTTP error handlers.
    """
    from flask import render_template

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html", error=error), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html", error=error), 500
