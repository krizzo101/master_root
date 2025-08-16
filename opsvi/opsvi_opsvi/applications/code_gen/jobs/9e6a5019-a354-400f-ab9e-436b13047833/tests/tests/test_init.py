import pytest
from app import create_app, setup_error_handlers
from flask import Flask


def test_create_app_with_default_config_creates_flask_app():
    app = create_app(None)
    assert isinstance(app, Flask)
    assert app.config is not None
    assert app.debug is False


class TestConfig:
    TESTING = True


def test_create_app_with_custom_config_class_sets_config():
    app = create_app(TestConfig)
    assert app.config["TESTING"] is True


def test_setup_error_handlers_registers_error_handlers():
    app = create_app(None)
    setup_error_handlers(app)

    # Flask stores error handlers in app.error_handler_spec pre Flask2, newer Flask uses app.error_handler_spec
    # We can test by invoking handlers directly or via test client

    client = app.test_client()

    # Trigger 404
    response_404 = client.get("/nonexistentpage")
    assert response_404.status_code == 404

    # To test 500, create route that raises Exception
    @app.route("/error500")
    def error500():
        raise Exception("Test 500 error")

    response_500 = client.get("/error500")
    # Flask's debug mode off should handle exception and return 500
    assert response_500.status_code == 500
