"""
Logging configuration and utility.
"""
import logging
from typing import Optional

logger = logging.getLogger("csv_reporter")

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

_DEFUALT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str = "INFO", stream=None) -> None:
    """
    Configure the application logging for all modules.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter(_DEFAULT_FORMAT, datefmt=_DEFUALT_DATEFMT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        for handler in logger.handlers:
            handler.setLevel(numeric_level)


__all__ = ["logger", "configure_logging"]
