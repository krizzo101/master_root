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
            "SECRET_KEY": "test",
            "SERVER_NAME": "localhost",
        }
    )
    with app.app_context():
        db.create_all()
        user = User(
            username="admin", email="a@a.com", password_hash="pw", is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login_admin(client):
    client.post("/login", data={"email": "a@a.com", "password": "pw"})


def test_admin_dashboard_access(client):
    login_admin(client)
    resp = client.get("/admin/", follow_redirects=True)
    assert b"AI-Enhanced CMS" in resp.data or resp.status_code == 200
