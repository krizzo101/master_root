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



from flask import g

def test_restrict_admin_access(monkeypatch, client):
    # Simulate non-admin user
    monkeypatch.setattr('flask.g', type('G', (), {'user': type('User', (), {'is_admin': False})()})())
    response = client.get('/admin/restrict')
    # Should redirect or abort
    assert response.status_code in (302, 403)

    # Simulate admin user
    monkeypatch.setattr('flask.g', type('G', (), {'user': type('User', (), {'is_admin': True})()})())
    response = client.get('/admin/restrict')
    assert response.status_code == 200 or response.status_code == 302


def test_admin_dashboard_displays_content(client, monkeypatch):
    # Setup any mocks for analytics or dashboard data
    response = client.get('/admin/dashboard')
    # Should respond OK
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data

