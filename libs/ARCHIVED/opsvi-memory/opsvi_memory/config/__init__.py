"""Configuration module for opsvi-memory.

Provides configuration management and settings.
"""

from .settings import OpsviMemorySettings, get_settings

__all__ = [
    "OpsviMemorySettings",
    "get_settings",
]
