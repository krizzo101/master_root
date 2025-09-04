"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from typing import Optional

from .settings import settings


def setup_logging(
    log_level: Optional[str] = None, log_file: Optional[str] = None
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Override log level from settings.
        log_file: Override log file from settings.
    """
    level = log_level or settings.log_level
    file_path = log_file or settings.log_file

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(settings.log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if file_path:
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    logger.info(f"Logging configured: level={level}, file={file_path}")
