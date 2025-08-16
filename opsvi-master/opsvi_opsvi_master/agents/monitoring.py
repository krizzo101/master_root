"""Agent monitoring and performance tracking system.

This module provides comprehensive monitoring capabilities for agents including:
- Real-time performance metrics collection
- Resource usage tracking  
- Task execution analytics
- Health status monitoring
- Alert generation and notification
"""

from __future__ import annotations

import asyncio
import logging
import psutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from statistics import mean, median

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""

    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point."""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent."""

    # Task execution metrics
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0

    # Resource metrics
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0

    # Communication metrics
    messages_sent: int = 0
    messages_received: int = 0

    # Health metrics
    uptime_seconds: float = 0.0
    last_heartbeat: Optional[datetime] = None
    error_count: int = 0

    # Timestamp
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Alert:
    """Alert information."""

    id: str
    level: AlertLevel
    message: str
    agent_id: str
    metric_name: str
    threshold_value: float
    actual_value: float
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.resolved_at is None


class MetricCollector:
    """Collects and stores metrics for analysis."""

    def __init__(self, max_points: int = 1000):
        """Initialize metric collector.

        Args:
            max_points: Maximum number of metric points to retain
        """
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)

    def record_counter(
        self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric."""
        self.counters[name] += value
        self._add_point(name, value, tags or {})

    def record_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric."""
        self.gauges[name] = value
        self._add_point(name, value, tags or {})

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric."""
        self._add_point(name, duration, tags or {})

    def _add_point(self, name: str, value: float, tags: Dict[str, str]) -> None:
        """Add a metric point."""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc), value=value, tags=tags
        )
        self.metrics[name].append(point)

    def get_recent_values(self, name: str, duration_minutes: int = 5) -> List[float]:
        """Get recent values for a metric."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)

        if name not in self.metrics:
            return []

        return [point.value for point in self.metrics[name] if point.timestamp > cutoff]

    def get_statistics(self, name: str, duration_minutes: int = 5) -> Dict[str, float]:
        """Get statistics for a metric."""
        values = self.get_recent_values(name, duration_minutes)

        if not values:
            return {}

        return {
            "count": len(values),
            "mean": mean(values),
            "median": median(values),
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
        }


class PerformanceMonitor:
    """Monitors agent performance and resource usage."""

    def __init__(self, agent_id: str):
        """Initialize performance monitor for an agent."""
        self.agent_id = agent_id
        self.start_time = time.time()
        self.metrics = PerformanceMetrics()
        self.collector = MetricCollector()
        self.process = psutil.Process()

        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor.{agent_id}")

    def start_task_timer(self) -> float:
        """Start timing a task execution."""
        return time.time()

    def end_task_timer(self, start_time: float, success: bool = True) -> float:
        """End task timing and record metrics."""
        duration = time.time() - start_time

        if success:
            self.metrics.tasks_completed += 1
            self.collector.record_counter("tasks.completed")
        else:
            self.metrics.tasks_failed += 1
            self.collector.record_counter("tasks.failed")

        self.metrics.total_execution_time += duration
        if self.metrics.tasks_completed > 0:
            self.metrics.average_execution_time = (
                self.metrics.total_execution_time / self.metrics.tasks_completed
            )

        self.collector.record_timer(
            "task.duration", duration, {"success": str(success)}
        )

        return duration

    def record_message_sent(self) -> None:
        """Record that a message was sent."""
        self.metrics.messages_sent += 1
        self.collector.record_counter("messages.sent")

    def record_message_received(self) -> None:
        """Record that a message was received."""
        self.metrics.messages_received += 1
        self.collector.record_counter("messages.received")

    def record_error(self) -> None:
        """Record an error occurrence."""
        self.metrics.error_count += 1
        self.collector.record_counter("errors")

    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        self.metrics.last_heartbeat = datetime.now(timezone.utc)
        self.collector.record_gauge("heartbeat", 1.0)

    def collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.metrics.cpu_usage_percent = cpu_percent
            self.collector.record_gauge("cpu.usage_percent", cpu_percent)

            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.metrics.memory_usage_mb = memory_mb
            self.collector.record_gauge("memory.usage_mb", memory_mb)

            # Uptime
            uptime = time.time() - self.start_time
            self.metrics.uptime_seconds = uptime
            self.collector.record_gauge("uptime.seconds", uptime)

        except Exception as e:
            self.logger.warning(f"Failed to collect system metrics: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        self.collect_system_metrics()

        # Calculate additional metrics
        success_rate = 0.0
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total_tasks > 0:
            success_rate = self.metrics.tasks_completed / total_tasks

        message_ratio = 0.0
        if self.metrics.messages_received > 0:
            message_ratio = self.metrics.messages_sent / self.metrics.messages_received

        return {
            "agent_id": self.agent_id,
            "uptime_seconds": self.metrics.uptime_seconds,
            "tasks": {
                "completed": self.metrics.tasks_completed,
                "failed": self.metrics.tasks_failed,
                "success_rate": success_rate,
                "average_duration": self.metrics.average_execution_time,
            },
            "resources": {
                "cpu_percent": self.metrics.cpu_usage_percent,
                "memory_mb": self.metrics.memory_usage_mb,
            },
            "communication": {
                "messages_sent": self.metrics.messages_sent,
                "messages_received": self.metrics.messages_received,
                "send_receive_ratio": message_ratio,
            },
            "health": {
                "error_count": self.metrics.error_count,
                "last_heartbeat": self.metrics.last_heartbeat.isoformat()
                if self.metrics.last_heartbeat
                else None,
            },
            "collected_at": self.metrics.collected_at.isoformat(),
        }

    def get_metric_statistics(
        self, metric_name: str, duration_minutes: int = 5
    ) -> Dict[str, float]:
        """Get statistics for a specific metric."""
        return self.collector.get_statistics(metric_name, duration_minutes)


class AlertManager:
    """Manages alerts and thresholds for agents."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[str, Alert] = {}
        self.thresholds: Dict[str, Dict[str, Any]] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []

        self.logger = logging.getLogger(f"{__name__}.AlertManager")

    def set_threshold(
        self,
        metric_name: str,
        threshold_value: float,
        level: AlertLevel = AlertLevel.WARNING,
        comparison: str = "greater_than",
    ) -> None:
        """Set alert threshold for a metric.

        Args:
            metric_name: Name of metric to monitor
            threshold_value: Threshold value
            level: Alert level
            comparison: Comparison type ("greater_than", "less_than", "equals")
        """
        self.thresholds[metric_name] = {
            "value": threshold_value,
            "level": level,
            "comparison": comparison,
        }

    def check_thresholds(self, agent_id: str, metrics: Dict[str, float]) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []

        for metric_name, metric_value in metrics.items():
            if metric_name not in self.thresholds:
                continue

            threshold = self.thresholds[metric_name]

            # Check threshold
            threshold_exceeded = False
            comparison = threshold["comparison"]
            threshold_value = threshold["value"]

            if comparison == "greater_than" and metric_value > threshold_value:
                threshold_exceeded = True
            elif comparison == "less_than" and metric_value < threshold_value:
                threshold_exceeded = True
            elif comparison == "equals" and metric_value == threshold_value:
                threshold_exceeded = True

            if threshold_exceeded:
                alert_id = f"{agent_id}_{metric_name}_{int(time.time())}"

                alert = Alert(
                    id=alert_id,
                    level=threshold["level"],
                    message=f"Metric {metric_name} exceeded threshold: {metric_value} {comparison} {threshold_value}",
                    agent_id=agent_id,
                    metric_name=metric_name,
                    threshold_value=threshold_value,
                    actual_value=metric_value,
                )

                self.alerts[alert_id] = alert
                new_alerts.append(alert)

                # Notify handlers
                for handler in self.alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        self.logger.error(f"Alert handler failed: {e}")

        return new_alerts

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)
            return True
        return False

    def get_active_alerts(self, agent_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts."""
        alerts = [alert for alert in self.alerts.values() if alert.is_active]

        if agent_id:
            alerts = [alert for alert in alerts if alert.agent_id == agent_id]

        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)

    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler."""
        self.alert_handlers.append(handler)


class AgentMonitor:
    """Comprehensive monitoring for a single agent."""

    def __init__(self, agent_id: str):
        """Initialize agent monitor."""
        self.agent_id = agent_id
        self.performance_monitor = PerformanceMonitor(agent_id)
        self.alert_manager = AlertManager()
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None

        # Set default thresholds
        self._set_default_thresholds()

        self.logger = logging.getLogger(f"{__name__}.AgentMonitor.{agent_id}")

    def _set_default_thresholds(self) -> None:
        """Set default alert thresholds."""
        self.alert_manager.set_threshold("cpu.usage_percent", 80.0, AlertLevel.WARNING)
        self.alert_manager.set_threshold("cpu.usage_percent", 95.0, AlertLevel.CRITICAL)
        self.alert_manager.set_threshold("memory.usage_mb", 1000.0, AlertLevel.WARNING)
        self.alert_manager.set_threshold("memory.usage_mb", 2000.0, AlertLevel.CRITICAL)
        self.alert_manager.set_threshold("errors", 5.0, AlertLevel.WARNING)
        self.alert_manager.set_threshold("errors", 10.0, AlertLevel.ERROR)

    async def start(self) -> None:
        """Start monitoring."""
        if self.running:
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Monitoring started for agent {self.agent_id}")

    async def stop(self) -> None:
        """Stop monitoring."""
        if not self.running:
            return

        self.running = False

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info(f"Monitoring stopped for agent {self.agent_id}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect metrics
                self.performance_monitor.collect_system_metrics()

                # Check for alerts
                current_metrics = {
                    "cpu.usage_percent": self.performance_monitor.metrics.cpu_usage_percent,
                    "memory.usage_mb": self.performance_monitor.metrics.memory_usage_mb,
                    "errors": self.performance_monitor.metrics.error_count,
                }

                new_alerts = self.alert_manager.check_thresholds(
                    self.agent_id, current_metrics
                )

                if new_alerts:
                    self.logger.warning(f"Generated {len(new_alerts)} new alerts")

                # Sleep before next collection
                await asyncio.sleep(30)  # Collect every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    # Delegate methods to performance monitor
    def start_task_timer(self) -> float:
        return self.performance_monitor.start_task_timer()

    def end_task_timer(self, start_time: float, success: bool = True) -> float:
        return self.performance_monitor.end_task_timer(start_time, success)

    def record_message_sent(self) -> None:
        self.performance_monitor.record_message_sent()

    def record_message_received(self) -> None:
        self.performance_monitor.record_message_received()

    def record_error(self) -> None:
        self.performance_monitor.record_error()

    def update_heartbeat(self) -> None:
        self.performance_monitor.update_heartbeat()

    def get_performance_summary(self) -> Dict[str, Any]:
        return self.performance_monitor.get_performance_summary()

    def get_active_alerts(self) -> List[Alert]:
        return self.alert_manager.get_active_alerts(self.agent_id)

    def set_threshold(
        self,
        metric_name: str,
        threshold_value: float,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        self.alert_manager.set_threshold(metric_name, threshold_value, level)


# Global monitoring registry
_monitoring_registry: Dict[str, AgentMonitor] = {}


def get_agent_monitor(agent_id: str) -> AgentMonitor:
    """Get or create monitor for an agent."""
    if agent_id not in _monitoring_registry:
        _monitoring_registry[agent_id] = AgentMonitor(agent_id)
    return _monitoring_registry[agent_id]


async def start_monitoring(agent_id: str) -> AgentMonitor:
    """Start monitoring for an agent."""
    monitor = get_agent_monitor(agent_id)
    await monitor.start()
    return monitor


async def stop_monitoring(agent_id: str) -> None:
    """Stop monitoring for an agent."""
    if agent_id in _monitoring_registry:
        await _monitoring_registry[agent_id].stop()
        del _monitoring_registry[agent_id]


def get_all_agents_summary() -> Dict[str, Any]:
    """Get performance summary for all monitored agents."""
    return {
        agent_id: monitor.get_performance_summary()
        for agent_id, monitor in _monitoring_registry.items()
    }
