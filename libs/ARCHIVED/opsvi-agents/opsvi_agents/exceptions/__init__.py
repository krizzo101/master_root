"""Exceptions module for opsvi-agents.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviAgentsConfigurationError,
    OpsviAgentsConnectionError,
    OpsviAgentsError,
    OpsviAgentsInitializationError,
    OpsviAgentsResourceError,
    OpsviAgentsTimeoutError,
    OpsviAgentsValidationError,
)

__all__ = [
    "OpsviAgentsError",
    "OpsviAgentsConfigurationError",
    "OpsviAgentsConnectionError",
    "OpsviAgentsValidationError",
    "OpsviAgentsTimeoutError",
    "OpsviAgentsResourceError",
    "OpsviAgentsInitializationError",
]
