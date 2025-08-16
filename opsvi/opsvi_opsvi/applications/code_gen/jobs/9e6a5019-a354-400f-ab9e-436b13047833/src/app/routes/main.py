"""
Main non-authenticated views: homepage, about, post detail.
"""
from flask import (
    Blueprint,
    render_template,
    current_app,
    request,
    abort,
    redirect,
    url_for,
    flash,
)
from sqlalchemy.orm import joinedload
from app.models import Post, Category, Tag, PostView
from app import db, redis_client
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def homepage():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template("main/home.html", posts=posts)


@main_bp.route("/post/<int:post_id>")
def post_detail(post_id: int):
    post = Post.query.options(
        joinedload(Post.tags), joinedload(Post.categories), joinedload(Post.images)
    ).get(post_id)
    if not post:
        abort(404)
    # Record post view in Redis atomically; store for analytics
    redis_client.incr(f"post:{post_id}:views")
    if current_user.is_authenticated:
        view = PostView(post_id=post_id, user_id=current_user.id)
    else:
        view = PostView(post_id=post_id)
    db.session.add(view)
    db.session.commit()
    return render_template("main/post_detail.html", post=post)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")
