"""
Blueprint: AI endpoints for content, tag, category, and alt text generation (AJAX/RESTful).
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.models import Image
from app.tasks import (
    ai_generate_post_content,
    ai_suggest_categories,
    ai_suggest_tags,
    generate_alt_text,
)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/generate_post", methods=["POST"])
@login_required
def ai_generate_post():
    data = request.get_json() or {}
    title = data.get("title", "")
    prompt = data.get("prompt", "")
    if not title:
        return jsonify({"error": "Title is required."}), 400
    task = ai_generate_post_content.delay(title, prompt)
    return jsonify({"task_id": task.id}), 202


@ai_bp.route("/suggest_tags", methods=["POST"])
@login_required
def ai_tags():
    data = request.get_json() or {}
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "Content required."}), 400
    task = ai_suggest_tags.delay(content)
    return jsonify({"task_id": task.id}), 202


@ai_bp.route("/suggest_categories", methods=["POST"])
@login_required
def ai_categories():
    data = request.get_json() or {}
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "Content required."}), 400
    task = ai_suggest_categories.delay(content)
    return jsonify({"task_id": task.id}), 202


@ai_bp.route("/image_alt_text/<int:image_id>", methods=["GET"])
@login_required
def image_alt_text(image_id: int):
    img = Image.query.get_or_404(image_id)
    if not img.alt_text:
        task = generate_alt_text.delay(image_id, img.url)
        return jsonify({"task_id": task.id, "status": "In progress"})
    return jsonify({"alt_text": img.alt_text, "status": "Ready"})
