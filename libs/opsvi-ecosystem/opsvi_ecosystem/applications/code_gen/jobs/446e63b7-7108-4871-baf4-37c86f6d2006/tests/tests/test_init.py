import pytest
from app import create_app, register_error_handlers
from flask import Flask


@pytest.fixture
def app():
    app = create_app()
    register_error_handlers(app)
    app.testing = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_create_app_returns_flask_app_instance():
    app = create_app()
    assert app is not None
    assert hasattr(app, "route")
    assert app.config.get("TESTING", False) == True or app.testing == True


def test_register_error_handlers_registers_handlers_correctly():
    app = Flask(__name__)
    register_error_handlers(app)
    assert 404 in app.error_handler_spec[None]
    assert 500 in app.error_handler_spec[None]


def test_not_found_returns_404_response(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert b"404" in response.data
    assert b"Not Found" in response.data


def test_server_error_returns_500_response(client):
    @client.application.route("/error")
    def error():
        raise Exception("Test Exception")

    response = client.get("/error")
    assert response.status_code == 500
    assert b"500" in response.data
    assert b"Server Error" in response.data
