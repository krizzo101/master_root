import pytest
from app import create_app


@pytest.fixture
def test_create_app_returns_flask_app_instance():
    """Verify that create_app() creates a Flask app with expected properties."""
    app = create_app()
    assert app is not None
    # Flask apps have attribute 'test_client'
    assert hasattr(app, "test_client")
    # Test app config has DEBUG and TESTING keys (typical config keys)
    assert "DEBUG" in app.config
    assert "TESTING" in app.config
