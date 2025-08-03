"""
Logging utilities for GenFileMap.

This module provides centralized logging functionality with configurable levels and output destinations.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

# Remove direct import from config to break circular dependency
# from genfilemap.config import get_config_value

# Log levels mapping
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class LogManager:
    """
    Singleton class for managing logging configuration.

    This provides a centralized control point for all logging in the application,
    ensuring consistent formatting and behavior.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if LogManager._initialized:
            return

        self.logger = logging.getLogger("genfilemap")
        # Clear any existing handlers to prevent duplication
        if self.logger.handlers:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)

        self.logger.setLevel(logging.INFO)
        self.formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handlers = []

        # Add a default console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
        self.handlers.append(console_handler)

        LogManager._initialized = True

    def configure(
        self,
        level: str = "info",
        log_file: Optional[str] = None,
        console: bool = True,
        debug: bool = False,
    ) -> None:
        """
        Configure logging with the specified options.

        Args:
            level: Log level (debug, info, warning, error, critical)
            log_file: Optional path to a log file
            console: Whether to log to console
            debug: Override to set debug level if True
        """
        # Set log level (debug overrides level)
        log_level = (
            logging.DEBUG if debug else LOG_LEVELS.get(level.lower(), logging.INFO)
        )
        self.logger.setLevel(log_level)

        # Remove existing handlers
        for handler in self.handlers:
            self.logger.removeHandler(handler)
        self.handlers = []

        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)
            self.handlers.append(console_handler)

        # Add file handler if specified
        if log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
            self.handlers.append(file_handler)

    def get_logger(self):
        """Get the configured logger instance"""
        return self.logger


# Global function to access logger
def get_logger():
    """Get the GenFileMap logger instance"""
    return LogManager().get_logger()


# Convenience functions
def debug(msg: str, *args, **kwargs):
    """Log a debug message"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log an info message"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log a warning message"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Log an error message"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """Log a critical message"""
    get_logger().critical(msg, *args, **kwargs)


def configure_logging(config: Dict[str, Any]) -> None:
    """
    Configure logging based on the provided configuration.

    Args:
        config: Configuration dictionary with logging options
    """

    # Helper function to get config value with a default
    def get_config_val(config, key, default=None):
        return config.get(key, default)

    log_level = get_config_val(config, "log_level", "info").upper()
    log_file = get_config_val(config, "log_file")
    console_output = get_config_val(config, "console_output", True)
    debug_mode = get_config_val(config, "debug", False)

    # Create logs directory if log file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not log_dir:
            # Use default logs directory
            log_dir = "logs"
            log_file = os.path.join(log_dir, log_file)

        # Create directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

    LogManager().configure(
        level=log_level, log_file=log_file, console=console_output, debug=debug_mode
    )

    # Log initialization at debug level
    if debug_mode:
        debug("Debug logging enabled")


def initialize_logging(config: Dict[str, Any]):
    """
    Initialize logging based on configuration.

    Args:
        config: Configuration dictionary with logging options

    Returns:
        The configured logger
    """

    # Helper function to get config value with a default
    def get_config_val(config, key, default=None):
        if isinstance(config, dict) and key in config:
            return config[key]

        # Handle nested keys with dot notation
        if isinstance(config, dict) and "." in key:
            parts = key.split(".")
            current = config
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current

        return default

    # Configure logging system
    debug_mode = get_config_val(config, "debug", False)
    log_level = "debug" if debug_mode else get_config_val(config, "log_level", "info")

    logging_config = {
        "log_level": log_level,
        "log_file": get_config_val(config, "log_file"),
        "console_output": True,
        "debug": debug_mode,
    }

    configure_logging(logging_config)
    logger = get_logger()

    if debug_mode:
        debug("Debug logging enabled")

    return logger
