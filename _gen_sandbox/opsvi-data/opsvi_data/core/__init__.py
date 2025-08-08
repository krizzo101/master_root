"""Core module for opsvi-data.

Provides base classes and core functionality.
"""

from .base import OpsviDataManagerError, OpsviDataManagerConfigurationError, OpsviDataManagerInitializationError

__all__ = [
    "OpsviDataManagerError",
    "OpsviDataManagerConfigurationError",
    "OpsviDataManagerInitializationError",
]
