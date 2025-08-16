"""
App global error handler setup.
"""
import logging

from flask import Flask, render_template


def register_error_handlers(app: Flask) -> None:
    """
    Register generic error handlers.
    Args:
        app (Flask): Flask app instance.
    """
    logger = logging.getLogger("app.error_handlers")

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 Not Found: {error}")
        return (
            render_template(
                "error.html",
                title="Not Found",
                message="The page you requested could not be found.",
            ),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Server Error: {error}")
        return (
            render_template(
                "error.html",
                title="Server Error",
                message="An internal error occurred. Please try again later.",
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_all_exceptions(error):
        logger.exception(f"Unhandled Exception: {error}")
        return (
            render_template(
                "error.html",
                title="Unexpected Error",
                message="An unexpected error occurred.",
            ),
            500,
        )
