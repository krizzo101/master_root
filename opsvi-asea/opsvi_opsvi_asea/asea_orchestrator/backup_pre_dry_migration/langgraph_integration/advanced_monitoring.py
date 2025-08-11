"""
Phase 3: Advanced Monitoring and Metrics for ASEA-LangGraph Integration

Implements comprehensive monitoring capabilities including:
1. Real-time Metrics Collection
2. Performance Analytics and Dashboards
3. Workflow Health Monitoring
4. Resource Usage Tracking
5. Alerting and Notification Systems
"""

import time
import json
import threading
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics

from .state import ASEAState


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"  # Incrementing count
    GAUGE = "gauge"  # Current value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements
    RATE = "rate"  # Events per time unit


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point."""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """Alert definition and state."""

    alert_id: str
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message: str
    cooldown_seconds: int = 300
    last_triggered: Optional[float] = None
    trigger_count: int = 0
    is_active: bool = False


class MetricsCollector:
    """
    Collects and aggregates metrics from workflow execution.

    Provides:
    - Real-time metric collection
    - Time-series data storage
    - Statistical aggregations
    - Metric export capabilities
    """

    def __init__(self, retention_hours: int = 24):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.retention_hours = retention_hours
        self.lock = threading.RLock()

        # Performance counters
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_old_metrics, daemon=True
        )
        self._cleanup_thread.start()

    def record_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Record a counter metric."""
        with self.lock:
            self.counters[name] += value
            metric = Metric(
                name=name,
                value=self.counters[name],
                metric_type=MetricType.COUNTER,
                timestamp=time.time(),
                labels=labels or {},
            )
            self.metrics[name].append(metric)

    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric."""
        with self.lock:
            self.gauges[name] = value
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                timestamp=time.time(),
                labels=labels or {},
            )
            self.metrics[name].append(metric)

    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer metric."""
        with self.lock:
            self.timers[name].append(duration)
            metric = Metric(
                name=name,
                value=duration,
                metric_type=MetricType.TIMER,
                timestamp=time.time(),
                labels=labels or {},
                unit="seconds",
            )
            self.metrics[name].append(metric)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        with self.lock:
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                timestamp=time.time(),
                labels=labels or {},
            )
            self.metrics[name].append(metric)

    def get_metric_summary(
        self, name: str, time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get statistical summary of a metric over time window."""
        with self.lock:
            if name not in self.metrics:
                return {}

            cutoff_time = time.time() - (time_window_minutes * 60)
            recent_metrics = [
                m for m in self.metrics[name] if m.timestamp >= cutoff_time
            ]

            if not recent_metrics:
                return {}

            values = [m.value for m in recent_metrics]

            summary = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "latest": values[-1] if values else 0,
                "time_window_minutes": time_window_minutes,
            }

            if len(values) > 1:
                summary["stddev"] = statistics.stdev(values)
                summary["median"] = statistics.median(values)

            # Add percentiles for larger datasets
            if len(values) >= 10:
                sorted_values = sorted(values)
                summary["p95"] = sorted_values[int(0.95 * len(sorted_values))]
                summary["p99"] = sorted_values[int(0.99 * len(sorted_values))]

            return summary

    def get_all_metrics_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        summaries = {}
        for metric_name in self.metrics:
            summaries[metric_name] = self.get_metric_summary(metric_name)
        return summaries

    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        if format_type == "json":
            return json.dumps(self.get_all_metrics_summary(), indent=2)
        elif format_type == "prometheus":
            return self._export_prometheus_format()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        for metric_name, summary in self.get_all_metrics_summary().items():
            if not summary:
                continue

            # Add help and type comments
            lines.append(f"# HELP {metric_name} Workflow metric")
            lines.append(f"# TYPE {metric_name} gauge")

            # Add metric values
            for stat_name, value in summary.items():
                if isinstance(value, (int, float)):
                    lines.append(f"{metric_name}_{stat_name} {value}")

        return "\n".join(lines)

    def _cleanup_old_metrics(self):
        """Background thread to clean up old metrics."""
        while True:
            try:
                time.sleep(3600)  # Run every hour
                cutoff_time = time.time() - (self.retention_hours * 3600)

                with self.lock:
                    for metric_name in list(self.metrics.keys()):
                        self.metrics[metric_name] = [
                            m
                            for m in self.metrics[metric_name]
                            if m.timestamp >= cutoff_time
                        ]

                        # Remove empty metric lists
                        if not self.metrics[metric_name]:
                            del self.metrics[metric_name]

            except Exception as e:
                print(f"Metrics cleanup error: {e}")


class WorkflowMonitor:
    """
    Monitors workflow execution and health.

    Provides:
    - Workflow performance tracking
    - Error rate monitoring
    - Resource usage analysis
    - Health status assessment
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    def start_workflow_monitoring(
        self, workflow_name: str, run_id: str, initial_state: ASEAState
    ):
        """Start monitoring a workflow execution."""
        with self.lock:
            self.active_workflows[run_id] = {
                "workflow_name": workflow_name,
                "start_time": time.time(),
                "state_updates": 0,
                "error_count": 0,
                "last_activity": time.time(),
                "initial_state_size": len(str(initial_state)),
                "status": "running",
            }

        self.metrics.record_counter("workflows_started", 1, {"workflow": workflow_name})
        self.metrics.record_gauge("active_workflows", len(self.active_workflows))

    def update_workflow_state(self, run_id: str, state: ASEAState):
        """Update monitoring data for a workflow state change."""
        with self.lock:
            if run_id in self.active_workflows:
                workflow_info = self.active_workflows[run_id]
                workflow_info["state_updates"] += 1
                workflow_info["last_activity"] = time.time()
                workflow_info["current_state_size"] = len(str(state))
                workflow_info["error_count"] = len(state.get("errors", []))

                # Record metrics
                self.metrics.record_counter(
                    "state_updates", 1, {"workflow": workflow_info["workflow_name"]}
                )

                if state.get("errors"):
                    self.metrics.record_counter(
                        "workflow_errors",
                        len(state["errors"]),
                        {"workflow": workflow_info["workflow_name"]},
                    )

    def finish_workflow_monitoring(
        self, run_id: str, final_state: ASEAState, success: bool
    ):
        """Finish monitoring a workflow execution."""
        with self.lock:
            if run_id not in self.active_workflows:
                return

            workflow_info = self.active_workflows[run_id]
            duration = time.time() - workflow_info["start_time"]

            # Record final metrics
            workflow_name = workflow_info["workflow_name"]
            self.metrics.record_timer(
                "workflow_duration", duration, {"workflow": workflow_name}
            )
            self.metrics.record_counter(
                "workflows_completed",
                1,
                {"workflow": workflow_name, "success": str(success)},
            )

            # Record detailed performance metrics
            self.metrics.record_histogram(
                "state_updates_per_workflow",
                workflow_info["state_updates"],
                {"workflow": workflow_name},
            )
            self.metrics.record_histogram(
                "final_state_size",
                workflow_info.get("current_state_size", 0),
                {"workflow": workflow_name},
            )

            # Clean up
            del self.active_workflows[run_id]
            self.metrics.record_gauge("active_workflows", len(self.active_workflows))

    def get_workflow_health(self) -> Dict[str, Any]:
        """Get overall workflow health status."""
        with self.lock:
            now = time.time()

            # Analyze active workflows
            active_count = len(self.active_workflows)
            stale_workflows = 0
            long_running_workflows = 0

            for run_id, info in self.active_workflows.items():
                age = now - info["start_time"]
                last_activity_age = now - info["last_activity"]

                if last_activity_age > 300:  # 5 minutes
                    stale_workflows += 1

                if age > 1800:  # 30 minutes
                    long_running_workflows += 1

            # Get recent error rates
            error_summary = self.metrics.get_metric_summary("workflow_errors", 60)
            duration_summary = self.metrics.get_metric_summary("workflow_duration", 60)

            health_status = "healthy"
            if stale_workflows > active_count * 0.5:
                health_status = "degraded"
            if long_running_workflows > 0 or error_summary.get("count", 0) > 10:
                health_status = "unhealthy"

            return {
                "status": health_status,
                "active_workflows": active_count,
                "stale_workflows": stale_workflows,
                "long_running_workflows": long_running_workflows,
                "error_rate_last_hour": error_summary.get("count", 0),
                "avg_duration_last_hour": duration_summary.get("mean", 0),
                "timestamp": now,
            }


class AlertManager:
    """
    Manages alerts and notifications for workflow monitoring.

    Provides:
    - Alert rule configuration
    - Condition evaluation
    - Alert state management
    - Notification dispatch
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable[[Alert, Dict[str, Any]], None]] = []
        self.lock = threading.RLock()

        # Start alert evaluation thread
        self._evaluation_thread = threading.Thread(
            target=self._evaluate_alerts, daemon=True
        )
        self._evaluation_thread.start()

    def add_alert(self, alert: Alert):
        """Add an alert rule."""
        with self.lock:
            self.alerts[alert.alert_id] = alert

    def add_notification_handler(
        self, handler: Callable[[Alert, Dict[str, Any]], None]
    ):
        """Add a notification handler function."""
        self.notification_handlers.append(handler)

    def create_threshold_alert(
        self,
        alert_id: str,
        metric_name: str,
        threshold: float,
        comparison: str = "greater",
        severity: AlertSeverity = AlertSeverity.WARNING,
        time_window_minutes: int = 5,
    ) -> Alert:
        """Create a threshold-based alert."""

        def condition(metrics_data: Dict[str, Any]) -> bool:
            summary = self.metrics.get_metric_summary(metric_name, time_window_minutes)
            if not summary:
                return False

            current_value = summary.get("latest", 0)

            if comparison == "greater":
                return current_value > threshold
            elif comparison == "less":
                return current_value < threshold
            elif comparison == "equal":
                return abs(current_value - threshold) < 0.001
            else:
                return False

        alert = Alert(
            alert_id=alert_id,
            name=f"{metric_name} {comparison} {threshold}",
            condition=condition,
            severity=severity,
            message=f"Metric {metric_name} is {comparison} than {threshold}",
        )

        self.add_alert(alert)
        return alert

    def create_rate_alert(
        self,
        alert_id: str,
        metric_name: str,
        rate_threshold: float,
        severity: AlertSeverity = AlertSeverity.ERROR,
        time_window_minutes: int = 10,
    ) -> Alert:
        """Create a rate-based alert (events per minute)."""

        def condition(metrics_data: Dict[str, Any]) -> bool:
            summary = self.metrics.get_metric_summary(metric_name, time_window_minutes)
            if not summary or summary.get("count", 0) == 0:
                return False

            rate_per_minute = summary["count"] / time_window_minutes
            return rate_per_minute > rate_threshold

        alert = Alert(
            alert_id=alert_id,
            name=f"{metric_name} rate > {rate_threshold}/min",
            condition=condition,
            severity=severity,
            message=f"Rate of {metric_name} exceeds {rate_threshold} per minute",
        )

        self.add_alert(alert)
        return alert

    def _evaluate_alerts(self):
        """Background thread to evaluate alert conditions."""
        while True:
            try:
                time.sleep(30)  # Evaluate every 30 seconds

                with self.lock:
                    metrics_data = self.metrics.get_all_metrics_summary()

                    for alert in self.alerts.values():
                        self._evaluate_single_alert(alert, metrics_data)

            except Exception as e:
                print(f"Alert evaluation error: {e}")

    def _evaluate_single_alert(self, alert: Alert, metrics_data: Dict[str, Any]):
        """Evaluate a single alert condition."""
        try:
            condition_met = alert.condition(metrics_data)
            now = time.time()

            # Check cooldown period
            if (
                alert.last_triggered
                and now - alert.last_triggered < alert.cooldown_seconds
            ):
                return

            if condition_met and not alert.is_active:
                # Alert triggered
                alert.is_active = True
                alert.last_triggered = now
                alert.trigger_count += 1

                alert_event = {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": now,
                    "trigger_count": alert.trigger_count,
                    "metrics_snapshot": metrics_data,
                }

                self.alert_history.append(alert_event)

                # Send notifications
                for handler in self.notification_handlers:
                    try:
                        handler(alert, alert_event)
                    except Exception as e:
                        print(f"Notification handler error: {e}")

            elif not condition_met and alert.is_active:
                # Alert resolved
                alert.is_active = False

                resolve_event = {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "action": "resolved",
                    "timestamp": now,
                }

                self.alert_history.append(resolve_event)

        except Exception as e:
            print(f"Error evaluating alert {alert.alert_id}: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        with self.lock:
            return [
                {
                    "alert_id": alert.alert_id,
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "trigger_count": alert.trigger_count,
                    "last_triggered": alert.last_triggered,
                }
                for alert in self.alerts.values()
                if alert.is_active
            ]

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        with self.lock:
            return self.alert_history[-limit:]


def create_default_monitoring_setup() -> (
    Tuple[MetricsCollector, WorkflowMonitor, AlertManager]
):
    """Create a default monitoring setup with common alerts."""

    # Initialize components
    metrics_collector = MetricsCollector()
    workflow_monitor = WorkflowMonitor(metrics_collector)
    alert_manager = AlertManager(metrics_collector)

    # Add default alerts
    alert_manager.create_threshold_alert(
        "high_error_rate", "workflow_errors", 10, "greater", AlertSeverity.ERROR, 15
    )

    alert_manager.create_threshold_alert(
        "long_workflow_duration",
        "workflow_duration",
        300,  # 5 minutes
        "greater",
        AlertSeverity.WARNING,
        10,
    )

    alert_manager.create_rate_alert(
        "workflow_failure_rate",
        "workflows_completed",
        5,  # 5 failures per minute
        AlertSeverity.CRITICAL,
        10,
    )

    # Add console notification handler
    def console_notification_handler(alert: Alert, event: Dict[str, Any]):
        severity = event["severity"].upper()
        timestamp = datetime.fromtimestamp(event["timestamp"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(f"🚨 [{severity}] {timestamp} - {event['name']}: {event['message']}")

    alert_manager.add_notification_handler(console_notification_handler)

    return metrics_collector, workflow_monitor, alert_manager
