import pytest
from app import create_app, db
from app.models import Category, Post, Tag, User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "another_key",
            "SERVER_NAME": "localhost",
        }
    )
    with app.app_context():
        db.create_all()
        cat = Category(name="TestCat")
        tag = Tag(name="TestTag")
        user = User(username="foo", email="foo@test.com", password_hash="pass")
        db.session.add_all([cat, tag, user])
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    client.post("/login", data={"email": "foo@test.com", "password": "pass"})


def test_create_post(client):
    login(client)
    resp = client.post(
        "/posts/create",
        data={
            "title": "Hello world",
            "content": "This is <b>content</b>.",
            "categories": [1],
            "tags": [1],
        },
        follow_redirects=True,
    )
    assert b"Post created" in resp.data
    post = Post.query.filter_by(title="Hello world").first()
    assert post is not None
