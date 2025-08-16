"""
Flask configuration using environment variables for security and flexibility.
"""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "REPLACE_ME_WITH_A_RANDOM_SECRET")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_cms"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get(
        "CSRF_SECRET_KEY", "REPLACE_ME_WITH_ANOTHER_SECRET"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    UPLOADED_IMAGES_DEST = os.environ.get(
        "UPLOADED_IMAGES_DEST", "static/uploads/images"
    )
    UPLOADED_IMAGES_ALLOW = set(["jpg", "jpeg", "png", "gif"])

    AWS_S3_BUCKET_NAME = os.environ.get("AWS_S3_BUCKET_NAME", "ai-cms-uploads")
    AWS_S3_REGION = os.environ.get("AWS_S3_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    QUILL_ALLOWED_TAGS = [
        "p",
        "b",
        "i",
        "strong",
        "em",
        "u",
        "ul",
        "li",
        "ol",
        "blockquote",
        "code",
        "a",
        "img",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]
    QUILL_ALLOWED_ATTRS = ["href", "src", "alt", "class", "title", "style"]

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

    # Flask-Admin
    FLASK_ADMIN_SWATCH = "cerulean"
