"""
Error handling for the Flask web application. Registers custom error handlers.
"""
from flask import render_template
from werkzeug.exceptions import HTTPException
import logging


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"Internal server error: {error}")
        return render_template("500.html"), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        code = 500
        if isinstance(e, HTTPException):
            code = e.code
        logging.error(f"Unhandled exception ({code}): {e}")
        return render_template("500.html"), code
