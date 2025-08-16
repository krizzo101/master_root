"""Configuration module for opsvi-pipeline.

Provides configuration management and settings.
"""

from .settings import OpsviPipelineSettings, get_settings

__all__ = [
    "OpsviPipelineSettings",
    "get_settings",
]
