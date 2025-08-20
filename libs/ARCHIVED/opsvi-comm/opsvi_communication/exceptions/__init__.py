"""Exceptions module for opsvi-communication.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviCommunicationConfigurationError,
    OpsviCommunicationConnectionError,
    OpsviCommunicationError,
    OpsviCommunicationInitializationError,
    OpsviCommunicationResourceError,
    OpsviCommunicationTimeoutError,
    OpsviCommunicationValidationError,
)

__all__ = [
    "OpsviCommunicationError",
    "OpsviCommunicationConfigurationError",
    "OpsviCommunicationConnectionError",
    "OpsviCommunicationValidationError",
    "OpsviCommunicationTimeoutError",
    "OpsviCommunicationResourceError",
    "OpsviCommunicationInitializationError",
]
