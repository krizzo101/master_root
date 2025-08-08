"""Exceptions module for opsvi-security.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviSecurityError,
    OpsviSecurityConfigurationError,
    OpsviSecurityConnectionError,
    OpsviSecurityValidationError,
    OpsviSecurityTimeoutError,
    OpsviSecurityResourceError,
    OpsviSecurityInitializationError,
)

__all__ = [
    "OpsviSecurityError",
    "OpsviSecurityConfigurationError",
    "OpsviSecurityConnectionError",
    "OpsviSecurityValidationError",
    "OpsviSecurityTimeoutError",
    "OpsviSecurityResourceError",
    "OpsviSecurityInitializationError",
]
