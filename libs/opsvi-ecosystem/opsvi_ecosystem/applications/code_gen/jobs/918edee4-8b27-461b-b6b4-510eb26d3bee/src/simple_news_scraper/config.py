"""
Centralized configuration and logging setup.
"""
import logging
import os
from typing import Any

import yaml

DEFAULT_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config.yaml"
)
DEFAULT_SITE_URL = "https://www.bbc.co.uk/news"

DEFAULT_CONFIG = {
    "url": DEFAULT_SITE_URL,
    "output_file": None,  # By default, do not write out
    "timeout": 20,
    "loglevel": "INFO",
    # "headline_selectors": ... optional, override selectors
}


def load_config(config_path: str = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    """
    Loads configuration from YAML file (if exists), merged with defaults.
    :param config_path: Path to config.yaml
    :return: Config dict
    """
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    config.update(data)
        except Exception as exc:
            print(f"[WARNING] Failed to load config from {config_path}: {exc}")
    return config


def setup_logging(loglevel: str = "INFO") -> None:
    """
    Setup and configure logging for the application.
    :param loglevel: Log level as string
    """
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    logging.basicConfig(
        level=numeric_level,
        format="[%(asctime)s %(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Reduce request/bs4 verbosity
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bs4").setLevel(logging.ERROR)
