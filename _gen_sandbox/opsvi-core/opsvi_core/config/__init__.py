"""Configuration module for opsvi-core.

Provides configuration management and settings.
"""

from .settings import OpsviCoreSettings, get_settings

__all__ = [
    "OpsviCoreSettings",
    "get_settings",
]
