"""
Base monitoring infrastructure for OPSVI Core.

Provides health checks, metrics collection, alerting, and performance monitoring.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger

logger = get_logger(__name__)


class MonitoringError(ComponentError):
    """Raised when monitoring operations fail."""

    pass


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(str, Enum):
    """Metric type definitions."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class HealthCheck:
    """Health check definition."""

    name: str
    check_func: Callable[[], bool]
    timeout: float = 5.0
    critical: bool = True
    interval: float = 30.0
    description: str = ""


@dataclass
class HealthResult:
    """Health check result."""

    name: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0
    critical: bool = True


@dataclass
class Metric:
    """Metric data point."""

    name: str
    value: float
    metric_type: MetricType
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""


class HealthChecker(BaseComponent):
    """Health check manager."""

    def __init__(self):
        super().__init__()
        self._checks: dict[str, HealthCheck] = {}
        self._results: dict[str, HealthResult] = {}

    def register_check(self, health_check: HealthCheck) -> None:
        """Register a health check."""
        self._checks[health_check.name] = health_check
        logger.info("Registered health check: %s", health_check.name)

    def unregister_check(self, name: str) -> None:
        """Unregister a health check."""
        self._checks.pop(name, None)
        self._results.pop(name, None)
        logger.info("Unregistered health check: %s", name)

    async def run_check(self, name: str) -> HealthResult:
        """Run a specific health check."""
        if name not in self._checks:
            return HealthResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' not found",
                critical=False,
            )

        check = self._checks[name]
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                asyncio.create_task(self._run_check_async(check)), timeout=check.timeout
            )

            duration = time.time() - start_time
            status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            message = "Check passed" if result else "Check failed"

            health_result = HealthResult(
                name=name,
                status=status,
                message=message,
                duration=duration,
                critical=check.critical,
            )

        except TimeoutError:
            duration = time.time() - start_time
            health_result = HealthResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check timed out after {check.timeout}s",
                duration=duration,
                critical=check.critical,
            )

        except Exception as e:
            duration = time.time() - start_time
            health_result = HealthResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {e}",
                duration=duration,
                critical=check.critical,
            )

        self._results[name] = health_result
        return health_result

    async def _run_check_async(self, check: HealthCheck) -> bool:
        """Run health check function asynchronously."""
        if asyncio.iscoroutinefunction(check.check_func):
            return await check.check_func()
        else:
            return check.check_func()

    async def run_all_checks(self) -> dict[str, HealthResult]:
        """Run all registered health checks."""
        tasks = [self.run_check(name) for name in self._checks.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        check_results = {}
        for name, result in zip(self._checks.keys(), results, strict=False):
            if isinstance(result, Exception):
                check_results[name] = HealthResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {result}",
                    critical=self._checks[name].critical,
                )
            else:
                check_results[name] = result

        return check_results

    def get_overall_health(self) -> HealthStatus:
        """Get overall system health status."""
        if not self._results:
            return HealthStatus.UNKNOWN

        critical_failures = [
            r
            for r in self._results.values()
            if r.critical and r.status == HealthStatus.UNHEALTHY
        ]

        if critical_failures:
            return HealthStatus.UNHEALTHY

        degraded_checks = [
            r
            for r in self._results.values()
            if r.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        ]

        if degraded_checks:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY


class MetricsCollector(BaseComponent):
    """Metrics collection and management."""

    def __init__(self):
        super().__init__()
        self._metrics: dict[str, list[Metric]] = {}
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}

    def increment_counter(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric."""
        labels = labels or {}
        key = self._get_metric_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

        metric = Metric(
            name=name,
            value=self._counters[key],
            metric_type=MetricType.COUNTER,
            labels=labels,
        )
        self._store_metric(metric)

    def set_gauge(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric value."""
        labels = labels or {}
        key = self._get_metric_key(name, labels)
        self._gauges[key] = value

        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels,
        )
        self._store_metric(metric)

    def record_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Record a histogram metric value."""
        labels = labels or {}
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels,
        )
        self._store_metric(metric)

    def _get_metric_key(self, name: str, labels: dict[str, str]) -> str:
        """Generate unique key for metric with labels."""
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]" if label_str else name

    def _store_metric(self, metric: Metric) -> None:
        """Store metric in memory."""
        if metric.name not in self._metrics:
            self._metrics[metric.name] = []

        self._metrics[metric.name].append(metric)

        # Keep only last 1000 metrics per name to prevent memory issues
        if len(self._metrics[metric.name]) > 1000:
            self._metrics[metric.name] = self._metrics[metric.name][-1000:]

    def get_metrics(self, name: str | None = None) -> dict[str, list[Metric]]:
        """Get collected metrics."""
        if name:
            return {name: self._metrics.get(name, [])}
        return self._metrics.copy()

    def get_current_values(self) -> dict[str, float]:
        """Get current values for counters and gauges."""
        return {**self._counters, **self._gauges}


class AlertManager(BaseComponent):
    """Alert management and notification."""

    def __init__(self):
        super().__init__()
        self._handlers: list[Callable[[str, str, dict[str, Any]], None]] = []
        self._active_alerts: dict[str, datetime] = {}

    def add_handler(self, handler: Callable[[str, str, dict[str, Any]], None]) -> None:
        """Add alert handler."""
        self._handlers.append(handler)
        logger.info("Added alert handler")

    def remove_handler(
        self, handler: Callable[[str, str, dict[str, Any]], None]
    ) -> None:
        """Remove alert handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
            logger.info("Removed alert handler")

    async def send_alert(
        self, level: str, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Send alert to all handlers."""
        context = context or {}
        alert_key = f"{level}:{message}"

        # Avoid duplicate alerts within 5 minutes
        now = datetime.utcnow()
        if alert_key in self._active_alerts:
            last_sent = self._active_alerts[alert_key]
            if (now - last_sent).total_seconds() < 300:  # 5 minutes
                return

        self._active_alerts[alert_key] = now

        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(level, message, context)
                else:
                    handler(level, message, context)
            except Exception as e:
                logger.error("Alert handler failed: %s", e)


class MonitoringSystem(BaseComponent):
    """Main monitoring system coordinator."""

    def __init__(self):
        super().__init__()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()

    async def _start(self) -> None:
        """Start monitoring system."""
        await self.health_checker.start()
        await self.metrics_collector.start()
        await self.alert_manager.start()
        logger.info("Monitoring system started")

    async def _stop(self) -> None:
        """Stop monitoring system."""
        await self.health_checker.stop()
        await self.metrics_collector.stop()
        await self.alert_manager.stop()
        logger.info("Monitoring system stopped")

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        health_results = await self.health_checker.run_all_checks()
        overall_health = self.health_checker.get_overall_health()
        current_metrics = self.metrics_collector.get_current_values()

        return {
            "overall_health": overall_health.value,
            "timestamp": datetime.utcnow().isoformat(),
            "health_checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "duration": result.duration,
                    "critical": result.critical,
                }
                for name, result in health_results.items()
            },
            "metrics": current_metrics,
        }
