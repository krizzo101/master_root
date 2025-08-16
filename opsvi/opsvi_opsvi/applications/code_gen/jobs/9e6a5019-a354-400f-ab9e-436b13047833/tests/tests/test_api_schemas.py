import pytest
from app.api_schemas import TagSchema, CategorySchema, ImageSchema, PostSchema


def test_tag_schema_serialization():
    tag = type("Tag", (), {"id": 1, "name": "Flask"})()
    schema = TagSchema()
    data = schema.dump(tag)
    assert data["id"] == 1
    assert data["name"] == "Flask"


def test_category_schema_serialization():
    cat = type("Category", (), {"id": 2, "name": "Tech"})()
    schema = CategorySchema()
    data = schema.dump(cat)
    assert data["id"] == 2
    assert data["name"] == "Tech"


def test_image_schema_serialization():
    image = type("Image", (), {"id": 3, "filename": "pic.png"})()
    schema = ImageSchema()
    data = schema.dump(image)
    assert data["id"] == 3
    assert data["filename"] == "pic.png"


def test_post_schema_serialization():
    post = type(
        "Post", (), {"id": 4, "title": "Test Post", "content": "Content here"}
    )()
    schema = PostSchema()
    data = schema.dump(post)
    assert data["id"] == 4
    assert data["title"] == "Test Post"
