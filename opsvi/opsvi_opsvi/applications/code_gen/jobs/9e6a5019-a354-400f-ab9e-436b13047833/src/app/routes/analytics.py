"""
Analytics endpoints for admin dashboard/charts.
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Post, PostView
from app import redis_client
import datetime

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/post_views")
@login_required
def post_views_stat():
    # Simple analytics: views per post (Redis)
    keys = redis_client.keys("post:*:views")
    stats = {}
    for k in keys:
        post_id = int(k.decode().split(":")[1])
        stats[post_id] = int(redis_client.get(k))
    return jsonify(stats)


@analytics_bp.route("/trending_posts")
@login_required
def trending_posts():
    # Return top 5 trending posts by view count
    keys = redis_client.keys("post:*:views")
    trending = []
    for k in keys:
        post_id = int(k.decode().split(":")[1])
        view_count = int(redis_client.get(k))
        trending.append((post_id, view_count))
    trending.sort(key=lambda x: x[1], reverse=True)
    results = [{"post_id": pid, "views": vc} for pid, vc in trending[:5]]
    return jsonify(results)
