"""Core module for opsvi-http.

Provides base classes and core functionality.
"""

from .base import Error, ConfigurationError, InitializationError

__all__ = [
    "Error",
    "ConfigurationError",
    "InitializationError",
]
