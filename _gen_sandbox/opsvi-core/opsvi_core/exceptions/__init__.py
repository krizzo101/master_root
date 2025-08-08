"""Exceptions module for opsvi-core.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviCoreError,
    OpsviCoreConfigurationError,
    OpsviCoreConnectionError,
    OpsviCoreValidationError,
    OpsviCoreTimeoutError,
    OpsviCoreResourceError,
    OpsviCoreInitializationError,
)

__all__ = [
    "OpsviCoreError",
    "OpsviCoreConfigurationError",
    "OpsviCoreConnectionError",
    "OpsviCoreValidationError",
    "OpsviCoreTimeoutError",
    "OpsviCoreResourceError",
    "OpsviCoreInitializationError",
]
