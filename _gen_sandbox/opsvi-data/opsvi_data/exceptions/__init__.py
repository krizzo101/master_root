"""Exceptions module for opsvi-data.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviDataError,
    OpsviDataConfigurationError,
    OpsviDataConnectionError,
    OpsviDataValidationError,
    OpsviDataTimeoutError,
    OpsviDataResourceError,
    OpsviDataInitializationError,
)

__all__ = [
    "OpsviDataError",
    "OpsviDataConfigurationError",
    "OpsviDataConnectionError",
    "OpsviDataValidationError",
    "OpsviDataTimeoutError",
    "OpsviDataResourceError",
    "OpsviDataInitializationError",
]
