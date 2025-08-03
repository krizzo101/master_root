"""
FastAPI application for the ACCF Research Agent.

This package contains the FastAPI application and API endpoints.
"""

from .app import create_app, get_app

__all__ = ["create_app", "get_app"]
