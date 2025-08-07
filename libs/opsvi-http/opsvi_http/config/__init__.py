"""Configuration module for opsvi-http.

Provides configuration management and settings.
"""

from .settings import OpsviHttpSettings, get_settings

__all__ = [
    "OpsviHttpSettings",
    "get_settings",
]
