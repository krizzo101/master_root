#!/usr/bin/env python
"""Convenience script to run the URL shortener service."""

import sys

import uvicorn
from url_shortener.config import settings
from url_shortener.config.logging_config import setup_logging


def main():
    """Run the application."""
    # Setup logging
    setup_logging()

    # Run the application
    uvicorn.run(
        "url_shortener.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
