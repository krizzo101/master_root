"""
Monitoring module for opsvi-core.

Provides application monitoring, metrics, health checks, and profiling capabilities.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base monitoring infrastructure
from .base import (
    AlertManager,
    HealthCheck,
    HealthChecker,
    HealthResult,
    HealthStatus,
    Metric,
    MetricsCollector,
    MetricType,
    MonitoringError,
    MonitoringSystem,
)

__all__ = [
    # Base classes
    "AlertManager",
    "HealthCheck",
    "HealthChecker",
    "HealthResult",
    "HealthStatus",
    "Metric",
    "MetricsCollector",
    "MetricType",
    "MonitoringError",
    "MonitoringSystem",
]

__version__ = "1.0.0"
