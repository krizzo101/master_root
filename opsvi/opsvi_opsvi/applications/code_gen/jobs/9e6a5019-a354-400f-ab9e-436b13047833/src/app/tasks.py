"""
Celery tasks: AI content/alt-text generation, tag/category suggestion.
"""
import os
from celery import Celery
import requests
from app.models import Post, Tag, Category, Image, db
from flask import current_app

celery = Celery(
    __name__, broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
)
celery.conf.update(
    task_serializer="json", result_serializer="json", accept_content=["json"]
)


@celery.task()
def ai_generate_post_content(title: str, prompt: str = "") -> str:
    """
    Use OpenAI GPT-like API to generate a SEO-optimized blog post based on title (+ optional prompt)
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API Key not set."
    msg = (
        prompt
        if prompt
        else f"Write a SEO-optimized, engaging blog post titled '{title}'."
    )
    url = "https://api.openai.com/v1/completions"
    payload = {
        "model": "text-davinci-003",
        "prompt": msg,
        "max_tokens": 600,
        "temperature": 0.7,
        "n": 1,
        "stop": None,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        generated = data["choices"][0]["text"].strip()
        return generated
    except Exception as e:
        return f"AI generation failed: {str(e)}"


@celery.task()
def ai_suggest_tags(content: str) -> list[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    prompt = (
        f"Suggest best 5 SEO tags (comma separated) for this content: {content[:400]}"
    )
    try:
        resp = requests.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "text-davinci-003",
                "prompt": prompt,
                "max_tokens": 30,
                "temperature": 0.4,
            },
            timeout=12,
        )
        resp.raise_for_status()
        tags = resp.json()["choices"][0]["text"].strip().replace("\n", "").split(",")
        return [t.strip() for t in tags if t.strip()]
    except Exception as e:
        return [f"AI failed: {str(e)}"]


@celery.task()
def ai_suggest_categories(content: str) -> list[str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    prompt = f"Suggest most fitting single category for this post: {content[:400]}"
    try:
        resp = requests.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": "text-davinci-003", "prompt": prompt, "max_tokens": 8},
            timeout=12,
        )
        resp.raise_for_status()
        cat = resp.json()["choices"][0]["text"].strip()
        return [cat]
    except Exception as e:
        return [f"AI failed: {str(e)}"]


@celery.task()
def generate_alt_text(image_id: int, image_url: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    # For demo: use prompt to describe, in production could call Vision API
    prompt = f"Describe the following image for SEO alt text: {image_url}"
    try:
        resp = requests.post(
            "https://api.openai.com/v1/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": "text-davinci-003", "prompt": prompt, "max_tokens": 40},
            timeout=15,
        )
        resp.raise_for_status()
        alt_text = resp.json()["choices"][0]["text"].strip()
        image = Image.query.get(image_id)
        if image:
            image.alt_text = alt_text
            db.session.commit()
        return alt_text
    except Exception as e:
        return f"AI failed: {str(e)}"
