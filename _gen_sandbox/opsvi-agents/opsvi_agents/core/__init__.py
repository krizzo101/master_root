"""Core module for opsvi-agents.

Provides base classes and core functionality.
"""

from .base import OpsviAgentsManagerError, OpsviAgentsManagerConfigurationError, OpsviAgentsManagerInitializationError

__all__ = [
    "OpsviAgentsManagerError",
    "OpsviAgentsManagerConfigurationError",
    "OpsviAgentsManagerInitializationError",
]
