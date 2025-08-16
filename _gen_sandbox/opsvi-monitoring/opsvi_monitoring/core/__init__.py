"""Core module for opsvi-monitoring.

Provides base classes and core functionality.
"""

from .base import OpsviMonitoringManagerError, OpsviMonitoringManagerConfigurationError, OpsviMonitoringManagerInitializationError

__all__ = [
    "OpsviMonitoringManagerError",
    "OpsviMonitoringManagerConfigurationError",
    "OpsviMonitoringManagerInitializationError",
]
