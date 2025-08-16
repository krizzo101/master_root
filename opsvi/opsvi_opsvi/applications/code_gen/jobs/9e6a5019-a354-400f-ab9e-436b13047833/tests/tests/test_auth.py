import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "testkey",
            "SERVER_NAME": "localhost",
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_registration(client):
    resp = client.post(
        "/register",
        data={
            "username": "tester",
            "email": "test@test.com",
            "password": "testpass123",
            "password2": "testpass123",
        },
        follow_redirects=True,
    )
    assert b"Please log in" in resp.data
    user = User.query.filter_by(username="tester").first()
    assert user


def test_login_logout(client):
    # Register first
    client.post(
        "/register",
        data={
            "username": "user1",
            "email": "user1@test.com",
            "password": "secret123",
            "password2": "secret123",
        },
    )
    resp = client.post(
        "/login",
        data={
            "email": "user1@test.com",
            "password": "secret123",
        },
        follow_redirects=True,
    )
    assert b"Login successful" in resp.data
    # Logout
    resp = client.get("/logout", follow_redirects=True)
    assert b"logged out" in resp.data
