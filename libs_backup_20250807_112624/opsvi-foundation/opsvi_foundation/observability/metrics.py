"""
Prometheus metrics collection.

Provides counters, gauges, histograms, and custom metrics.
"""

from __future__ import annotations

import time
from typing import Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel

from ..observability import get_logger

logger = get_logger(__name__)


class MetricsConfig(BaseModel):
    """Configuration for metrics collection."""

    enabled: bool = True
    namespace: str = "opsvi"
    subsystem: str = ""
    registry_name: str = "default"


class MetricsCollector:
    """Centralized metrics collection with Prometheus integration."""

    def __init__(self, config: MetricsConfig | None = None):
        self.config = config or MetricsConfig()
        self.registry = CollectorRegistry()
        self._metrics: dict[str, Any] = {}

        if self.config.enabled:
            self._initialize_default_metrics()

        logger.debug(
            "Initialized MetricsCollector",
            enabled=self.config.enabled,
            namespace=self.config.namespace,
        )

    def _initialize_default_metrics(self):
        """Initialize default system metrics."""
        # Request metrics
        self.request_count = self.create_counter(
            "requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"],
        )

        self.request_duration = self.create_histogram(
            "request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
        )

        # Error metrics
        self.error_count = self.create_counter(
            "errors_total",
            "Total number of errors",
            ["type", "component"],
        )

        # System metrics
        self.active_connections = self.create_gauge(
            "active_connections",
            "Number of active connections",
            ["type"],
        )

        # Component health
        self.component_status = self.create_enum(
            "component_status",
            "Component health status",
            ["component"],
            states=["healthy", "degraded", "unhealthy"],
        )

        logger.debug("Initialized default metrics")

    def create_counter(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Counter:
        """Create a Prometheus counter.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names

        Returns:
            Prometheus Counter instance
        """
        if not self.config.enabled:
            return None

        full_name = self._build_metric_name(name)
        counter = Counter(
            full_name,
            description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self._metrics[full_name] = counter
        logger.debug("Created counter", name=full_name, labels=labels)
        return counter

    def create_gauge(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Gauge:
        """Create a Prometheus gauge.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names

        Returns:
            Prometheus Gauge instance
        """
        if not self.config.enabled:
            return None

        full_name = self._build_metric_name(name)
        gauge = Gauge(
            full_name,
            description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self._metrics[full_name] = gauge
        logger.debug("Created gauge", name=full_name, labels=labels)
        return gauge

    def create_histogram(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Histogram:
        """Create a Prometheus histogram.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names

        Returns:
            Prometheus Histogram instance
        """
        if not self.config.enabled:
            return None

        full_name = self._build_metric_name(name)
        histogram = Histogram(
            full_name,
            description,
            labelnames=labels or [],
            registry=self.registry,
        )

        self._metrics[full_name] = histogram
        logger.debug("Created histogram", name=full_name, labels=labels)
        return histogram

    def create_enum(
        self,
        name: str,
        description: str,
        labels: list[str],
        states: list[str],
    ) -> Enum:
        """Create a Prometheus enum.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names
            states: Possible enum states

        Returns:
            Prometheus Enum instance
        """
        if not self.config.enabled:
            return None

        full_name = self._build_metric_name(name)
        enum = Enum(
            full_name,
            description,
            labelnames=labels,
            states=states,
            registry=self.registry,
        )

        self._metrics[full_name] = enum
        logger.debug("Created enum", name=full_name, labels=labels, states=states)
        return enum

    def _build_metric_name(self, name: str) -> str:
        """Build full metric name with namespace and subsystem.

        Args:
            name: Base metric name

        Returns:
            Full metric name
        """
        parts = [self.config.namespace]

        if self.config.subsystem:
            parts.append(self.config.subsystem)

        parts.append(name)
        return "_".join(parts)

    def record_request(self, method: str, endpoint: str, status: str, duration: float):
        """Record request metrics.

        Args:
            method: HTTP method
            endpoint: Request endpoint
            status: Response status
            duration: Request duration in seconds
        """
        if not self.config.enabled:
            return

        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        logger.debug(
            "Recorded request metrics",
            method=method,
            endpoint=endpoint,
            status=status,
            duration=duration,
        )

    def record_error(self, error_type: str, component: str):
        """Record error metrics.

        Args:
            error_type: Type of error
            component: Component that generated the error
        """
        if not self.config.enabled:
            return

        self.error_count.labels(type=error_type, component=component).inc()
        logger.debug("Recorded error", error_type=error_type, component=component)

    def set_component_status(self, component: str, status: str):
        """Set component health status.

        Args:
            component: Component name
            status: Health status (healthy, degraded, unhealthy)
        """
        if not self.config.enabled:
            return

        self.component_status.labels(component=component).state(status)
        logger.debug("Set component status", component=component, status=status)

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format.

        Returns:
            Metrics as Prometheus text format
        """
        if not self.config.enabled:
            return ""

        return generate_latest(self.registry).decode("utf-8")

    def get_content_type(self) -> str:
        """Get Prometheus content type.

        Returns:
            Prometheus content type
        """
        return CONTENT_TYPE_LATEST


class TimingContext:
    """Context manager for timing operations."""

    def __init__(
        self,
        histogram: Histogram | None,
        labels: dict[str, str] | None = None,
    ):
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.histogram and self.start_time:
            duration = time.time() - self.start_time
            if self.labels:
                self.histogram.labels(**self.labels).observe(duration)
            else:
                self.histogram.observe(duration)


# Global metrics collector
metrics = MetricsCollector()


def time_operation(
    histogram: Histogram,
    labels: dict[str, str] | None = None,
) -> TimingContext:
    """Create timing context for operation.

    Args:
        histogram: Histogram to record timing
        labels: Labels for the histogram

    Returns:
        Timing context manager
    """
    return TimingContext(histogram, labels)
