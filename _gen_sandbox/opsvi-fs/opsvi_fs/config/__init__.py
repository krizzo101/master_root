"""Configuration module for opsvi-fs.

Provides configuration management and settings.
"""

from .settings import OpsviFsSettings, get_settings

__all__ = [
    "OpsviFsSettings",
    "get_settings",
]
