# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Configuration Loader Module","description":"This module provides utilities for loading and validating configuration files.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules for configuration loading and logging.","line_start":3,"line_end":11},{"name":"Constants","description":"Defines constants used for configuration file paths.","line_start":12,"line_end":12},{"name":"load_config Function","description":"Loads a configuration file based on type and name, handling various exceptions.","line_start":16,"line_end":48},{"name":"load_prompt_config Function","description":"Loads a prompt configuration by delegating to the load_config function.","line_start":49,"line_end":58}],"key_elements":[{"name":"load_config","description":"Function to load a configuration file.","line":16},{"name":"load_prompt_config","description":"Function to load a prompt configuration.","line":49},{"name":"CONFIG_DIR","description":"Constant that holds the path to the configuration directory.","line":12},{"name":"logger","description":"Logger instance for logging configuration loading events.","line":11},{"name":"os","description":"Module for interacting with the operating system.","line":7},{"name":"json","description":"Module for parsing JSON data.","line":8},{"name":"logging","description":"Module for logging events.","line":9},{"name":"Dict","description":"Type hint for dictionary types.","line":10},{"name":"Any","description":"Type hint for any type.","line":10},{"name":"Optional","description":"Type hint for optional types.","line":10}]}
"""
# FILE_MAP_END

"""
Configuration Loader Module.

This module provides utilities for loading and validating configuration files.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config"
)


def load_config(config_type: str, config_name: str) -> Dict[str, Any]:
    """
    Load a configuration file.

    Args:
        config_type: Type of config (prompts, templates, schemas)
        config_name: Name of config file without extension

    Returns:
        Configuration dictionary
    """
    # Handle app_config specially since it's in the root config directory
    if config_type == "app_config" and config_name == "app_config":
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "app_config.json",
        )
    else:
        # For other configurations, use the subdirectory structure
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            config_type,
            f"{config_name}.json",
        )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.debug(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration {config_path}: {str(e)}")
        return {}


def load_prompt_config(prompt_name: str) -> Dict[str, str]:
    """
    Load a prompt configuration.

    Args:
        prompt_name: The name of the prompt configuration

    Returns:
        The loaded prompt configuration with system_message and user_prompt_template
    """
    return load_config("prompts", prompt_name)
