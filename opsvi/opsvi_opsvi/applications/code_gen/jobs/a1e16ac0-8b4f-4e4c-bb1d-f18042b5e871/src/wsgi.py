"""
WSGI entry point for gunicorn and other WSGI servers.
"""
from app import create_app

app = create_app()
