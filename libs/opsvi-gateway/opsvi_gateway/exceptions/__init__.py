"""Exceptions module for opsvi-gateway.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviGatewayError,
    OpsviGatewayConfigurationError,
    OpsviGatewayConnectionError,
    OpsviGatewayValidationError,
    OpsviGatewayTimeoutError,
    OpsviGatewayResourceError,
    OpsviGatewayInitializationError,
)

__all__ = [
    "OpsviGatewayError",
    "OpsviGatewayConfigurationError",
    "OpsviGatewayConnectionError",
    "OpsviGatewayValidationError",
    "OpsviGatewayTimeoutError",
    "OpsviGatewayResourceError",
    "OpsviGatewayInitializationError",
]
