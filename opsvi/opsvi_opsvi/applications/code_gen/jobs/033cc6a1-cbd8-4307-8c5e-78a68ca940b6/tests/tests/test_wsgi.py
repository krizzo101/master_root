import pytest
import wsgi


def test_wsgi_app_is_flask_app_instance():
    assert hasattr(wsgi, "app")
    # Simple attribute check
    assert hasattr(wsgi.app, "test_client")
