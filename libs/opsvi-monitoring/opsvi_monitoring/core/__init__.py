"""Core module for opsvi-monitoring.

Provides base classes and core functionality.
"""

from .base import Error, ConfigurationError, InitializationError

__all__ = [
    "Error",
    "ConfigurationError",
    "InitializationError",
]
