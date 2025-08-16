import pytest
from app.middleware import error_handling
from fastapi import FastAPI
from starlette.testclient import TestClient


@pytest.fixture
def app_with_error_handlers():
    app = FastAPI()

    # Example endpoint to raise exception for testing
    @app.get("/error")
    def error_endpoint():
        raise ValueError("Test error")

    error_handling.add_exception_handlers(app)
    return app


@pytest.fixture
def client(app_with_error_handlers):
    return TestClient(app_with_error_handlers)


def test_add_exception_handlers_catches_valueerror(client):
    response = client.get("/error")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Test error" in data["detail"]
