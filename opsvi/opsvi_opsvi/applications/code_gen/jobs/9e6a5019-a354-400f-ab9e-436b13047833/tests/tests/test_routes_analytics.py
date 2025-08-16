import pytest
from app import create_app

import json

@pytest.fixture
 def client():
    app = create_app(None)
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            yield client



def test_post_views_stat_returns_data(client):
    response = client.get('/analytics/post_views')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_trending_posts_returns_list(client):
    response = client.get('/analytics/trending_posts')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

