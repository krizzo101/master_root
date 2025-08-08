"""Core module for opsvi-gateway.

Provides base classes and core functionality.
"""

from .base import OpsviGatewayManagerError, OpsviGatewayManagerConfigurationError, OpsviGatewayManagerInitializationError

__all__ = [
    "OpsviGatewayManagerError",
    "OpsviGatewayManagerConfigurationError",
    "OpsviGatewayManagerInitializationError",
]
