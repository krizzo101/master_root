"""Core module for opsvi-foundation.

Provides base classes and core functionality.
"""

from .base import OpsviFoundationManagerError, OpsviFoundationManagerConfigurationError, OpsviFoundationManagerInitializationError

__all__ = [
    "OpsviFoundationManagerError",
    "OpsviFoundationManagerConfigurationError",
    "OpsviFoundationManagerInitializationError",
]
