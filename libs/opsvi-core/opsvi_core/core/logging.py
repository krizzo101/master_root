"""
Structured logging setup for OPSVI Core Library.

Configures structured logging with structlog and standard library logging integration.
"""

import logging
import os
import sys
from typing import Any

import orjson
import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with structlog and standard logging.

    Args:
        log_level: The logging level as string (e.g., 'INFO', 'DEBUG', 'WARNING', 'ERROR').
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Set structlog processors chain
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(
            serializer=lambda x: orjson.dumps(x).decode()
        ),
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        BoundLogger: Configured structured logger
    """
    return structlog.get_logger(name)


def log_context(**kwargs: Any) -> dict[str, Any]:
    """
    Create a log context dictionary for structured logging.

    Args:
        **kwargs: Key-value pairs to include in log context

    Returns:
        Dict[str, Any]: Log context dictionary
    """
    return kwargs


# Set up logging at import time, can be overridden
setup_logging(os.environ.get("OPSVI_LOG_LEVEL", "INFO"))
