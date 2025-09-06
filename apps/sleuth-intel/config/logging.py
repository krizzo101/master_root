"""
Logging configuration for Sleuth Intel system
"""

import logging
import logging.config
import os
from typing import Any, Dict


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration dictionary"""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", "logs")

    os.makedirs(log_dir, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            },
        },
        "handlers": {
            "default": {
                "level": log_level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": log_level,
                "formatter": "detailed",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(log_dir, "sleuth-intel.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {
                "handlers": ["default", "file"],
                "level": log_level,
                "propagate": False,
            }
        },
    }


def setup_logging():
    """Setup logging configuration"""
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Test logging
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")


if __name__ == "__main__":
    setup_logging()
