"""Configuration module for opsvi-monitoring.

Provides configuration management and settings.
"""

from .settings import OpsviMonitoringSettings, get_settings

__all__ = [
    "OpsviMonitoringSettings",
    "get_settings",
]
