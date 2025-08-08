"""Configuration module for opsvi-gateway.

Provides configuration management and settings.
"""

from .settings import OpsviGatewaySettings, get_settings

__all__ = [
    "OpsviGatewaySettings",
    "get_settings",
]
