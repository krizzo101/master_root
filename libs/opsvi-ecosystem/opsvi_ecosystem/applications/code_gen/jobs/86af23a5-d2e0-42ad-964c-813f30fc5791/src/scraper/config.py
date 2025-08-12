# scraper/config.py
"""
Configuration module for the Python News Headlines Scraper.
Handles loading and validation of scraper settings and per-site parsing rules.
"""
import os
import yaml
import logging
from typing import Dict, Any

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config.yaml")

logger = logging.getLogger("scraper.config")


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Loads YAML configuration from the specified file.

    Args:
        config_path (str): The path to the config.yaml file.

    Returns:
        dict: Configuration dictionary.

    Raises:
        FileNotFoundError: If the config file is not found.
        yaml.YAMLError: If the config file contains invalid YAML.
    """
    config_path = config_path or DEFAULT_CONFIG_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {config_path}")
        raise e
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        raise e
    return config
