"""Core module for opsvi-security.

Provides base classes and core functionality.
"""

from .base import OpsviSecurityManagerError, OpsviSecurityManagerConfigurationError, OpsviSecurityManagerInitializationError

__all__ = [
    "OpsviSecurityManagerError",
    "OpsviSecurityManagerConfigurationError",
    "OpsviSecurityManagerInitializationError",
]
