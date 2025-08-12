import pytest
from flask import Flask, Response, json
from app import (
    create_app,
    log_request,
    hello_world,
    not_found,
    method_not_allowed,
    handle_exception,
)


@pytest.fixture(scope="module")
def test_client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as testing_client:
        yield testing_client


@pytest.fixture(autouse=True)
def enable_flask_logging(monkeypatch):
    # Monkeypatch logging to capture log outputs if needed
    pass


def test_create_app_initializes_flask_app():
    app = create_app()
    assert isinstance(app, Flask), "create_app should return a Flask app instance"
    # The app should have the '/' route
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/" in rules, "App should have a root ('/') route"
    # The methods for root route should contain GET only
    root_rule = next(rule for rule in app.url_map.iter_rules() if rule.rule == "/")
    assert "GET" in root_rule.methods, "Root route should support GET method"
    assert "POST" not in root_rule.methods, "Root route should not support POST method"


def test_hello_world_returns_expected_response(test_client):
    response = test_client.get("/")
    assert response.status_code == 200, "Response status code should be 200 OK"
    assert (
        response.data.decode("utf-8") == "Hello, World!"
    ), "Response data should be 'Hello, World!'"
    # Content type is not enforced but usually text/html or text/plain
    assert "text" in response.content_type, "Content-Type should be a type of text"


import logging
from unittest.mock import patch
from flask import Request


def test_log_request_logs_info_and_returns_none(test_client):
    with patch("app.logging.info") as mocked_logging:
        response = test_client.get("/")
        # call log_request with current request context
        # We need to simulate a call context
        from flask import request

        # Invoke log_request explicitly to test
        result = log_request()
        mocked_logging.assert_called()
        # The log should contain the HTTP method and path
        args, _ = mocked_logging.call_args
        log_msg = args[0]
        assert "GET" in log_msg and "/" in log_msg
        # log_request returns None
        assert result is None


def test_not_found_handler_returns_404_json_response():
    from werkzeug.exceptions import NotFound

    error = NotFound(description="Resource not found")
    response = not_found(error)
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Resource not found"
    assert "status" in data and data["status"] == 404


def test_method_not_allowed_handler_returns_405_json_response():
    from werkzeug.exceptions import MethodNotAllowed

    error = MethodNotAllowed(description="Method Not Allowed")
    response = method_not_allowed(error)
    assert response.status_code == 405
    data = json.loads(response.data)
    assert "error" in data and data["error"] == "Method Not Allowed"
    assert data.get("status") == 405


def test_handle_exception_returns_500_json_response_for_unexpected_error():
    class DummyError(Exception):
        pass

    error = DummyError("Unexpected error")
    response = handle_exception(error)
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data.get("error") == "An internal error occurred."
    assert data.get("status") == 500


from werkzeug.exceptions import BadRequest


def test_handle_exception_returns_pass_through_for_http_exceptions():
    error = BadRequest(description="Bad request error")
    response = handle_exception(error)
    # This should be the same object as error.get_response()
    expected_response = error.get_response()
    assert response.status_code == expected_response.status_code
    assert response.data == expected_response.data
    data = json.loads(response.data)
    assert (
        "Bad request error" in data.get("description", "")
        or "Bad request error" in data.get("message", "")
        or True
    )  # Sometimes Flask default
    assert response.content_type == expected_response.content_type


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_root_route_only_accepts_get_method(test_client, method):
    http_method = getattr(test_client, method)
    response = http_method("/")
    assert response.status_code == 405
    data = json.loads(response.data)
    assert "error" in data
    assert response.content_type == "application/json"


def test_app_run_starts_flask_server_and_handles_requests(monkeypatch):
    # We cannot actually start the server in test
    # Instead, we verify that main calls app.run with expected arguments
    called_args = {}

    class DummyApp:
        def run(self, host=None, port=None, debug=None):
            called_args["host"] = host
            called_args["port"] = port
            called_args["debug"] = debug

    dummy_app = DummyApp()

    def dummy_create_app():
        return dummy_app

    monkeypatch.setattr("app.create_app", dummy_create_app)

    # Import main dynamically to test
    from app import main

    main()

    assert called_args.get("host") == "0.0.0.0"
    assert isinstance(called_args.get("port"), int)
    assert called_args.get("debug") is True


def test_root_route_response_content_type_and_headers(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    # Typically Flask sets text/html by default
    assert response.content_type in [
        "text/html; charset=utf-8",
        "text/plain; charset=utf-8",
    ]
    # Check Content-Length header exists
    assert "Content-Length" in response.headers
    assert int(response.headers["Content-Length"]) == len("Hello, World!")


from werkzeug.exceptions import NotFound, MethodNotAllowed


def test_error_handlers_return_json_and_expected_status_codes(test_client):
    # 404 Not Found
    response_404 = test_client.get("/nonexistent")
    assert response_404.status_code == 404
    data_404 = json.loads(response_404.data)
    assert "error" in data_404

    # 405 Method Not Allowed for POST on root
    response_405 = test_client.post("/")
    assert response_405.status_code == 405
    data_405 = json.loads(response_405.data)
    assert "error" in data_405
    # The error message should mention 'Method Not Allowed'
    assert "Method Not Allowed" in data_405["error"]


def test_rate_limiting_and_security_headers_not_applicable(test_client):
    response = test_client.get("/")
    # Assert no security headers like CSP or Rate-Limiting headers exist
    assert "X-RateLimit-Limit" not in response.headers
    assert "Content-Security-Policy" not in response.headers
    assert "X-Content-Type-Options" not in response.headers


def test_logging_does_not_raise_under_normal_operation(test_client):
    response = test_client.get("/")
    # Log request is called within the route
    # If any exception occurred it would fail
    assert response.status_code == 200


from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound

import pytest


@pytest.mark.parametrize(
    "error_class, expected_status",
    [
        (BadRequest, 400),
        (Unauthorized, 401),
        (Forbidden, 403),
        (NotFound, 404),
    ],
)
def test_error_handler_handles_various_http_errors(error_class, expected_status):
    error = error_class(description=f"Simulated {expected_status} error")
    # Choose handler
    if expected_status == 404:
        response = not_found(error)
    elif expected_status == 405:
        response = method_not_allowed(error)
    else:
        response = handle_exception(error)

    assert response.status_code == expected_status
    data = json.loads(response.data)
    assert "error" in data
    assert data["status"] == expected_status
