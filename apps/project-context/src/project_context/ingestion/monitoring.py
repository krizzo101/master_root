"""Advanced monitoring and alerting system for ingestion pipeline."""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"


@dataclass
class Alert:
    """System alert."""

    id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str  # component that generated the alert
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class MetricValue:
    """A single metric measurement."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result."""

    component: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class AlertRule:
    """Rule for generating alerts based on metrics."""

    def __init__(
        self,
        name: str,
        metric_name: str,
        condition: str,  # e.g., "> 100", "< 0.5", "== 0"
        threshold_value: float,
        severity: AlertSeverity,
        time_window_seconds: int = 300,  # 5 minutes
        evaluation_interval_seconds: int = 60,  # 1 minute
        min_samples: int = 1,
        description: str = "",
    ):
        self.name = name
        self.metric_name = metric_name
        self.condition = condition
        self.threshold_value = threshold_value
        self.severity = severity
        self.time_window_seconds = time_window_seconds
        self.evaluation_interval_seconds = evaluation_interval_seconds
        self.min_samples = min_samples
        self.description = description
        self.last_evaluation = None
        self.currently_firing = False

    def evaluate(self, metrics: List[MetricValue]) -> Optional[Alert]:
        """Evaluate the rule against recent metrics."""
        now = datetime.utcnow()

        # Check if it's time to evaluate
        if (
            self.last_evaluation
            and (now - self.last_evaluation).total_seconds()
            < self.evaluation_interval_seconds
        ):
            return None

        self.last_evaluation = now

        # Filter metrics to time window
        cutoff_time = now - timedelta(seconds=self.time_window_seconds)
        recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if len(recent_metrics) < self.min_samples:
            return None

        # Calculate aggregate value (average for now)
        avg_value = sum(m.value for m in recent_metrics) / len(recent_metrics)

        # Evaluate condition
        should_fire = self._evaluate_condition(avg_value)

        if should_fire and not self.currently_firing:
            # Start firing
            self.currently_firing = True
            return Alert(
                id=f"{self.name}_{int(now.timestamp())}",
                severity=self.severity,
                title=f"Alert: {self.name}",
                message=f"{self.description}\nMetric: {self.metric_name} = {avg_value:.2f}, Threshold: {self.condition} {self.threshold_value}",
                source="monitoring_system",
                metadata={
                    "metric_name": self.metric_name,
                    "metric_value": avg_value,
                    "threshold_value": self.threshold_value,
                    "condition": self.condition,
                    "samples_count": len(recent_metrics),
                },
            )
        elif not should_fire and self.currently_firing:
            # Stop firing
            self.currently_firing = False

        return None

    def _evaluate_condition(self, value: float) -> bool:
        """Evaluate the threshold condition."""
        if self.condition.startswith(">"):
            return value > self.threshold_value
        elif self.condition.startswith("<"):
            return value < self.threshold_value
        elif self.condition.startswith("=="):
            return abs(value - self.threshold_value) < 0.001
        elif self.condition.startswith("!="):
            return abs(value - self.threshold_value) >= 0.001
        elif self.condition.startswith(">="):
            return value >= self.threshold_value
        elif self.condition.startswith("<="):
            return value <= self.threshold_value
        else:
            return False


class MetricsCollector:
    """Collects and stores metrics from pipeline components."""

    def __init__(self, retention_hours: int = 24, max_metrics_per_name: int = 10000):
        self.retention_hours = retention_hours
        self.max_metrics_per_name = max_metrics_per_name

        # Storage: metric_name -> deque of MetricValue
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_name)
        )
        self._metrics_lock = asyncio.Lock()

        self.logger = logger.bind(component="metrics_collector")

    async def record_metric(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Record a metric value."""
        metric = MetricValue(
            timestamp=timestamp or datetime.utcnow(), value=value, labels=labels or {}
        )

        async with self._metrics_lock:
            self._metrics[name].append(metric)

    async def get_metrics(
        self, name: str, since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[MetricValue]:
        """Get metrics for a given name."""
        async with self._metrics_lock:
            metrics = list(self._metrics[name])

        if since:
            metrics = [m for m in metrics if m.timestamp >= since]

        if limit:
            metrics = metrics[-limit:]

        return metrics

    async def get_latest_metric(self, name: str) -> Optional[MetricValue]:
        """Get the most recent metric value."""
        async with self._metrics_lock:
            metrics = self._metrics[name]
            return metrics[-1] if metrics else None

    async def get_metric_names(self) -> List[str]:
        """Get all metric names."""
        async with self._metrics_lock:
            return list(self._metrics.keys())

    async def cleanup_old_metrics(self) -> int:
        """Remove metrics older than retention period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        removed_count = 0

        async with self._metrics_lock:
            for name, metrics_deque in self._metrics.items():
                # Convert to list, filter, then recreate deque
                filtered_metrics = [
                    m for m in metrics_deque if m.timestamp >= cutoff_time
                ]
                removed_count += len(metrics_deque) - len(filtered_metrics)

                # Replace the deque
                new_deque = deque(filtered_metrics, maxlen=self.max_metrics_per_name)
                self._metrics[name] = new_deque

        if removed_count > 0:
            self.logger.debug("Cleaned up old metrics", removed_count=removed_count)

        return removed_count


class AlertManager:
    """Manages alerts and notification rules."""

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self._alerts: deque = deque(maxlen=max_alerts)
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_rules: List[AlertRule] = []
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._alerts_lock = asyncio.Lock()

        self.logger = logger.bind(component="alert_manager")

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_rules.append(rule)
        self.logger.info("Alert rule added", rule_name=rule.name)

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function."""
        self._alert_handlers.append(handler)

    async def fire_alert(self, alert: Alert) -> None:
        """Fire an alert."""
        async with self._alerts_lock:
            self._alerts.append(alert)
            if not alert.resolved:
                self._active_alerts[alert.id] = alert

        # Call alert handlers
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                self.logger.error("Alert handler error", error=str(e))

        self.logger.warning(
            "Alert fired",
            alert_id=alert.id,
            severity=alert.severity.value,
            title=alert.title,
            source=alert.source,
        )

    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an active alert."""
        async with self._alerts_lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                del self._active_alerts[alert_id]

                self.logger.info(
                    "Alert resolved", alert_id=alert_id, resolved_by=resolved_by
                )
                return True
            return False

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        async with self._alerts_lock:
            return list(self._active_alerts.values())

    async def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts."""
        async with self._alerts_lock:
            return list(self._alerts)[-limit:]

    async def evaluate_rules(self, metrics_collector: MetricsCollector) -> None:
        """Evaluate all alert rules against current metrics."""
        for rule in self._alert_rules:
            try:
                metrics = await metrics_collector.get_metrics(
                    rule.metric_name,
                    since=datetime.utcnow()
                    - timedelta(seconds=rule.time_window_seconds),
                )

                alert = rule.evaluate(metrics)
                if alert:
                    await self.fire_alert(alert)

            except Exception as e:
                self.logger.error(
                    "Rule evaluation error", rule_name=rule.name, error=str(e)
                )


class HealthMonitor:
    """Monitors component health."""

    def __init__(self):
        self._health_checks: Dict[str, HealthCheck] = {}
        self._health_lock = asyncio.Lock()

        self.logger = logger.bind(component="health_monitor")

    async def record_health_check(self, health_check: HealthCheck) -> None:
        """Record a health check result."""
        async with self._health_lock:
            self._health_checks[health_check.component] = health_check

    async def get_health_status(self, component: str) -> Optional[HealthCheck]:
        """Get health status for a component."""
        async with self._health_lock:
            return self._health_checks.get(component)

    async def get_all_health_statuses(self) -> Dict[str, HealthCheck]:
        """Get all health statuses."""
        async with self._health_lock:
            return dict(self._health_checks)

    async def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy components."""
        async with self._health_lock:
            return [
                name
                for name, check in self._health_checks.items()
                if check.status == "unhealthy"
            ]


class PipelineMonitor:
    """Main monitoring system for the ingestion pipeline."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        self.metrics = MetricsCollector(
            retention_hours=self.config.get("metrics_retention_hours", 24),
            max_metrics_per_name=self.config.get("max_metrics_per_name", 10000),
        )

        self.alerts = AlertManager(max_alerts=self.config.get("max_alerts", 1000))

        self.health = HealthMonitor()

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        self.logger = logger.bind(component="pipeline_monitor")

        # Setup default alert rules
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Setup default alert rules."""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                metric_name="pipeline.error_rate",
                condition="> 0.1",  # More than 10% error rate
                threshold_value=0.1,
                severity=AlertSeverity.ERROR,
                time_window_seconds=300,
                description="High error rate detected in pipeline",
            ),
            AlertRule(
                name="low_throughput",
                metric_name="pipeline.throughput",
                condition="< 10",  # Less than 10 items/second
                threshold_value=10.0,
                severity=AlertSeverity.WARNING,
                time_window_seconds=600,
                description="Low throughput detected in pipeline",
            ),
            AlertRule(
                name="adapter_failures",
                metric_name="adapter.failures",
                condition="> 5",  # More than 5 failures
                threshold_value=5.0,
                severity=AlertSeverity.ERROR,
                time_window_seconds=300,
                description="High number of adapter failures",
            ),
            AlertRule(
                name="database_errors",
                metric_name="database.errors",
                condition="> 0",  # Any database errors
                threshold_value=0.0,
                severity=AlertSeverity.CRITICAL,
                time_window_seconds=60,
                description="Database errors detected",
            ),
            AlertRule(
                name="memory_usage",
                metric_name="system.memory_mb",
                condition="> 1500",  # More than 1.5GB
                threshold_value=1500.0,
                severity=AlertSeverity.WARNING,
                time_window_seconds=300,
                description="High memory usage detected",
            ),
        ]

        for rule in default_rules:
            self.alerts.add_rule(rule)

    async def start(self) -> None:
        """Start monitoring."""
        if self._running:
            return

        self._running = True

        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("Pipeline monitoring started")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return

        self._running = False

        # Stop background tasks
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Pipeline monitoring stopped")

    async def record_pipeline_metric(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a pipeline metric."""
        await self.metrics.record_metric(f"pipeline.{name}", value, labels)

    async def record_adapter_metric(
        self,
        adapter_id: str,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record an adapter-specific metric."""
        adapter_labels = {"adapter_id": adapter_id}
        if labels:
            adapter_labels.update(labels)

        await self.metrics.record_metric(f"adapter.{name}", value, adapter_labels)

    async def record_database_metric(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a database metric."""
        await self.metrics.record_metric(f"database.{name}", value, labels)

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status."""
        # Get metrics summary
        metric_names = await self.metrics.get_metric_names()
        metrics_summary = {}

        for name in metric_names:
            latest = await self.metrics.get_latest_metric(name)
            if latest:
                metrics_summary[name] = {
                    "latest_value": latest.value,
                    "timestamp": latest.timestamp.isoformat(),
                    "labels": latest.labels,
                }

        # Get alert summary
        active_alerts = await self.alerts.get_active_alerts()
        recent_alerts = await self.alerts.get_recent_alerts(limit=10)

        # Get health summary
        health_statuses = await self.health.get_all_health_statuses()
        unhealthy_components = await self.health.get_unhealthy_components()

        return {
            "monitoring_running": self._running,
            "metrics_count": len(metric_names),
            "metrics_summary": metrics_summary,
            "active_alerts_count": len(active_alerts),
            "active_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in active_alerts
            ],
            "recent_alerts_count": len(recent_alerts),
            "components_count": len(health_statuses),
            "healthy_components": len(health_statuses) - len(unhealthy_components),
            "unhealthy_components": unhealthy_components,
            "health_statuses": {
                name: {
                    "status": check.status,
                    "response_time_ms": check.response_time_ms,
                    "timestamp": check.timestamp.isoformat(),
                    "error": check.error,
                }
                for name, check in health_statuses.items()
            },
        }

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Evaluate alert rules
                await self.alerts.evaluate_rules(self.metrics)

                # Record system metrics
                await self._record_system_metrics()

                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(60)

    async def _cleanup_loop(self) -> None:
        """Cleanup old data periodically."""
        while self._running:
            try:
                # Cleanup old metrics
                await self.metrics.cleanup_old_metrics()

                # Wait before next cleanup (every hour)
                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Cleanup loop error", error=str(e))
                await asyncio.sleep(3600)

    async def _record_system_metrics(self) -> None:
        """Record system-level metrics."""
        try:
            import psutil

            # Memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            await self.metrics.record_metric("system.memory_mb", memory_mb)

            # CPU usage
            cpu_percent = process.cpu_percent()
            await self.metrics.record_metric("system.cpu_percent", cpu_percent)

            # System-wide memory
            system_memory = psutil.virtual_memory()
            await self.metrics.record_metric(
                "system.memory_percent", system_memory.percent
            )

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error("System metrics error", error=str(e))
