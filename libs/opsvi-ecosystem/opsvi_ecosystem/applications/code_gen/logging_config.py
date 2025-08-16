"""Structured logging configuration for code generation pipeline."""

import json
import logging
import sys
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add custom fields
        for key, value in record.__dict__.items():
            if key.startswith("extra_"):
                log_entry[key[6:]] = value

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure structured logging."""
    formatter = JSONFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler (optional)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format="%(message)s",
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
