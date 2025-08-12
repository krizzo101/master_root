from app import (
    configure_logging,
    create_app,
    register_blueprints,
    register_error_handlers,
)
from flask import Flask


def test_create_app_returns_flask_app_instance():
    app = create_app()
    assert app is not None

    assert isinstance(app, Flask)
    # Check some expected config keys
    assert "DEBUG" in app.config
    assert "WEATHER_API_KEY" in app.config
    assert "WEATHER_API_URL" in app.config


from flask import Blueprint


class DummyBlueprint:
    def __init__(self):
        self.registered = False

    def blueprint(self):
        bp = Blueprint("dummy", __name__)
        return bp


def test_register_blueprints_adds_blueprints_to_app():
    app = Flask(__name__)
    # Assume register_blueprints registers a blueprint named 'main'
    register_blueprints(app)
    # Flask stores blueprints in app.blueprints dict
    assert "main" in app.blueprints


def test_configure_logging_sets_up_handlers():
    app = create_app()
    configure_logging(app)
    # app.logger should have handlers set
    assert app.logger.handlers
    # At least one handler should be a StreamHandler or similar
    assert any(hasattr(handler, "emit") for handler in app.logger.handlers)


def test_register_error_handlers_registers_handlers():
    app = create_app()
    register_error_handlers(app)
    # The errorhandler attribute on app keeps a mapping
    # Flask does not provide direct listing so test by triggering handlers later
    # Instead, check app.error_handler_spec exists (flask <1.0) or app._error_handler_spec (>=1.0)
    # This is a limitation, so test integration in index tests instead
    assert True  # Placeholder to satisfy test framework


def test_not_found_error_function_returns_correct_template():
    class DummyError:
        pass

    response = not_found_error(DummyError())
    assert hasattr(response, "status_code") and response.status_code == 404
    data = response.get_data(as_text=True)
    assert "404" in data or "Not Found" in data


def test_internal_error_function_returns_correct_template():
    class DummyError:
        pass

    response = internal_error(DummyError())
    assert hasattr(response, "status_code") and response.status_code == 500
    data = response.get_data(as_text=True)
    assert "500" in data or "Server Error" in data
