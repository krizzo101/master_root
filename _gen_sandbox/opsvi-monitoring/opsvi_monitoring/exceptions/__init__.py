"""Exceptions module for opsvi-monitoring.

Provides exception hierarchy and error handling.
"""

from .base import (
    OpsviMonitoringError,
    OpsviMonitoringConfigurationError,
    OpsviMonitoringConnectionError,
    OpsviMonitoringValidationError,
    OpsviMonitoringTimeoutError,
    OpsviMonitoringResourceError,
    OpsviMonitoringInitializationError,
)

__all__ = [
    "OpsviMonitoringError",
    "OpsviMonitoringConfigurationError",
    "OpsviMonitoringConnectionError",
    "OpsviMonitoringValidationError",
    "OpsviMonitoringTimeoutError",
    "OpsviMonitoringResourceError",
    "OpsviMonitoringInitializationError",
]
