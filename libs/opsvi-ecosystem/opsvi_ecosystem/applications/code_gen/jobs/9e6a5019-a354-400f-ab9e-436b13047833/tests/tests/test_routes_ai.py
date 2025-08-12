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



def test_ai_generate_post_returns_generated_content(client, monkeypatch):
    fake_content = {'title': 'AI generated title', 'content': 'AI generated post content optimized for SEO.'}

    monkeypatch.setattr('app.routes.ai.ai_generate_post_content', lambda title, prompt: fake_content)

    response = client.post('/ai/generate_post', json={'title': 'Test', 'prompt': 'Write a blog post'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'title' in data
    assert 'content' in data
    assert data['title'] == fake_content['title']


def test_ai_tags_and_categories_return_suggestions(client, monkeypatch):
    monkeypatch.setattr('app.routes.ai.ai_suggest_tags', lambda content: ['tag1', 'tag2'])
    monkeypatch.setattr('app.routes.ai.ai_suggest_categories', lambda content: ['cat1'])

    response_tags = client.post('/ai/tags', json={'content': 'Some blog content'})
    response_cats = client.post('/ai/categories', json={'content': 'Some blog content'})

    assert response_tags.status_code == 200
    assert 'tag1' in response_tags.get_json()

    assert response_cats.status_code == 200
    assert 'cat1' in response_cats.get_json()


def test_image_alt_text_returns_generated_text(client, monkeypatch):
    fake_alt_text = {'alt_text': 'A descriptive alt text for image'}

    monkeypatch.setattr('app.routes.ai.generate_alt_text', lambda image_id: fake_alt_text)

    response = client.get('/ai/image_alt_text/123')
    assert response.status_code == 200
    data = response.get_json()
    assert 'alt_text' in data
    assert data['alt_text'] == fake_alt_text['alt_text']

