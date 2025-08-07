"""Configuration module for opsvi-security.

Provides configuration management and settings.
"""

from .settings import OpsviSecuritySettings, get_settings

__all__ = [
    "OpsviSecuritySettings",
    "get_settings",
]
