"""Exceptions module for opsvi-orchestration.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviOrchestrationError,
    OpsviOrchestrationConfigurationError,
    OpsviOrchestrationConnectionError,
    OpsviOrchestrationValidationError,
    OpsviOrchestrationTimeoutError,
    OpsviOrchestrationResourceError,
    OpsviOrchestrationInitializationError,
)

__all__ = [
    "OpsviOrchestrationError",
    "OpsviOrchestrationConfigurationError",
    "OpsviOrchestrationConnectionError",
    "OpsviOrchestrationValidationError",
    "OpsviOrchestrationTimeoutError",
    "OpsviOrchestrationResourceError",
    "OpsviOrchestrationInitializationError",
]
