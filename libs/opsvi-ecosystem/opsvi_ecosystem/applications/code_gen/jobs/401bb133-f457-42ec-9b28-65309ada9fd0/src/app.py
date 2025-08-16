"""
Flask Hello World Web API
------------------------
A simple, production-ready Flask application that exposes a single GET route at '/'.
Returns 'Hello, World!' as the response.
"""

import logging

from flask import Flask, Response, request


def create_app() -> Flask:
    """
    Factory to create and configure the Flask web application.

    Returns:
        Flask: A configured Flask app instance.
    """
    app = Flask(__name__)

    # Configure logging for the application
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    @app.before_request
    def log_request():
        logger.info(f"Received {request.method} request at {request.path}")

    @app.route("/", methods=["GET"])
    def hello_world() -> Response:
        """
        GET endpoint for the root path. Returns 'Hello, World!'.

        Returns:
            Response: Flask text response.
        """
        return Response("Hello, World!", status=200, mimetype="text/plain")

    @app.errorhandler(404)
    def not_found(error) -> Response:
        logger.warning(f"404 Not Found: {request.path}")
        return Response("Not Found", status=404, mimetype="text/plain")

    @app.errorhandler(405)
    def method_not_allowed(error) -> Response:
        logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
        return Response("Method Not Allowed", status=405, mimetype="text/plain")

    @app.errorhandler(Exception)
    def handle_exception(error) -> Response:
        logger.error(f"Unhandled Exception: {error}")
        return Response("Internal Server Error", status=500, mimetype="text/plain")

    return app


def main() -> None:
    """
    Entrypoint for running the Flask development server.
    """
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
