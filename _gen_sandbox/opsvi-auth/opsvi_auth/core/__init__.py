"""Core module for opsvi-auth.

Provides base classes and core functionality.
"""

from .base import OpsviAuthManagerError, OpsviAuthManagerConfigurationError, OpsviAuthManagerInitializationError

__all__ = [
    "OpsviAuthManagerError",
    "OpsviAuthManagerConfigurationError",
    "OpsviAuthManagerInitializationError",
]
