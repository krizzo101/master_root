"""Configuration module for opsvi-data.

Provides configuration management and settings.
"""

from .settings import OpsviDataSettings, get_settings

__all__ = [
    "OpsviDataSettings",
    "get_settings",
]
