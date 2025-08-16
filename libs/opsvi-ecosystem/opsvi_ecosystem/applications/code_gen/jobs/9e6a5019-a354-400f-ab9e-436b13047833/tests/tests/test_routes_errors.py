import pytest
from app import create_app

import sys

@pytest.fixture
 def client():
    app = create_app(None)
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            yield client



def test_page_not_found_returns_404_template(client):
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data or b'404' in response.data


def test_internal_error_returns_500(client, monkeypatch):
    @client.application.route('/trigger_500')
    def trigger_500():
        raise Exception('Test 500')

    response = client.get('/trigger_500')
    assert response.status_code == 500
    assert b'Internal Server Error' in response.data or b'500' in response.data

