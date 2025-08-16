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



def test_create_post_requires_login_and_creates_post(client, monkeypatch):
    # Simulate logged-in user by setting user_id in session
    with client.session_transaction() as session:
        session['user_id'] = 1

    monkeypatch.setattr('app.routes.posts.PostForm.validate_on_submit', lambda self: True)
    monkeypatch.setattr('app.routes.posts.PostForm.title', 'Test Title')
    monkeypatch.setattr('app.routes.posts.PostForm.content', 'Test content')

    monkeypatch.setattr('app.routes.posts.db', type('DB', (), {'session': type('Session', (), {'add': lambda self, x: None, 'commit': lambda self: None})()})())

    response = client.post('/post/create', data={'title': 'Test Title', 'content': 'Test content'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Title' in response.data


def test_edit_post_loads_and_updates(client, monkeypatch):
    with client.session_transaction() as session:
        session['user_id'] = 1

    class DummyPost:
        id = 1
        title = 'Old Title'
        content = 'Old content'
        author_id = 1
        def save(self):
            return True

    monkeypatch.setattr('app.routes.posts.Post.query.get_or_404', staticmethod(lambda post_id: DummyPost()))
    monkeypatch.setattr('app.routes.posts.PostForm.validate_on_submit', lambda self: True)
    monkeypatch.setattr('app.routes.posts.db', type('DB', (), {'session': type('Session', (), {'commit': lambda self: None})()})())

    response = client.post('/post/1/edit', data={
        'title': 'Updated Title',
        'content': 'Updated content'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Updated Title' in response.data


def test_delete_post_deletes_post_and_redirects(client, monkeypatch):
    with client.session_transaction() as session:
        session['user_id'] = 1

    class DummyPost:
        author_id = 1
    
    monkeypatch.setattr('app.routes.posts.Post.query.get_or_404', staticmethod(lambda post_id: DummyPost()))
    monkeypatch.setattr('app.routes.posts.db', type('DB', (), {'session': type('Session', (), {'delete': lambda self, x: None, 'commit': lambda self: None})()})())

    response = client.post('/post/1/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Post deleted' in response.data or b'Deleted' in response.data

