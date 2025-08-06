"""
OPSVI Core Library

Core utilities and base classes for the OPSVI ecosystem.
Provides configuration, logging, exceptions, and base patterns for AI/ML operations.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

from .agents.base_agent import BaseAgent
from .core.config import AppConfig, config, load_config
from .core.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
    ExternalServiceError,
    InitializationError,
    OpsviError,
    ValidationError,
)
from .core.logging import setup_logging
from .core.patterns import BaseActor

__all__ = [
    # Configuration
    "config",
    "AppConfig",
    "load_config",
    # Logging
    "setup_logging",
    # Exceptions
    "OpsviError",
    "ConfigurationError",
    "InitializationError",
    "ValidationError",
    "ExternalServiceError",
    "DatabaseConnectionError",
    # Patterns
    "BaseActor",
    "BaseAgent",
]
