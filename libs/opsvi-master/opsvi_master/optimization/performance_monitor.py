"""
Performance Monitor for KG-DB Optimization System

Provides real-time performance monitoring, alerting, and optimization recommendations
for database operations, Knowledge Graph queries, and overall system health.
"""

from __future__ import annotations
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import logging
import statistics


class MetricType(Enum):
    """Types of performance metrics."""

    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_CONNECTION_COUNT = "db_connection_count"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    QUEUE_DEPTH = "queue_depth"


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricThreshold:
    """Performance threshold configuration."""

    warning_threshold: float
    critical_threshold: float
    operator: str = "gt"  # gt, lt, eq
    window_seconds: int = 60

    def check_violation(self, value: float) -> Optional[AlertLevel]:
        """Check if value violates thresholds."""
        if self.operator == "gt":
            if value >= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value >= self.warning_threshold:
                return AlertLevel.WARNING
        elif self.operator == "lt":
            if value <= self.critical_threshold:
                return AlertLevel.CRITICAL
            elif value <= self.warning_threshold:
                return AlertLevel.WARNING
        return None


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement."""

    metric_type: MetricType
    value: float
    timestamp: datetime
    operation: Optional[str] = None
    component: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Performance alert."""

    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


class PerformanceMonitor:
    """
    Real-time performance monitoring and alerting system.

    Features:
    - Real-time metric collection and analysis
    - Configurable thresholds and alerting
    - Performance trend analysis
    - Optimization recommendations
    - Health score calculation
    - Automated performance reporting
    """

    def __init__(
        self, retention_hours: int = 24, alert_callback: Optional[Callable] = None
    ) -> None:
        self.retention_hours = retention_hours
        self.alert_callback = alert_callback
        self._metrics: List[PerformanceMetric] = []
        self._alerts: List[Alert] = []
        self._thresholds: Dict[MetricType, MetricThreshold] = {}
        self._active_operations: Dict[str, Tuple[datetime, str]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(__name__)

        # Default thresholds
        self._setup_default_thresholds()

    def _setup_default_thresholds(self) -> None:
        """Set up default performance thresholds."""
        self._thresholds = {
            MetricType.RESPONSE_TIME: MetricThreshold(
                warning_threshold=1.0,  # 1 second
                critical_threshold=5.0,  # 5 seconds
                operator="gt",
            ),
            MetricType.ERROR_RATE: MetricThreshold(
                warning_threshold=0.05,  # 5%
                critical_threshold=0.15,  # 15%
                operator="gt",
            ),
            MetricType.CACHE_HIT_RATE: MetricThreshold(
                warning_threshold=0.6,  # 60%
                critical_threshold=0.4,  # 40%
                operator="lt",
            ),
            MetricType.DATABASE_CONNECTION_COUNT: MetricThreshold(
                warning_threshold=8,  # 8 connections
                critical_threshold=12,  # 12 connections
                operator="gt",
            ),
            MetricType.QUEUE_DEPTH: MetricThreshold(
                warning_threshold=10,  # 10 queued operations
                critical_threshold=25,  # 25 queued operations
                operator="gt",
            ),
        }

    async def start(self) -> None:
        """Start performance monitoring with background cleanup."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._logger.info("Performance monitoring started")

    async def stop(self) -> None:
        """Stop performance monitoring."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        self._logger.info("Performance monitoring stopped")

    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a performance metric.

        Args:
            metric_type: Type of metric
            value: Metric value
            operation: Operation name (optional)
            component: Component name (optional)
            metadata: Additional metadata (optional)
        """
        async with self._lock:
            metric = PerformanceMetric(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.now(),
                operation=operation,
                component=component,
                metadata=metadata or {},
            )

            self._metrics.append(metric)

            # Check for threshold violations
            await self._check_thresholds(metric)

            self._logger.debug(
                "Recorded metric %s: %f (operation: %s)",
                metric_type.value,
                value,
                operation,
            )

    @asynccontextmanager
    async def measure_operation(
        self, operation_name: str, component: Optional[str] = None
    ):
        """
        Context manager to measure operation duration.

        Args:
            operation_name: Name of the operation
            component: Component performing the operation
        """
        start_time = time.time()
        operation_id = f"{operation_name}_{int(start_time * 1000)}"

        async with self._lock:
            self._active_operations[operation_id] = (datetime.now(), operation_name)

        try:
            yield operation_id
        except Exception as e:
            # Record error
            await self.record_metric(
                MetricType.ERROR_RATE,
                1.0,
                operation=operation_name,
                component=component,
                metadata={"error": str(e)},
            )
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # Record response time
            await self.record_metric(
                MetricType.RESPONSE_TIME,
                duration,
                operation=operation_name,
                component=component,
            )

            # Remove from active operations
            async with self._lock:
                self._active_operations.pop(operation_id, None)

    async def set_threshold(
        self, metric_type: MetricType, threshold: MetricThreshold
    ) -> None:
        """Set custom threshold for a metric type."""
        async with self._lock:
            self._thresholds[metric_type] = threshold
            self._logger.info(
                "Updated threshold for %s: warning=%f, critical=%f",
                metric_type.value,
                threshold.warning_threshold,
                threshold.critical_threshold,
            )

    async def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        operation: Optional[str] = None,
        component: Optional[str] = None,
        hours: Optional[int] = None,
    ) -> List[PerformanceMetric]:
        """
        Retrieve metrics with optional filtering.

        Args:
            metric_type: Filter by metric type
            operation: Filter by operation
            component: Filter by component
            hours: Number of hours to look back

        Returns:
            List of matching metrics
        """
        async with self._lock:
            metrics = self._metrics.copy()

        # Apply time filter
        if hours:
            cutoff = datetime.now() - timedelta(hours=hours)
            metrics = [m for m in metrics if m.timestamp >= cutoff]

        # Apply other filters
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        if component:
            metrics = [m for m in metrics if m.component == component]

        return metrics

    async def get_metric_summary(
        self, metric_type: MetricType, hours: int = 1
    ) -> Dict[str, Any]:
        """
        Get statistical summary for a metric type.

        Args:
            metric_type: Type of metric to summarize
            hours: Number of hours to analyze

        Returns:
            Statistical summary
        """
        metrics = await self.get_metrics(metric_type=metric_type, hours=hours)

        if not metrics:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "std_dev": 0,
            }

        values = [m.value for m in metrics]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "p95": statistics.quantiles(values, n=20)[18]
            if len(values) > 20
            else max(values),
            "p99": statistics.quantiles(values, n=100)[98]
            if len(values) > 100
            else max(values),
        }

    async def get_alerts(
        self, level: Optional[AlertLevel] = None, resolved: Optional[bool] = None
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.

        Args:
            level: Filter by alert level
            resolved: Filter by resolution status

        Returns:
            List of matching alerts
        """
        async with self._lock:
            alerts = self._alerts.copy()

        if level:
            alerts = [a for a in alerts if a.level == level]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return alerts

    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.

        Args:
            alert_id: ID of alert to resolve

        Returns:
            True if alert was found and resolved
        """
        async with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolution_timestamp = datetime.now()
                    self._logger.info("Resolved alert %s", alert_id)
                    return True
        return False

    async def get_health_score(self) -> Dict[str, Any]:
        """
        Calculate overall system health score.

        Returns:
            Health score and component breakdown
        """
        # Get recent metrics (last hour)
        recent_metrics = await self.get_metrics(hours=1)

        if not recent_metrics:
            return {
                "overall_score": 100,
                "component_scores": {},
                "recommendations": ["No recent metrics available"],
            }

        # Calculate component scores
        component_scores = {}

        # Response time score (lower is better)
        response_times = [
            m.value for m in recent_metrics if m.metric_type == MetricType.RESPONSE_TIME
        ]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            response_score = max(0, 100 - (avg_response_time * 20))  # 5s = 0 points
            component_scores["response_time"] = response_score

        # Error rate score (lower is better)
        error_metrics = [
            m.value for m in recent_metrics if m.metric_type == MetricType.ERROR_RATE
        ]
        if error_metrics:
            error_rate = statistics.mean(error_metrics)
            error_score = max(0, 100 - (error_rate * 500))  # 20% error rate = 0 points
            component_scores["error_rate"] = error_score

        # Cache hit rate score (higher is better)
        cache_metrics = [
            m.value
            for m in recent_metrics
            if m.metric_type == MetricType.CACHE_HIT_RATE
        ]
        if cache_metrics:
            hit_rate = statistics.mean(cache_metrics)
            cache_score = hit_rate * 100
            component_scores["cache_performance"] = cache_score

        # Calculate overall score
        if component_scores:
            overall_score = statistics.mean(component_scores.values())
        else:
            overall_score = 100

        # Generate recommendations
        recommendations = []
        if overall_score < 70:
            recommendations.append("System performance is below optimal levels")
        if component_scores.get("response_time", 100) < 80:
            recommendations.append("Consider optimizing slow operations")
        if component_scores.get("error_rate", 100) < 90:
            recommendations.append("Investigate and fix recurring errors")
        if component_scores.get("cache_performance", 100) < 70:
            recommendations.append("Review cache configuration and hit rates")

        return {
            "overall_score": round(overall_score, 1),
            "component_scores": {k: round(v, 1) for k, v in component_scores.items()},
            "recommendations": recommendations,
            "active_operations": len(self._active_operations),
            "unresolved_alerts": len([a for a in self._alerts if not a.resolved]),
        }

    async def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if metric violates configured thresholds."""
        threshold = self._thresholds.get(metric.metric_type)
        if not threshold:
            return

        violation_level = threshold.check_violation(metric.value)
        if violation_level:
            alert_id = f"{metric.metric_type.value}_{int(metric.timestamp.timestamp())}"

            alert = Alert(
                alert_id=alert_id,
                level=violation_level,
                metric_type=metric.metric_type,
                message=f"{metric.metric_type.value} threshold violation: {metric.value:.2f}",
                value=metric.value,
                threshold=threshold.warning_threshold
                if violation_level == AlertLevel.WARNING
                else threshold.critical_threshold,
                timestamp=metric.timestamp,
            )

            self._alerts.append(alert)

            # Call alert callback if configured
            if self.alert_callback:
                try:
                    await self.alert_callback(alert)
                except Exception as e:
                    self._logger.error("Error in alert callback: %s", e)

            self._logger.warning(
                "Performance alert: %s (level: %s, value: %f)",
                alert.message,
                violation_level.value,
                metric.value,
            )

    async def _cleanup_old_data(self) -> None:
        """Clean up old metrics and resolved alerts."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        # Clean old metrics
        initial_metric_count = len(self._metrics)
        self._metrics = [m for m in self._metrics if m.timestamp >= cutoff_time]

        # Clean old resolved alerts (keep for 48 hours)
        alert_cutoff = datetime.now() - timedelta(hours=48)
        initial_alert_count = len(self._alerts)
        self._alerts = [
            a
            for a in self._alerts
            if not a.resolved
            or a.resolution_timestamp is None
            or a.resolution_timestamp >= alert_cutoff
        ]

        metrics_cleaned = initial_metric_count - len(self._metrics)
        alerts_cleaned = initial_alert_count - len(self._alerts)

        if metrics_cleaned > 0 or alerts_cleaned > 0:
            self._logger.debug(
                "Cleaned up %d old metrics and %d old alerts",
                metrics_cleaned,
                alerts_cleaned,
            )

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                async with self._lock:
                    await self._cleanup_old_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("Error in performance monitor cleanup loop: %s", e)
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
