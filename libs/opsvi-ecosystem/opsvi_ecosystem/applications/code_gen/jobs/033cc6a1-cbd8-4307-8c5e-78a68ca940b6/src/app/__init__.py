"""
Flask application factory module.
Initializes Flask app and loads configurations.
"""
import logging
from flask import Flask
from .config import Config


def create_app() -> Flask:
    """
    App factory for Weather Information Web App.
    :return: Configured Flask app.
    """
    app = Flask(__name__, static_url_path="/static")
    app.config.from_object(Config)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
    )

    from .views import main_bp

    app.register_blueprint(main_bp)

    # Error handlers
    from .errors import register_error_handlers

    register_error_handlers(app)

    return app
