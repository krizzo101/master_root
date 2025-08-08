"""Configuration module for opsvi-auth.

Provides configuration management and settings.
"""

from .settings import OpsviAuthSettings, get_settings

__all__ = [
    "OpsviAuthSettings",
    "get_settings",
]
