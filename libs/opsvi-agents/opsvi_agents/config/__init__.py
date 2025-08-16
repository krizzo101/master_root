"""Configuration module for opsvi-agents.

Provides configuration management and settings.
"""

from .settings import OpsviAgentsSettings, get_settings

__all__ = [
    "OpsviAgentsSettings",
    "get_settings",
]
