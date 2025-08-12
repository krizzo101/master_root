import pytest
from app.admin_views import SecureModelView

class DummyUser:
    def __init__(self, is_admin=False):
        self.is_admin = is_admin

class DummyAdmin:
    pass

class DummyDB:
    pass

@pytest.fixture
 def secure_model_view():
    view = SecureModelView(model=None, session=None)
    return view



def test_secure_model_view_is_accessible_returns_true_for_admin(monkeypatch, secure_model_view):
    monkeypatch.setattr('flask_login.current_user', DummyUser(is_admin=True))
    assert secure_model_view.is_accessible() is True


def test_secure_model_view_is_accessible_returns_false_for_non_admin(monkeypatch, secure_model_view):
    monkeypatch.setattr('flask_login.current_user', DummyUser(is_admin=False))
    assert secure_model_view.is_accessible() is False


from flask import Flask, redirect

def test_inaccessible_callback():
    app = Flask(__name__)
    with app.test_request_context():
        view = SecureModelView(model=None, session=None)
        response = view.inaccessible_callback('name')
        assert response.status_code in (302, 401)

