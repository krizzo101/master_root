"""Real-time monitoring and alerting dashboard for production chat import operations."""

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics we track."""

    THROUGHPUT = "throughput"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    DATABASE_PERFORMANCE = "database_performance"
    EMBEDDING_SERVICE = "embedding_service"
    QUEUE_SIZE = "queue_size"
    SYSTEM_HEALTH = "system_health"


@dataclass
class MetricPoint:
    """A single metric data point."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels,
        }


@dataclass
class Alert:
    """Alert notification."""

    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    metric_type: MetricType
    current_value: float
    threshold: float
    created_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    @property
    def duration_minutes(self) -> float:
        end_time = self.resolved_at or datetime.utcnow()
        return (end_time - self.created_at).total_seconds() / 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "metric_type": self.metric_type.value,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "duration_minutes": self.duration_minutes,
            "metadata": self.metadata,
        }


@dataclass
class AlertRule:
    """Configuration for an alert rule."""

    rule_id: str
    metric_type: MetricType
    condition: str  # "gt", "lt", "eq", "ge", "le"
    threshold: float
    severity: AlertSeverity
    title_template: str
    message_template: str
    cooldown_minutes: int = 5  # Minimum time between alerts
    enabled: bool = True


class MetricsCollector:
    """Collects and stores time-series metrics."""

    def __init__(self, max_points_per_metric: int = 10000):
        self.max_points_per_metric = max_points_per_metric
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.lock = asyncio.Lock()

    async def record_metric(
        self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric point."""
        async with self.lock:
            if metric_name not in self.metrics:
                self.metrics[metric_name] = []

            point = MetricPoint(
                timestamp=datetime.utcnow(), value=value, labels=labels or {}
            )

            self.metrics[metric_name].append(point)

            # Trim old points to prevent memory growth
            if len(self.metrics[metric_name]) > self.max_points_per_metric:
                self.metrics[metric_name] = self.metrics[metric_name][
                    -self.max_points_per_metric :
                ]

    async def get_metric_history(
        self, metric_name: str, duration_minutes: int = 60
    ) -> List[MetricPoint]:
        """Get metric history for specified duration."""
        async with self.lock:
            if metric_name not in self.metrics:
                return []

            cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)

            return [
                point
                for point in self.metrics[metric_name]
                if point.timestamp >= cutoff_time
            ]

    async def get_latest_value(self, metric_name: str) -> Optional[float]:
        """Get the most recent value for a metric."""
        async with self.lock:
            if metric_name not in self.metrics or not self.metrics[metric_name]:
                return None

            return self.metrics[metric_name][-1].value

    async def calculate_average(
        self, metric_name: str, duration_minutes: int = 5
    ) -> Optional[float]:
        """Calculate average value over specified duration."""
        history = await self.get_metric_history(metric_name, duration_minutes)
        if not history:
            return None

        return sum(point.value for point in history) / len(history)

    async def get_all_metrics_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        async with self.lock:
            summary = {}

            for metric_name, points in self.metrics.items():
                if not points:
                    continue

                latest = points[-1]
                values = [p.value for p in points[-100:]]  # Last 100 points

                summary[metric_name] = {
                    "latest_value": latest.value,
                    "latest_timestamp": latest.timestamp.isoformat(),
                    "count": len(points),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0,
                }

            return summary


class AlertManager:
    """Manages alerts and alert rules."""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.lock = asyncio.Lock()

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.alert_rules[rule.rule_id] = rule

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function."""
        self.alert_handlers.append(handler)

    async def evaluate_metric(
        self, metric_name: str, current_value: float, metric_type: MetricType
    ) -> None:
        """Evaluate metric against alert rules."""
        async with self.lock:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled or rule.metric_type != metric_type:
                    continue

                # Check cooldown
                if rule_id in self.alert_cooldowns:
                    cooldown_end = self.alert_cooldowns[rule_id] + timedelta(
                        minutes=rule.cooldown_minutes
                    )
                    if datetime.utcnow() < cooldown_end:
                        continue

                # Evaluate condition
                triggered = self._evaluate_condition(
                    current_value, rule.condition, rule.threshold
                )

                if triggered:
                    await self._trigger_alert(rule, metric_name, current_value)
                else:
                    # Check if we should resolve existing alert
                    await self._check_resolve_alert(rule_id)

    def _evaluate_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "ge":
            return value >= threshold
        elif condition == "le":
            return value <= threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001  # Float equality with tolerance
        else:
            return False

    async def _trigger_alert(
        self, rule: AlertRule, metric_name: str, current_value: float
    ) -> None:
        """Trigger an alert."""
        # Check if alert already exists
        if rule.rule_id in self.active_alerts:
            return

        alert_id = f"{rule.rule_id}_{int(time.time())}"

        alert = Alert(
            alert_id=alert_id,
            severity=rule.severity,
            title=rule.title_template.format(
                metric_name=metric_name,
                current_value=current_value,
                threshold=rule.threshold,
            ),
            message=rule.message_template.format(
                metric_name=metric_name,
                current_value=current_value,
                threshold=rule.threshold,
            ),
            metric_type=rule.metric_type,
            current_value=current_value,
            threshold=rule.threshold,
            created_at=datetime.utcnow(),
            metadata={"rule_id": rule.rule_id, "metric_name": metric_name},
        )

        # Add to active alerts
        self.active_alerts[rule.rule_id] = alert
        self.alert_history.append(alert)

        # Set cooldown
        self.alert_cooldowns[rule.rule_id] = datetime.utcnow()

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(
                    "Alert handler failed", handler=handler.__name__, error=str(e)
                )

        logger.warning(
            "Alert triggered",
            alert_id=alert_id,
            severity=rule.severity.value,
            title=alert.title,
        )

    async def _check_resolve_alert(self, rule_id: str) -> None:
        """Check if an active alert should be resolved."""
        if rule_id in self.active_alerts:
            alert = self.active_alerts[rule_id]
            alert.resolved_at = datetime.utcnow()

            # Remove from active alerts
            del self.active_alerts[rule_id]

            # Notify handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(
                        "Alert handler failed", handler=handler.__name__, error=str(e)
                    )

            logger.info(
                "Alert resolved",
                alert_id=alert.alert_id,
                duration_minutes=alert.duration_minutes,
            )

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        async with self.lock:
            return list(self.active_alerts.values())

    async def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified duration."""
        async with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            return [
                alert for alert in self.alert_history if alert.created_at >= cutoff_time
            ]


class ProductionMonitoringDashboard:
    """Comprehensive monitoring dashboard for production chat import."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.logger = logger.bind(component="monitoring_dashboard")

        # Background tasks
        self._monitoring_tasks: List[asyncio.Task] = []
        self._running = False

        # Setup default alert rules
        self._setup_default_alert_rules()

        # Setup default alert handlers
        self._setup_default_alert_handlers()

    def _setup_default_alert_rules(self) -> None:
        """Setup default alert rules for common issues."""

        # Throughput alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="low_throughput",
                metric_type=MetricType.THROUGHPUT,
                condition="lt",
                threshold=50.0,  # items per second
                severity=AlertSeverity.WARNING,
                title_template="Low Throughput Detected",
                message_template="Import throughput dropped to {current_value:.1f} items/sec (threshold: {threshold})",
                cooldown_minutes=10,
            )
        )

        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="critical_throughput",
                metric_type=MetricType.THROUGHPUT,
                condition="lt",
                threshold=10.0,  # items per second
                severity=AlertSeverity.CRITICAL,
                title_template="Critical Throughput Issue",
                message_template="Import throughput critically low: {current_value:.1f} items/sec (threshold: {threshold})",
                cooldown_minutes=5,
            )
        )

        # Error rate alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="high_error_rate",
                metric_type=MetricType.ERROR_RATE,
                condition="gt",
                threshold=5.0,  # 5% error rate
                severity=AlertSeverity.WARNING,
                title_template="High Error Rate",
                message_template="Error rate elevated: {current_value:.1f}% (threshold: {threshold}%)",
                cooldown_minutes=5,
            )
        )

        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="critical_error_rate",
                metric_type=MetricType.ERROR_RATE,
                condition="gt",
                threshold=15.0,  # 15% error rate
                severity=AlertSeverity.CRITICAL,
                title_template="Critical Error Rate",
                message_template="Error rate critical: {current_value:.1f}% (threshold: {threshold}%)",
                cooldown_minutes=2,
            )
        )

        # Memory usage alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="high_memory_usage",
                metric_type=MetricType.MEMORY_USAGE,
                condition="gt",
                threshold=3072.0,  # 3GB
                severity=AlertSeverity.WARNING,
                title_template="High Memory Usage",
                message_template="Memory usage high: {current_value:.0f}MB (threshold: {threshold}MB)",
                cooldown_minutes=10,
            )
        )

        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="critical_memory_usage",
                metric_type=MetricType.MEMORY_USAGE,
                condition="gt",
                threshold=4096.0,  # 4GB
                severity=AlertSeverity.CRITICAL,
                title_template="Critical Memory Usage",
                message_template="Memory usage critical: {current_value:.0f}MB (threshold: {threshold}MB)",
                cooldown_minutes=2,
            )
        )

        # Database performance alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="slow_database",
                metric_type=MetricType.DATABASE_PERFORMANCE,
                condition="gt",
                threshold=5000.0,  # 5 seconds average query time
                severity=AlertSeverity.WARNING,
                title_template="Slow Database Queries",
                message_template="Database queries slow: {current_value:.0f}ms (threshold: {threshold}ms)",
                cooldown_minutes=10,
            )
        )

        # Embedding service alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="embedding_service_slow",
                metric_type=MetricType.EMBEDDING_SERVICE,
                condition="gt",
                threshold=1000.0,  # 1 second average
                severity=AlertSeverity.WARNING,
                title_template="Slow Embedding Generation",
                message_template="Embedding generation slow: {current_value:.0f}ms (threshold: {threshold}ms)",
                cooldown_minutes=10,
            )
        )

        # Queue size alerts
        self.alert_manager.add_alert_rule(
            AlertRule(
                rule_id="large_queue_size",
                metric_type=MetricType.QUEUE_SIZE,
                condition="gt",
                threshold=5000.0,  # 5000 items in queue
                severity=AlertSeverity.WARNING,
                title_template="Large Queue Size",
                message_template="Queue size large: {current_value:.0f} items (threshold: {threshold})",
                cooldown_minutes=15,
            )
        )

    def _setup_default_alert_handlers(self) -> None:
        """Setup default alert handlers."""

        def log_alert_handler(alert: Alert) -> None:
            """Log alert to structured logger."""
            log_level = {
                AlertSeverity.INFO: "info",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "error",
                AlertSeverity.CRITICAL: "error",
            }[alert.severity]

            getattr(self.logger, log_level)(
                "Alert notification" if not alert.is_resolved else "Alert resolved",
                alert_id=alert.alert_id,
                severity=alert.severity.value,
                title=alert.title,
                message=alert.message,
                current_value=alert.current_value,
                threshold=alert.threshold,
                duration_minutes=alert.duration_minutes if alert.is_resolved else None,
            )

        self.alert_manager.add_alert_handler(log_alert_handler)

    async def start_monitoring(self) -> None:
        """Start the monitoring dashboard."""
        if self._running:
            return

        self.logger.info("Starting production monitoring dashboard")
        self._running = True

        # Start background monitoring tasks
        self._monitoring_tasks = [
            asyncio.create_task(self._system_metrics_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]

        self.logger.info("Production monitoring dashboard started")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring dashboard."""
        if not self._running:
            return

        self.logger.info("Stopping production monitoring dashboard")
        self._running = False

        # Cancel background tasks
        for task in self._monitoring_tasks:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

        self._monitoring_tasks.clear()
        self.logger.info("Production monitoring dashboard stopped")

    async def _system_metrics_loop(self) -> None:
        """Background loop to collect system metrics."""
        while self._running:
            try:
                # Collect system memory usage
                memory_usage_mb = await self._get_memory_usage()
                await self.metrics_collector.record_metric(
                    "system_memory_usage_mb",
                    memory_usage_mb,
                    labels={"component": "system"},
                )

                # Collect CPU usage if available
                cpu_percent = await self._get_cpu_usage()
                if cpu_percent is not None:
                    await self.metrics_collector.record_metric(
                        "system_cpu_percent",
                        cpu_percent,
                        labels={"component": "system"},
                    )

                await asyncio.sleep(30)  # Collect every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("System metrics collection failed", error=str(e))
                await asyncio.sleep(30)

    async def _alert_evaluation_loop(self) -> None:
        """Background loop to evaluate alerts."""
        while self._running:
            try:
                # Get current metric values and evaluate alerts
                metrics_summary = await self.metrics_collector.get_all_metrics_summary()

                for metric_name, summary in metrics_summary.items():
                    # Map metric names to types for alert evaluation
                    metric_type = self._get_metric_type_from_name(metric_name)
                    if metric_type:
                        await self.alert_manager.evaluate_metric(
                            metric_name, summary["latest_value"], metric_type
                        )

                await asyncio.sleep(10)  # Evaluate every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Alert evaluation failed", error=str(e))
                await asyncio.sleep(10)

    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup tasks."""
        while self._running:
            try:
                # Clean up old alert history (keep last 7 days)
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.alert_manager.alert_history = [
                    alert
                    for alert in self.alert_manager.alert_history
                    if alert.created_at >= cutoff_time
                ]

                await asyncio.sleep(3600)  # Cleanup every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Cleanup loop failed", error=str(e))
                await asyncio.sleep(3600)

    def _get_metric_type_from_name(self, metric_name: str) -> Optional[MetricType]:
        """Map metric name to metric type for alert evaluation."""
        type_mapping = {
            "throughput": MetricType.THROUGHPUT,
            "items_per_second": MetricType.THROUGHPUT,
            "error_rate": MetricType.ERROR_RATE,
            "memory_usage": MetricType.MEMORY_USAGE,
            "system_memory_usage_mb": MetricType.MEMORY_USAGE,
            "database_query_time": MetricType.DATABASE_PERFORMANCE,
            "embedding_processing_time": MetricType.EMBEDDING_SERVICE,
            "queue_size": MetricType.QUEUE_SIZE,
        }

        for pattern, metric_type in type_mapping.items():
            if pattern in metric_name.lower():
                return metric_type

        return None

    async def record_import_metrics(
        self,
        throughput_items_per_sec: float,
        error_rate_percent: float,
        memory_usage_mb: float,
        processed_items: int,
        failed_items: int,
    ) -> None:
        """Record import-specific metrics."""
        await self.metrics_collector.record_metric(
            "import_throughput_items_per_sec",
            throughput_items_per_sec,
            labels={"component": "import"},
        )

        await self.metrics_collector.record_metric(
            "import_error_rate_percent",
            error_rate_percent,
            labels={"component": "import"},
        )

        await self.metrics_collector.record_metric(
            "import_memory_usage_mb", memory_usage_mb, labels={"component": "import"}
        )

        await self.metrics_collector.record_metric(
            "import_processed_items_total",
            processed_items,
            labels={"component": "import", "type": "processed"},
        )

        await self.metrics_collector.record_metric(
            "import_failed_items_total",
            failed_items,
            labels={"component": "import", "type": "failed"},
        )

    async def record_database_metrics(
        self, query_time_ms: float, connection_count: int, pool_utilization: float
    ) -> None:
        """Record database performance metrics."""
        await self.metrics_collector.record_metric(
            "database_query_time_ms", query_time_ms, labels={"component": "database"}
        )

        await self.metrics_collector.record_metric(
            "database_connections_active",
            connection_count,
            labels={"component": "database"},
        )

        await self.metrics_collector.record_metric(
            "database_pool_utilization",
            pool_utilization,
            labels={"component": "database"},
        )

    async def record_embedding_metrics(
        self, processing_time_ms: float, cache_hit_rate: float, queue_size: int
    ) -> None:
        """Record embedding service metrics."""
        await self.metrics_collector.record_metric(
            "embedding_processing_time_ms",
            processing_time_ms,
            labels={"component": "embedding"},
        )

        await self.metrics_collector.record_metric(
            "embedding_cache_hit_rate",
            cache_hit_rate,
            labels={"component": "embedding"},
        )

        await self.metrics_collector.record_metric(
            "embedding_queue_size", queue_size, labels={"component": "embedding"}
        )

    async def get_dashboard_data(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        # Get metrics summary
        metrics_summary = await self.metrics_collector.get_all_metrics_summary()

        # Get active alerts
        active_alerts = await self.alert_manager.get_active_alerts()

        # Get alert history
        alert_history = await self.alert_manager.get_alert_history(hours=24)

        # Calculate key performance indicators
        kpis = await self._calculate_kpis(duration_minutes)

        # Get time series data for charts
        charts_data = await self._get_charts_data(duration_minutes)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_summary": metrics_summary,
            "active_alerts": [alert.to_dict() for alert in active_alerts],
            "alert_history": [alert.to_dict() for alert in alert_history],
            "kpis": kpis,
            "charts": charts_data,
            "system_health": await self._get_system_health_score(),
        }

    async def _calculate_kpis(self, duration_minutes: int) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        kpis = {}

        # Throughput KPIs
        avg_throughput = await self.metrics_collector.calculate_average(
            "import_throughput_items_per_sec", duration_minutes
        )
        if avg_throughput is not None:
            kpis["average_throughput_items_per_sec"] = avg_throughput

        # Error rate KPIs
        avg_error_rate = await self.metrics_collector.calculate_average(
            "import_error_rate_percent", duration_minutes
        )
        if avg_error_rate is not None:
            kpis["average_error_rate_percent"] = avg_error_rate

        # Memory usage KPIs
        current_memory = await self.metrics_collector.get_latest_value(
            "import_memory_usage_mb"
        )
        if current_memory is not None:
            kpis["current_memory_usage_mb"] = current_memory

        # Database performance KPIs
        avg_db_time = await self.metrics_collector.calculate_average(
            "database_query_time_ms", duration_minutes
        )
        if avg_db_time is not None:
            kpis["average_database_query_time_ms"] = avg_db_time

        return kpis

    async def _get_charts_data(
        self, duration_minutes: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get time series data for dashboard charts."""
        charts = {}

        # Key metrics for charts
        chart_metrics = [
            "import_throughput_items_per_sec",
            "import_error_rate_percent",
            "import_memory_usage_mb",
            "database_query_time_ms",
            "embedding_processing_time_ms",
        ]

        for metric_name in chart_metrics:
            history = await self.metrics_collector.get_metric_history(
                metric_name, duration_minutes
            )
            charts[metric_name] = [point.to_dict() for point in history]

        return charts

    async def _get_system_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        health_score = 100.0
        health_factors = []

        # Check active critical alerts
        active_alerts = await self.alert_manager.get_active_alerts()
        critical_alerts = [
            a for a in active_alerts if a.severity == AlertSeverity.CRITICAL
        ]
        warning_alerts = [
            a for a in active_alerts if a.severity == AlertSeverity.WARNING
        ]

        if critical_alerts:
            health_score -= len(critical_alerts) * 30  # -30 per critical alert
            health_factors.append(f"{len(critical_alerts)} critical alerts")

        if warning_alerts:
            health_score -= len(warning_alerts) * 10  # -10 per warning alert
            health_factors.append(f"{len(warning_alerts)} warning alerts")

        # Check recent error rates
        recent_error_rate = await self.metrics_collector.calculate_average(
            "import_error_rate_percent", 5
        )
        if recent_error_rate is not None and recent_error_rate > 5.0:
            health_score -= min(
                recent_error_rate * 2, 30
            )  # Up to -30 for high error rates
            health_factors.append(f"{recent_error_rate:.1f}% error rate")

        # Check throughput
        recent_throughput = await self.metrics_collector.calculate_average(
            "import_throughput_items_per_sec", 5
        )
        if recent_throughput is not None and recent_throughput < 50.0:
            health_score -= 50 - recent_throughput  # Deduct based on low throughput
            health_factors.append(f"Low throughput: {recent_throughput:.1f} items/sec")

        health_score = max(0.0, health_score)  # Don't go below 0

        # Determine health status
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        elif health_score >= 25:
            health_status = "poor"
        else:
            health_status = "critical"

        return {
            "score": health_score,
            "status": health_status,
            "factors": health_factors,
            "active_alerts_count": len(active_alerts),
            "critical_alerts_count": len(critical_alerts),
        }

    async def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

    async def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        try:
            import psutil

            return psutil.cpu_percent(interval=1)
        except ImportError:
            return None

    async def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        dashboard_data = await self.get_dashboard_data()

        if format_type.lower() == "json":
            return json.dumps(dashboard_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of monitoring system itself."""
        try:
            metrics_count = len(self.metrics_collector.metrics)
            active_alerts_count = len(self.alert_manager.active_alerts)
            alert_rules_count = len(self.alert_manager.alert_rules)

            return {
                "status": "healthy",
                "monitoring_active": self._running,
                "background_tasks": len(self._monitoring_tasks),
                "metrics_tracked": metrics_count,
                "alert_rules": alert_rules_count,
                "active_alerts": active_alerts_count,
                "last_collection_time": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
