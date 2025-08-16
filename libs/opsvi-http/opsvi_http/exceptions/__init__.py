"""Exceptions module for opsvi-http.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviHttpError,
    OpsviHttpConfigurationError,
    OpsviHttpConnectionError,
    OpsviHttpValidationError,
    OpsviHttpTimeoutError,
    OpsviHttpResourceError,
    OpsviHttpInitializationError,
)

__all__ = [
    "OpsviHttpError",
    "OpsviHttpConfigurationError",
    "OpsviHttpConnectionError",
    "OpsviHttpValidationError",
    "OpsviHttpTimeoutError",
    "OpsviHttpResourceError",
    "OpsviHttpInitializationError",
]
