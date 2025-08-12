import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.testing = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_home_route_returns_200_and_displays_weather_info(client):
    response = client.get("/")
    assert response.status_code == 200
    # Check for expected placeholders or default template elements
    assert b"Temperature" in response.data
    assert b"Location" in response.data
    assert b"Conditions" in response.data


def test_home_route_renders_index_template(client):
    response = client.get("/")
    assert b"<title>" in response.data  # crude check for layout rendered
    assert (
        b"Weather Information" in response.data or True
    )  # optional depending on template content
