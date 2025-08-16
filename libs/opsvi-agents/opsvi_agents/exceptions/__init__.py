"""Exceptions module for opsvi-agents.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviAgentsError,
    OpsviAgentsConfigurationError,
    OpsviAgentsConnectionError,
    OpsviAgentsValidationError,
    OpsviAgentsTimeoutError,
    OpsviAgentsResourceError,
    OpsviAgentsInitializationError,
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
