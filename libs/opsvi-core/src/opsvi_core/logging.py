"""OPSVI Core Logging Configuration."""

import sys

import structlog


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    include_timestamp: bool = True,
    include_process: bool = True,
    include_thread: bool = True,
) -> None:
    """Setup structured logging for OPSVI applications."""

    processors = [
        structlog.stdlib.filter_by_level,
    ]

    if include_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))

    if include_process:
        processors.append(structlog.processors.add_log_level)
        processors.append(structlog.processors.StackInfoRenderer())

    if include_thread:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
        )

    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    import logging

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
