"""
Advanced Metrics Collection System
Collects and aggregates real-time metrics from agent execution
"""
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected"""

    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_SPAWN = "agent_spawn"
    AGENT_TERMINATE = "agent_terminate"
    TOKEN_USAGE = "token_usage"
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    QUEUE_DEPTH = "queue_depth"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class Metric:
    """Individual metric data point"""

    metric_type: MetricType
    value: Union[int, float, str]
    timestamp: float = field(default_factory=time.time)
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "metadata": self.metadata,
        }


@dataclass
class MetricsSummary:
    """Aggregated metrics summary"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_agents: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    error_rate: float = 0.0
    throughput_per_minute: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class MetricsCollector:
    """Thread-safe metrics collection and aggregation"""

    def __init__(self, history_size: int = 10000, aggregate_interval: int = 5):
        self.history_size = history_size
        self.aggregate_interval = aggregate_interval

        # Thread-safe collections
        self._lock = threading.RLock()
        self._metrics = deque(maxlen=history_size)
        self._active_tasks = {}  # task_id -> start_time
        self._active_agents = set()
        self._subscribers = []  # Callbacks for real-time updates

        # Aggregated data
        self._summary = MetricsSummary()
        self._last_aggregate_time = time.time()

        # Background aggregation
        self._aggregation_thread = threading.Thread(
            target=self._background_aggregation, daemon=True
        )
        self._running = True
        self._aggregation_thread.start()

        logger.info("MetricsCollector initialized with history_size=%d", history_size)

    def record_metric(self, metric: Metric) -> None:
        """Record a new metric"""
        with self._lock:
            self._metrics.append(metric)

            # Update active tracking
            if metric.metric_type == MetricType.TASK_STARTED:
                self._active_tasks[metric.task_id] = metric.timestamp
            elif metric.metric_type == MetricType.TASK_COMPLETED:
                self._active_tasks.pop(metric.task_id, None)
            elif metric.metric_type == MetricType.TASK_FAILED:
                self._active_tasks.pop(metric.task_id, None)
            elif metric.metric_type == MetricType.AGENT_SPAWN:
                self._active_agents.add(metric.agent_id)
            elif metric.metric_type == MetricType.AGENT_TERMINATE:
                self._active_agents.discard(metric.agent_id)

        # Notify subscribers
        self._notify_subscribers(metric)

        logger.debug("Recorded metric: %s", metric.metric_type.value)

    def record_task_started(
        self, task_id: str, agent_id: str = None, metadata: Dict[str, Any] = None
    ) -> None:
        """Convenience method for recording task start"""
        metric = Metric(
            metric_type=MetricType.TASK_STARTED,
            value=1,
            task_id=task_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self.record_metric(metric)

    def record_task_completed(
        self,
        task_id: str,
        agent_id: str = None,
        execution_time: float = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Convenience method for recording task completion"""
        metric = Metric(
            metric_type=MetricType.TASK_COMPLETED,
            value=1,
            task_id=task_id,
            agent_id=agent_id,
            metadata=metadata or {},
        )
        self.record_metric(metric)

        if execution_time:
            exec_metric = Metric(
                metric_type=MetricType.EXECUTION_TIME,
                value=execution_time,
                task_id=task_id,
                agent_id=agent_id,
                metadata=metadata or {},
            )
            self.record_metric(exec_metric)

    def record_task_failed(
        self,
        task_id: str,
        agent_id: str = None,
        error: str = None,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Convenience method for recording task failure"""
        fail_metadata = metadata or {}
        if error:
            fail_metadata["error"] = error

        metric = Metric(
            metric_type=MetricType.TASK_FAILED,
            value=1,
            task_id=task_id,
            agent_id=agent_id,
            metadata=fail_metadata,
        )
        self.record_metric(metric)

    def record_token_usage(
        self,
        agent_id: str,
        input_tokens: int,
        output_tokens: int,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Record token usage metrics"""
        usage_metadata = metadata or {}
        usage_metadata.update(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
        )

        metric = Metric(
            metric_type=MetricType.TOKEN_USAGE,
            value=input_tokens + output_tokens,
            agent_id=agent_id,
            metadata=usage_metadata,
        )
        self.record_metric(metric)

    def subscribe(self, callback: Callable[[Metric], None]) -> None:
        """Subscribe to real-time metric updates"""
        with self._lock:
            self._subscribers.append(callback)
        logger.info("Added metrics subscriber")

    def unsubscribe(self, callback: Callable[[Metric], None]) -> None:
        """Unsubscribe from metric updates"""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        logger.info("Removed metrics subscriber")

    def get_summary(self) -> MetricsSummary:
        """Get current metrics summary"""
        with self._lock:
            return MetricsSummary(
                total_tasks=self._summary.total_tasks,
                completed_tasks=self._summary.completed_tasks,
                failed_tasks=self._summary.failed_tasks,
                active_agents=len(self._active_agents),
                total_execution_time=self._summary.total_execution_time,
                average_execution_time=self._summary.average_execution_time,
                error_rate=self._summary.error_rate,
                throughput_per_minute=self._summary.throughput_per_minute,
                token_usage=dict(self._summary.token_usage),
                resource_utilization=dict(self._summary.resource_utilization),
                updated_at=self._summary.updated_at,
            )

    def get_recent_metrics(self, seconds: int = 300) -> List[Dict[str, Any]]:
        """Get metrics from the last N seconds"""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [
                metric.to_dict()
                for metric in self._metrics
                if metric.timestamp >= cutoff_time
            ]

    def get_metrics_by_type(
        self, metric_type: MetricType, seconds: int = 300
    ) -> List[Dict[str, Any]]:
        """Get specific metric type from the last N seconds"""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [
                metric.to_dict()
                for metric in self._metrics
                if metric.metric_type == metric_type and metric.timestamp >= cutoff_time
            ]

    def get_active_tasks(self) -> Dict[str, float]:
        """Get currently active tasks and their start times"""
        with self._lock:
            return dict(self._active_tasks)

    def get_active_agents(self) -> List[str]:
        """Get list of currently active agents"""
        with self._lock:
            return list(self._active_agents)

    def _notify_subscribers(self, metric: Metric) -> None:
        """Notify all subscribers of new metric"""
        with self._lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(metric)
            except Exception as e:
                logger.error("Error notifying subscriber: %s", e)

    def _background_aggregation(self) -> None:
        """Background thread for computing aggregated metrics"""
        while self._running:
            try:
                time.sleep(self.aggregate_interval)
                self._compute_aggregates()
            except Exception as e:
                logger.error("Error in background aggregation: %s", e)

    def _compute_aggregates(self) -> None:
        """Compute aggregated metrics"""
        current_time = time.time()
        window_start = current_time - 300  # 5 minute window

        with self._lock:
            # Get metrics from the last 5 minutes
            recent_metrics = [
                metric for metric in self._metrics if metric.timestamp >= window_start
            ]

            # Count metrics by type
            metric_counts = defaultdict(int)
            execution_times = []
            token_totals = defaultdict(int)

            for metric in recent_metrics:
                metric_counts[metric.metric_type] += 1

                if metric.metric_type == MetricType.EXECUTION_TIME:
                    execution_times.append(metric.value)
                elif metric.metric_type == MetricType.TOKEN_USAGE:
                    if metric.agent_id:
                        token_totals[metric.agent_id] += metric.value

            # Update summary
            total_tasks = metric_counts[MetricType.TASK_STARTED]
            completed = metric_counts[MetricType.TASK_COMPLETED]
            failed = metric_counts[MetricType.TASK_FAILED]

            self._summary.total_tasks = total_tasks
            self._summary.completed_tasks = completed
            self._summary.failed_tasks = failed
            self._summary.active_agents = len(self._active_agents)

            if execution_times:
                self._summary.total_execution_time = sum(execution_times)
                self._summary.average_execution_time = sum(execution_times) / len(
                    execution_times
                )

            if total_tasks > 0:
                self._summary.error_rate = failed / total_tasks
                # Throughput per minute
                time_window_minutes = (current_time - window_start) / 60
                self._summary.throughput_per_minute = completed / max(
                    time_window_minutes, 1
                )

            self._summary.token_usage = dict(token_totals)
            self._summary.updated_at = current_time

    def shutdown(self) -> None:
        """Shutdown the metrics collector"""
        self._running = False
        if self._aggregation_thread.is_alive():
            self._aggregation_thread.join(timeout=5)
        logger.info("MetricsCollector shutdown complete")


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_global_collector() -> MetricsCollector:
    """Get or create the global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def shutdown_global_collector() -> None:
    """Shutdown the global metrics collector"""
    global _global_collector
    if _global_collector:
        _global_collector.shutdown()
        _global_collector = None
