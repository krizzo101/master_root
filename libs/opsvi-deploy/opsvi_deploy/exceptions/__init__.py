"""Exceptions module for opsvi-deploy.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviDeployError,
    OpsviDeployConfigurationError,
    OpsviDeployConnectionError,
    OpsviDeployValidationError,
    OpsviDeployTimeoutError,
    OpsviDeployResourceError,
    OpsviDeployInitializationError,
)

__all__ = [
    "OpsviDeployError",
    "OpsviDeployConfigurationError",
    "OpsviDeployConnectionError",
    "OpsviDeployValidationError",
    "OpsviDeployTimeoutError",
    "OpsviDeployResourceError",
    "OpsviDeployInitializationError",
]
