"""Configuration module for opsvi-deploy.

Provides configuration management and settings.
"""

from .settings import OpsviDeploySettings, get_settings

__all__ = [
    "OpsviDeploySettings",
    "get_settings",
]
