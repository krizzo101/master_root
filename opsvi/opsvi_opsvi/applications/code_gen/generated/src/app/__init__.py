"""
Application package initializer for Flask Weather Information Web App.
"""
import logging
from flask import Flask
from .config import Config


def create_app() -> Flask:
    """
    Flask application factory.
    Returns:
        Flask: Configured Flask app instance.
    """
    app = Flask(__name__, static_folder="static")
    app.config.from_object(Config)

    configure_logging(app)
    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints.
    Args:
        app (Flask): The Flask application.
    """
    from .routes import main_bp

    app.register_blueprint(main_bp)


def configure_logging(app: Flask) -> None:
    """
    Configure application-wide logging.
    Args:
        app (Flask): The Flask application.
    """
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_error_handlers(app: Flask) -> None:
    """
    Register common error handlers.
    Args:
        app (Flask): The Flask application.
    """
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {error}")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Internal Server Error: {error}")
        return render_template("500.html"), 500
