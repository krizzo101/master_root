import pytest
from app.models import User, Post, Image, Category, Tag, PostView


def test_user_repr_returns_correct_string():
    user = User(id=1, username="testuser")
    expected = f"<User {user.username}>"
    assert repr(user) == expected


def test_post_repr_and_view_count_methods_work_correctly():
    # Setup post with views
    post = Post(id=10, title="Test Post")
    # Mock PostView entries related to this post
    post.post_views = [PostView(post_id=10), PostView(post_id=10), PostView(post_id=10)]
    assert repr(post) == f"<Post {post.title}>"
    assert post.view_count == 3


def test_image_repr_returns_correct_string():
    image = Image(id=5, filename="image.png")
    assert repr(image) == f"<Image {image.filename}>"


def test_category_repr_returns_name():
    cat = Category(id=1, name="Tech")
    assert repr(cat) == f"<Category {cat.name}>"


def test_tag_repr_returns_name():
    tag = Tag(id=2, name="Flask")
    assert repr(tag) == f"<Tag {tag.name}>"


def test_postview_repr_returns_string():
    pv = PostView(id=3, post_id=1)
    assert repr(pv) == f"<PostView post_id={pv.post_id}>"
