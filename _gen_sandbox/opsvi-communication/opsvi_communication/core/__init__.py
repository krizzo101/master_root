"""Core module for opsvi-communication.

Provides base classes and core functionality.
"""

from .base import OpsviCommunicationManagerError, OpsviCommunicationManagerConfigurationError, OpsviCommunicationManagerInitializationError

__all__ = [
    "OpsviCommunicationManagerError",
    "OpsviCommunicationManagerConfigurationError",
    "OpsviCommunicationManagerInitializationError",
]
