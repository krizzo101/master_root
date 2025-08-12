"""
Centralized error handler registrations for the Flask app.
"""
import logging

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """
    Registers custom error handlers for the Flask app.
    :param app: Flask app instance
    """
    logger = logging.getLogger("error_handlers")

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 Not Found: {error}")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Server Error: {error}")
        return render_template("500.html"), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        logger.error(f"Unhandled exception: {e}")
        return render_template("error.html", message=str(e)), code
