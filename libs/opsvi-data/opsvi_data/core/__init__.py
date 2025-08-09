"""Core module for opsvi-data.

Provides base classes and core functionality.
"""

from .base import ConfigurationError, Error, InitializationError

__all__ = [
    "Error",
    "ConfigurationError",
    "InitializationError",
]
