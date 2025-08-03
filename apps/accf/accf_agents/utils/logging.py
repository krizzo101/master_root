"""
Logging configuration for the ACCF Research Agent.

This module provides centralized logging configuration and utilities.
"""

import logging
import sys
from typing import Optional
from ..core.settings import Settings


def setup_logging(settings: Settings, level: Optional[str] = None) -> None:
    """Setup logging configuration for the application."""

    # Determine log level
    log_level = level or settings.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            (
                logging.FileHandler("accf_agent.log")
                if settings.debug
                else logging.NullHandler()
            ),
        ],
    )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

    # Create logger for this application
    logger = logging.getLogger("accf_agents")
    logger.setLevel(numeric_level)

    logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(f"accf_agents.{name}")
