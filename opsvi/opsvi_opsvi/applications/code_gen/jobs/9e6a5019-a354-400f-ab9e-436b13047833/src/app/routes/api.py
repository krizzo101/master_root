"""
RESTful API endpoints for posts, tags, categories, analytics.
"""
from flask import Blueprint, abort, jsonify
from flask_login import login_required
from sqlalchemy.orm import joinedload

from app.api_schemas import CategorySchema, PostSchema, TagSchema
from app.models import Category, Post, Tag, db

api_bp = Blueprint("api", __name__)

post_schema = PostSchema()
tag_schema = TagSchema()
cat_schema = CategorySchema()


@api_bp.route("/posts", methods=["GET"])
def api_get_posts():
    posts = Post.query.options(joinedload(Post.tags), joinedload(Post.categories)).all()
    return jsonify(post_schema.dump(posts, many=True)), 200


@api_bp.route("/post/<int:post_id>", methods=["GET"])
def api_get_post(post_id: int):
    post = Post.query.options(joinedload(Post.tags), joinedload(Post.categories)).get(
        post_id
    )
    if not post:
        abort(404)
    return jsonify(post_schema.dump(post)), 200


@api_bp.route("/tags", methods=["GET"])
def api_get_tags():
    tags = Tag.query.all()
    return jsonify(tag_schema.dump(tags, many=True)), 200


@api_bp.route("/categories", methods=["GET"])
def api_get_categories():
    cats = Category.query.all()
    return jsonify(cat_schema.dump(cats, many=True)), 200


@api_bp.route("/analytics", methods=["GET"])
@login_required
def api_analytics():
    # Example: top posts by view count
    data = db.session.execute(
        "SELECT id, title FROM post ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    return jsonify({"recent_posts": [dict(row) for row in data]})
