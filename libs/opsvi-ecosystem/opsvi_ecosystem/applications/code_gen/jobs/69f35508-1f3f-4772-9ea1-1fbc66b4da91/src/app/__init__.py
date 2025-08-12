"""
Flask App initialization and factory function.
"""
import logging

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .config import Config


def create_app() -> Flask:
    """
    Flask application factory. Sets up config, logging, CSRF, and blueprints.

    Returns:
        Flask: The Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Set up CSRF protection
    CSRFProtect(app)

    from .routes import main_bp

    app.register_blueprint(main_bp)

    from .error_handlers import register_error_handlers

    register_error_handlers(app)

    return app
