import logging
import os
from logging.handlers import RotatingFileHandler

LOG_PATH = os.environ.get("LOG_PATH", "logs/json_processor.log")

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1024 * 1024, backupCount=3)
    handler.setFormatter(formatter)
    # Avoid duplicate handlers
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(handler)
    return logger


# Call during application startup
setup_logger()
