"""
Configuration module for GenFileMap.

This module provides functionality for managing configuration settings
for the GenFileMap tool, including loading from files and environment.
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import appdirs
import pathspec

# Remove circular import
# from genfilemap.logging_utils import info, error as log_error

# Set up basic logging (will be replaced by proper logging later)
_logger = logging.getLogger("genfilemap")
if not _logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


def _log_info(msg):
    """Internal info logging function"""
    _logger.info(msg)


def _log_error(msg):
    """Internal error logging function"""
    _logger.error(msg)


# Set up app information for appdirs
APP_NAME = "genfilemap"
APP_AUTHOR = "genfilemap"


def expand_env_vars(obj: Any) -> Any:
    """
    Recursively expand environment variables in configuration values.

    Supports both ${VAR} and $VAR syntax.

    Args:
        obj: Configuration object (dict, list, str, or other)

    Returns:
        Object with environment variables expanded
    """
    if isinstance(obj, dict):
        return {key: expand_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Expand ${VAR} and $VAR patterns
        def replace_env_var(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))

        # Pattern matches ${VAR} or $VAR (but not if escaped with \)
        pattern = r"(?<!\\)\$\{([^}]+)\}|(?<!\\)\$([A-Za-z_][A-Za-z0-9_]*)"
        return re.sub(pattern, replace_env_var, obj)
    else:
        return obj


# Use appdirs to get platform-appropriate directories
def get_user_config_dir():
    """Get the user config directory in a platform-appropriate way."""
    # For backward compatibility: keep using ~/.genfilemap/.config
    return os.path.expanduser("~/.genfilemap/.config")
    # return appdirs.user_config_dir(APP_NAME, APP_AUTHOR)


def get_user_cache_dir():
    """Get the user cache directory in a platform-appropriate way."""
    # For backward compatibility: keep using ~/.genfilemap/.cache
    return os.path.expanduser("~/.genfilemap/.cache")
    # return appdirs.user_cache_dir(APP_NAME, APP_AUTHOR)


def get_user_data_dir():
    """Get the user data directory in a platform-appropriate way."""
    # For backward compatibility: keep using ~/.genfilemap/.local/share
    return os.path.expanduser("~/.genfilemap/.local/share")
    # return appdirs.user_data_dir(APP_NAME, APP_AUTHOR)


def get_user_log_dir():
    """Get the user log directory in a platform-appropriate way."""
    # For backward compatibility: keep using ~/.genfilemap/.local/share/logs
    return os.path.expanduser("~/.genfilemap/.local/share/logs")
    # return appdirs.user_log_dir(APP_NAME, APP_AUTHOR)


# Default configuration settings
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.genfilemap/.config/config.json")
DEFAULT_PROJECT_CONFIG_PATH = ".genfilemap/config.json"

# Default configuration
DEFAULT_CONFIG = {
    "path": ".",
    "recursive": False,
    "force": False,
    "debug": False,
    "dry_run": False,
    "clean": False,
    "project_map": False,
    "output_dirs": {
        # Global directories (user-level)
        "global": {
            "maps": os.path.expanduser("~/.genfilemap/.local/share/maps"),
            "logs": os.path.expanduser("~/.genfilemap/.local/share/logs"),
            "cache": os.path.expanduser("~/.genfilemap/.cache"),
            "config": os.path.expanduser("~/.genfilemap/.config"),
            "templates": os.path.expanduser("~/.genfilemap/.local/share/templates"),
            "schemas": os.path.expanduser("~/.genfilemap/.local/share/schemas"),
        },
        # Project-specific directories (relative to project root)
        "project": {
            "maps": ".genfilemap/maps",
            "logs": ".genfilemap/logs",
            "cache": ".genfilemap/cache",
            "reports": ".genfilemap/reports",
            "map_reports": ".genfilemap/map_reports",
        },
    },
    "project_map_output": ".genfilemap/maps/PROJECT_FILE_MAP.md",
    "api": {"vendor": "openai", "model": "gpt-4.1-mini", "key_var": "OPENAI_API_KEY"},
    "file_processing": {
        "recursive": False,
        "include_extensions": [
            ".py",
            ".js",
            ".ts",
            ".md",
            ".txt",
            ".html",
            ".css",
            ".java",
            ".c",
            ".cpp",
            ".cs",
            ".go",
            ".rs",
        ],
        "exclude_extensions": [
            ".min.js",
            ".min.css",
            ".pyc",
            ".pyo",
            ".pyd",
            ".o",
            ".obj",
            ".a",
            ".lib",
            ".so",
            ".dll",
            ".dylib",
            ".exe",
            ".bin",
        ],
        "min_lines": 10,
        "ignore_file": ".fileignore",
    },
    "output": {
        "template": "standard",
        "template_dir": os.path.expanduser("~/.genfilemap/.local/share/templates"),
        "schema_path": os.path.expanduser(
            "~/.genfilemap/.local/share/schemas/schema.json"
        ),
        "report_path": ".genfilemap/reports/filemap_report.json",
    },
    "performance": {
        "concurrency": 5,
        "processes": 1,
        "use_dir_hashing": False,
        "force_recompute": False,
    },
}


def _deep_update(target: Dict, source: Dict) -> Dict:
    """
    Recursively update a dictionary with values from another.

    Args:
        target: Target dictionary to update
        source: Source dictionary to get values from

    Returns:
        Updated target dictionary
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
    return target


def get_config_value(config: Dict[str, Any], key_path: str, default=None) -> Any:
    """
    Get a value from the config using dot notation.

    Handles both flattened keys (like "api.vendor") and nested dictionaries.

    Args:
        config: Configuration dictionary
        key_path: Path to the key, using dot notation (e.g., "api.model")
        default: Default value to return if key not found

    Returns:
        The value at the specified path, or default if not found
    """
    # First, try direct access for flattened keys
    if key_path in config:
        return config[key_path]

    # If not found, try nested access
    keys = key_path.split(".")
    current = config

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def load_config(
    config_path: Optional[str] = None, project_config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load configuration from files in the following order:
    1. Project-specific config (in project directory)
    2. Global config (~/.genfilemap/.config/config.json)
    3. Default hardcoded config

    Args:
        config_path: Path to global config file, if None uses default
        project_config_path: Path to project-specific config file, if None uses default

    Returns:
        Dict containing the merged configuration.
    """
    # Use default paths if none specified
    if not config_path:
        config_path = DEFAULT_CONFIG_PATH
    if not project_config_path:
        project_config_path = DEFAULT_PROJECT_CONFIG_PATH

    _log_info("\nLoading configuration...")
    config = {}  # Start with empty config

    # Move import here to avoid circular import
    from genfilemap.utils.file_utils import load_ignore_patterns

    # First try to load project config
    if os.path.exists(project_config_path):
        try:
            with open(project_config_path, "r") as f:
                config = json.load(f)
            _log_info(f"✓ Loaded project-level config from: {project_config_path}")
            _log_info("  Project config values:")
            for key in config.keys():
                _log_info(f"  - {key}")
            _log_info(f"  Project config overrides {len(config)} global settings")
        except Exception as e:
            _log_error(
                f"✗ Error loading project config from {project_config_path}: {str(e)}"
            )
    else:
        _log_info(f"- No project config found at: {project_config_path}")

    # If no project config or it's empty, try global config
    if not config and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            _log_info(f"✓ Loaded global config from: {config_path}")
            _log_info("  Global config values:")
            for key in config.keys():
                _log_info(f"  - {key}")
        except Exception as e:
            _log_error(f"✗ Error loading global config from {config_path}: {str(e)}")
    elif not config:
        _log_info(f"- No global config found at: {config_path}")

    # If no configs found or they're empty, use default
    if not config:
        config = DEFAULT_CONFIG.copy()
        _log_info("✓ Using default hardcoded configuration")
        _log_info("  Default config sections:")
        for key in config.keys():
            _log_info(f"  - {key}")
    else:
        # Expand environment variables in loaded config
        _log_info("- Expanding environment variables in configuration")
        config = expand_env_vars(config)

        # Merge with defaults to ensure all required fields exist
        _log_info(
            "- Merging with default configuration to ensure all required fields exist"
        )
        default = DEFAULT_CONFIG.copy()
        _deep_update(default, config)
        config = default

    _log_info(
        f"Final configuration has {len(config)} top-level sections: {list(config.keys())}"
    )

    _log_info("Configuration loading complete\n")

    # Create project directories if they don't exist
    ensure_output_dirs(config)

    # --- UNIVERSAL IGNORE LOGIC ---
    # Load ignore patterns and compile PathSpec for universal use
    ignore_file = config.get("file_processing", {}).get("ignore_file", ".fileignore")
    if not os.path.isabs(ignore_file):
        ignore_file = os.path.join(os.getcwd(), ignore_file)

    # Load patterns from .fileignore file
    file_patterns = []
    if os.path.exists(ignore_file):
        file_patterns = load_ignore_patterns(ignore_file)

    # Get patterns from config JSON
    config_patterns = get_config_value(config, "file_processing.ignore_patterns", [])

    # Merge both sources of patterns
    all_patterns = file_patterns + config_patterns

    config["ignore_patterns"] = all_patterns
    config["ignore_pathspec"] = pathspec.PathSpec.from_lines(
        "gitwildmatch", all_patterns
    )

    return config


def ensure_output_dirs(config: Dict[str, Any]) -> None:
    """
    Ensure that all output directories exist.

    Args:
        config: Configuration dictionary
    """
    # Create global directories
    global_dirs = get_config_value(config, "output_dirs.global", {})
    for dir_path in global_dirs.values():
        if dir_path:  # Skip empty paths
            os.makedirs(dir_path, exist_ok=True)

    # Create project directories if in a project
    project_dirs = get_config_value(config, "output_dirs.project", {})
    for dir_name, rel_path in project_dirs.items():
        if rel_path and os.path.isdir(os.path.dirname(rel_path) or "."):
            os.makedirs(rel_path, exist_ok=True)


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Save configuration to a file.

    Args:
        config: Configuration dictionary
        config_path: Path to save config, if None uses default

    Returns:
        True if successful, False otherwise
    """
    # Use default path if none specified
    if not config_path:
        config_path = DEFAULT_CONFIG_PATH

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        _log_error(f"Error saving config to {config_path}: {str(e)}")
        return False


def get_environment_overrides() -> Dict[str, Any]:
    """
    Get configuration overrides from environment variables.

    Returns:
        Dict containing configuration overrides from environment
    """
    overrides = {}
    prefix = "GENFILEMAP_"

    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix) :].lower().replace("_", ".")
            overrides[config_key] = value

    return overrides


def generate_default_config(config_path: Optional[str] = None) -> bool:
    """
    Generate a default configuration file.

    Args:
        config_path: Path to save config, if None uses default

    Returns:
        True if successful, False otherwise
    """
    return save_config(DEFAULT_CONFIG, config_path)
