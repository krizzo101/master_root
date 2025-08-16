"""Exceptions module for opsvi-data.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviDataConfigurationError,
    OpsviDataConnectionError,
    OpsviDataError,
    OpsviDataInitializationError,
    OpsviDataResourceError,
    OpsviDataTimeoutError,
    OpsviDataValidationError,
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
