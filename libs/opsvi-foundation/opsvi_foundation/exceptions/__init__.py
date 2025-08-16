"""Exceptions module for opsvi-foundation.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviFoundationError,
    OpsviFoundationConfigurationError,
    OpsviFoundationConnectionError,
    OpsviFoundationValidationError,
    OpsviFoundationTimeoutError,
    OpsviFoundationResourceError,
    OpsviFoundationInitializationError,
)

__all__ = [
    "OpsviFoundationError",
    "OpsviFoundationConfigurationError",
    "OpsviFoundationConnectionError",
    "OpsviFoundationValidationError",
    "OpsviFoundationTimeoutError",
    "OpsviFoundationResourceError",
    "OpsviFoundationInitializationError",
]
