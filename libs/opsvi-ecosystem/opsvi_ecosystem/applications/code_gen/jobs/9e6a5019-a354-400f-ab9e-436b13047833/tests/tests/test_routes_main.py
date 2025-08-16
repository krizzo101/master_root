import pytest
from app import create_app
from flask import url_for

import os

@pytest.fixture
 def client():
    app = create_app(None)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            yield client



def test_homepage_renders_successfully_with_posts(client):
    response = client.get(url_for('main.homepage'))
    assert response.status_code == 200
    assert b'Blog' in response.data or b'Posts' in response.data


def test_post_detail_renders_existing_post_and_404_for_missing(client, monkeypatch):
    # Patch query.get_or_404 to simulate post exists
    class DummyPost:
        id = 1
        title = 'Test Post'
        body = 'Test content'

    def get_or_404(post_id):
        if post_id == 1:
            return DummyPost()
        else:
            from flask import abort
            abort(404)

    monkeypatch.setattr('app.routes.main.Post.query.get_or_404', staticmethod(get_or_404))

    response = client.get('/post/1')
    assert response.status_code == 200
    assert b'Test Post' in response.data

    response_404 = client.get('/post/9999')
    assert response_404.status_code == 404


def test_about_page_renders_ok(client):
    response = client.get('/about')
    assert response.status_code == 200
    assert b'About' in response.data

