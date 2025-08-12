"""
Admin dashboard: stats, management views, content admin.
"""
from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app.models import User, Post, Category, Tag, Image
from app import db, redis_client

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
def restrict_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@admin_bp.route("/")
def admin_dashboard():
    post_count = Post.query.count()
    user_count = User.query.count()
    image_count = Image.query.count()
    tag_count = Tag.query.count()
    category_count = Category.query.count()
    top_posts = db.session.execute(
        "SELECT id, title FROM post ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    stats = {
        "post_count": post_count,
        "user_count": user_count,
        "tag_count": tag_count,
        "category_count": category_count,
        "image_count": image_count,
        "top_posts": top_posts,
    }
    return render_template("admin/dashboard.html", stats=stats)
