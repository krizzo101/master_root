"""Core module for opsvi-http.

Provides base classes and core functionality.
"""

from .base import OpsviHttpManagerError, OpsviHttpManagerConfigurationError, OpsviHttpManagerInitializationError

__all__ = [
    "OpsviHttpManagerError",
    "OpsviHttpManagerConfigurationError",
    "OpsviHttpManagerInitializationError",
]
