"""Exceptions module for opsvi-auth.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviAuthError,
    OpsviAuthConfigurationError,
    OpsviAuthConnectionError,
    OpsviAuthValidationError,
    OpsviAuthTimeoutError,
    OpsviAuthResourceError,
    OpsviAuthInitializationError,
)

__all__ = [
    "OpsviAuthError",
    "OpsviAuthConfigurationError",
    "OpsviAuthConnectionError",
    "OpsviAuthValidationError",
    "OpsviAuthTimeoutError",
    "OpsviAuthResourceError",
    "OpsviAuthInitializationError",
]
