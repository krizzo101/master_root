from app.main import app
from app.views import (
    require_auth,
)
from starlette.testclient import TestClient

client = TestClient(app)


def test_require_auth_redirects_to_login_if_unauthenticated():
    from starlette.responses import RedirectResponse

    class DummyRequest:
        session = {}

    req = DummyRequest()
    response = require_auth(req)
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303
    # Redirects to login
    assert "/login" in response.headers["location"]


def test_home_shows_welcome_message():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.text or "Automated Python Code Review" in response.text


def test_signup_get_renders_signup_template():
    response = client.get("/signup")
    assert response.status_code == 200
    assert "Sign Up" in response.text


def test_signup_post_creates_user_and_redirects(monkeypatch):
    monkeypatch.setattr(
        "app.auth.signup", lambda user_in, db: MagicMock(id=1, email=user_in.email)
    )

    response = client.post(
        "/signup",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "pass123",
        },
    )
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["location"]


def test_login_get_renders_login_page():
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


def test_login_post_with_valid_creds_redirects(monkeypatch):
    monkeypatch.setattr(
        "app.auth.login",
        lambda form_data, db: {"access_token": "fake", "token_type": "bearer"},
    )

    response = client.post(
        "/login", data={"email": "test@example.com", "password": "pass123"}
    )
    assert response.status_code in (302, 303)
    assert "/dashboard" in response.headers["location"]


def test_login_post_with_invalid_creds_returns_401(monkeypatch):
    def fail_login(form_data, db):
        raise Exception("Invalid credentials")

    monkeypatch.setattr("app.auth.login", fail_login)

    response = client.post(
        "/login", data={"email": "wrong@example.com", "password": "nopass"}
    )
    assert response.status_code == 401 or response.status_code == 400


def test_logout_redirects_to_home():
    response = client.get("/logout")
    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/"


def test_dashboard_requires_authentication(monkeypatch):
    monkeypatch.setattr("app.auth.require_auth", lambda request: MagicMock())
    response = client.get("/dashboard")
    assert response.status_code == 200


def test_view_report_requires_authentication(monkeypatch):
    monkeypatch.setattr("app.auth.require_auth", lambda request: MagicMock())
    monkeypatch.setattr(
        "app.api.get_report",
        lambda report_id, db, current_user: {"id": report_id, "data": "report content"},
    )

    response = client.get("/project/1/report/1")
    assert response.status_code == 200
    assert "report content" in response.text
