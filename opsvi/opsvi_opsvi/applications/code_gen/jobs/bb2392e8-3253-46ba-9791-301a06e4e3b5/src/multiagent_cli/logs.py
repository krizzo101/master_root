"""
Logging & Audit module – loguru + Rich integration
"""
from loguru import logger
import sys
from rich.logging import RichHandler
from pathlib import Path
import os


def get_log_file_path() -> str:
    return os.environ.get("MULTIAGENT_LOG_FILE", "multiagent_cli.log")


def configure_logging(log_file: Path, verbose: bool, quiet: bool):
    level = "DEBUG" if verbose else ("ERROR" if quiet else "INFO")
    logger.remove()
    # Console handler (Rich)
    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format="<level>{level: <8}</level> | <cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan> | <magenta>{module:15}</magenta> | <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
    # File handler (if enabled)
    if log_file:
        logger.add(
            str(log_file),
            rotation="5 MB",
            retention="7 days",
            level="DEBUG",
            compression="zip",
        )
    # Legacy integration for stdlib logging
    import logging

    logging.basicConfig(
        level=level, handlers=[RichHandler(rich_tracebacks=True)], format="%(message)s"
    )
