"""Core module for opsvi-core.

Provides base classes and core functionality.
"""

from .base import OpsviCoreManagerError, OpsviCoreManagerConfigurationError, OpsviCoreManagerInitializationError

__all__ = [
    "OpsviCoreManagerError",
    "OpsviCoreManagerConfigurationError",
    "OpsviCoreManagerInitializationError",
]
