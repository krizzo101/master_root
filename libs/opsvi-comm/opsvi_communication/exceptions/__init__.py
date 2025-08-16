"""Exceptions module for opsvi-communication.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviCommunicationError,
    OpsviCommunicationConfigurationError,
    OpsviCommunicationConnectionError,
    OpsviCommunicationValidationError,
    OpsviCommunicationTimeoutError,
    OpsviCommunicationResourceError,
    OpsviCommunicationInitializationError,
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
