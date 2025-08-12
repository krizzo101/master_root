import pytest
from app.tasks import (
    ai_generate_post_content,
    ai_suggest_tags,
    ai_suggest_categories,
    generate_alt_text,
)


def test_ai_generate_post_content_returns_seo_optimized_content():
    result = ai_generate_post_content("Test Title", "Write a blog post about testing")
    assert isinstance(result, dict)
    assert "title" in result
    assert "content" in result
    assert len(result["content"]) > 0


def test_ai_suggest_tags_returns_list_of_tags():
    tags = ai_suggest_tags("Content about Flask web development")
    assert isinstance(tags, list)
    assert all(isinstance(tag, str) for tag in tags)


def test_ai_suggest_categories_returns_list_of_categories():
    categories = ai_suggest_categories("Content about coding in Python")
    assert isinstance(categories, list)
    assert all(isinstance(cat, str) for cat in categories)


def test_generate_alt_text_returns_string():
    alt_text = generate_alt_text(1, "http://example.com/image.jpg")
    assert isinstance(alt_text, str)
    assert len(alt_text) > 0
