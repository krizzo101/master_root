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



def test_api_get_posts_returns_json_array(client):
    response = client.get('/api/posts')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_api_get_post_behavior(client):
    response = client.get('/api/post/1')
    if response.status_code == 200:
        data = response.get_json()
        assert 'id' in data
        assert data['id'] == 1
    else:
        assert response.status_code == 404


def test_api_get_tags_and_categories(client):
    response_tags = client.get('/api/tags')
    response_cats = client.get('/api/categories')

    assert response_tags.status_code == 200
    assert isinstance(response_tags.get_json(), list)

    assert response_cats.status_code == 200
    assert isinstance(response_cats.get_json(), list)


def test_api_analytics_returns_expected_keys(client):
    response = client.get('/api/analytics')
    assert response.status_code == 200
    data = response.get_json()
    # Expecting dictionary with keys such as 'post_views' and 'user_activity'
    assert isinstance(data, dict)
    assert 'post_views' in data
    assert 'user_activity' in data

