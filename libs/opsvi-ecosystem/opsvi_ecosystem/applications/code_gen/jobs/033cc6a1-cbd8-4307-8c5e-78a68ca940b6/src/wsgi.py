"""
WSGI entry point for production deployments (e.g., Gunicorn).
"""
from app import create_app

app = create_app()
