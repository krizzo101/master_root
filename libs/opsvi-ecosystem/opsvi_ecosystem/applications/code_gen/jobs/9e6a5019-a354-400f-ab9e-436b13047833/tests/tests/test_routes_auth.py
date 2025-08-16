import pytest
from app import create_app
from flask import url_for
from app.models import User

import os
import bcrypt

@pytest.fixture
 def client():
    app = create_app(None)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            yield client



def test_register_and_login_and_logout_flow(client, monkeypatch):
    # Mock User.query.filter_by for registration validation
    monkeypatch.setattr('app.forms.User.query.filter_by', lambda self, **kwargs: type('Query', (), {'first': lambda: None})())

    # Register new user
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'Password1!',
        'confirm_password': 'Password1!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome' in response.data or b'Registered' in response.data

    # Login with that user
    # Need to mock actual user lookup
    class DummyUser:
        id = 1
        username = 'testuser'
        password_hash = '$2b$12$KIX1qHK9Ylzw/B0KIRQmdOtbydSRsFan.gfPM3xqMOrNsN6nZr4i.'  # bcrypt hash for Password1!
        def verify_password(self, password):
            return password == 'Password1!'

    monkeypatch.setattr('app.models.User.query.filter_by', lambda self, username=None, email=None: type('Query', (), {'first': lambda: DummyUser()})())

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'Password1!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in' in response.data or b'Logout' in response.data

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_profile_access_requires_login(client):
    response = client.get('/profile')
    # Not logged in redirects to login
    assert response.status_code in (302, 401)

