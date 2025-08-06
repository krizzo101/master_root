"""
Core module for OPSVI Core Library.

Provides configuration, logging, exceptions, and base patterns.
"""

from .config import AppConfig, config, load_config
from .exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    ExternalServiceError,
    InitializationError,
    OpsviError,
    ValidationError,
)
from .logging import setup_logging
from .patterns import BaseActor

__all__ = [
    "config",
    "AppConfig",
    "load_config",
    "setup_logging",
    "OpsviError",
    "ConfigurationError",
    "InitializationError",
    "ValidationError",
    "ExternalServiceError",
    "DatabaseConnectionError",
    "BaseActor",
]
