"""Core module for opsvi-communication.

Provides base classes and core functionality.
"""

from .base import ConfigurationError, Error, InitializationError

__all__ = [
    "Error",
    "ConfigurationError",
    "InitializationError",
]
