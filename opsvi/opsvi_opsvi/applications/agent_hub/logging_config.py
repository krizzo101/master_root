import logging
import logging.config
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_CONFIG = {
    "version": 1,
    "formatters": {
        "std": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "std",
            "level": LOG_LEVEL,
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}


def setup_logging():
    logging.config.dictConfig(LOG_CONFIG)
