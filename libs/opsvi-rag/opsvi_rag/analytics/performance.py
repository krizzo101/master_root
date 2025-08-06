"""
Performance Analytics for OPSVI-RAG

Provides comprehensive performance monitoring, metrics collection, and analysis
for RAG systems including search latency, throughput, and quality metrics.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class SearchMetrics:
    """Metrics for a single search operation."""

    query: str
    search_type: str
    execution_time_ms: float
    results_count: int
    timestamp: datetime
    datastore_type: str
    success: bool
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class DatastoreMetrics:
    """Metrics for datastore operations."""

    operation: str  # add, update, delete, search
    execution_time_ms: float
    timestamp: datetime
    datastore_type: str
    success: bool
    document_count: int | None = None
    error_message: str | None = None


class PerformanceConfig(BaseModel):
    """Configuration for performance monitoring."""

    # Metrics collection
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_buffer_size: int = Field(
        default=10000, description="Maximum metrics to keep in memory"
    )

    # Performance thresholds
    slow_query_threshold_ms: float = Field(
        default=1000.0, description="Threshold for slow queries"
    )
    error_rate_threshold: float = Field(
        default=0.05, description="Error rate threshold (5%)"
    )

    # Reporting intervals
    report_interval_seconds: int = Field(
        default=300, description="Reporting interval (5 minutes)"
    )
    retention_hours: int = Field(default=24, description="Metrics retention period")

    # Alerting
    enable_alerts: bool = Field(default=True, description="Enable performance alerts")
    alert_cooldown_minutes: int = Field(default=10, description="Alert cooldown period")


class PerformanceMonitor:
    """Performance monitoring system for RAG operations."""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.search_metrics: deque = deque(maxlen=config.metrics_buffer_size)
        self.datastore_metrics: deque = deque(maxlen=config.metrics_buffer_size)
        self.alert_history: dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def record_search_metric(self, metric: SearchMetrics) -> None:
        """Record a search performance metric."""
        if not self.config.enable_metrics:
            return

        async with self._lock:
            self.search_metrics.append(metric)

            # Check for performance issues
            if self.config.enable_alerts:
                await self._check_search_alerts(metric)

    async def record_datastore_metric(self, metric: DatastoreMetrics) -> None:
        """Record a datastore operation metric."""
        if not self.config.enable_metrics:
            return

        async with self._lock:
            self.datastore_metrics.append(metric)

            # Check for performance issues
            if self.config.enable_alerts:
                await self._check_datastore_alerts(metric)

    async def _check_search_alerts(self, metric: SearchMetrics) -> None:
        """Check for search performance alerts."""
        alerts = []

        # Slow query alert
        if metric.execution_time_ms > self.config.slow_query_threshold_ms:
            alerts.append(
                {
                    "type": "slow_query",
                    "message": f"Slow query detected: {metric.execution_time_ms:.2f}ms",
                    "metric": metric,
                }
            )

        # Search failure alert
        if not metric.success:
            alerts.append(
                {
                    "type": "search_failure",
                    "message": f"Search failed: {metric.error_message}",
                    "metric": metric,
                }
            )

        # Process alerts
        for alert in alerts:
            await self._process_alert(alert)

    async def _check_datastore_alerts(self, metric: DatastoreMetrics) -> None:
        """Check for datastore performance alerts."""
        alerts = []

        # Slow operation alert
        if metric.execution_time_ms > self.config.slow_query_threshold_ms:
            alerts.append(
                {
                    "type": "slow_datastore_operation",
                    "message": f"Slow {metric.operation}: {metric.execution_time_ms:.2f}ms",
                    "metric": metric,
                }
            )

        # Operation failure alert
        if not metric.success:
            alerts.append(
                {
                    "type": "datastore_failure",
                    "message": f"{metric.operation} failed: {metric.error_message}",
                    "metric": metric,
                }
            )

        # Process alerts
        for alert in alerts:
            await self._process_alert(alert)

    async def _process_alert(self, alert: dict[str, Any]) -> None:
        """Process a performance alert."""
        alert_key = alert["type"]
        now = datetime.now()

        # Check cooldown period
        if alert_key in self.alert_history:
            last_alert = self.alert_history[alert_key]
            cooldown = timedelta(minutes=self.config.alert_cooldown_minutes)
            if now - last_alert < cooldown:
                return  # Still in cooldown

        # Log the alert
        logger.warning(f"Performance alert: {alert['message']}")

        # Update alert history
        self.alert_history[alert_key] = now

        # Here you could integrate with external alerting systems
        # e.g., send to monitoring systems, email, Slack, etc.

    async def get_search_statistics(
        self, time_window_minutes: int | None = None
    ) -> dict[str, Any]:
        """Get search performance statistics."""
        async with self._lock:
            metrics = list(self.search_metrics)

        if not metrics:
            return {"total_searches": 0}

        # Filter by time window if specified
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]

        if not metrics:
            return {"total_searches": 0}

        # Calculate statistics
        execution_times = [m.execution_time_ms for m in metrics]
        successful_searches = [m for m in metrics if m.success]
        failed_searches = [m for m in metrics if not m.success]

        # Group by search type
        by_search_type = defaultdict(list)
        for m in metrics:
            by_search_type[m.search_type].append(m)

        # Group by datastore type
        by_datastore = defaultdict(list)
        for m in metrics:
            by_datastore[m.datastore_type].append(m)

        stats = {
            "total_searches": len(metrics),
            "successful_searches": len(successful_searches),
            "failed_searches": len(failed_searches),
            "success_rate": len(successful_searches) / len(metrics) if metrics else 0,
            "error_rate": len(failed_searches) / len(metrics) if metrics else 0,
            "execution_time": {
                "mean_ms": np.mean(execution_times),
                "median_ms": np.median(execution_times),
                "p95_ms": np.percentile(execution_times, 95),
                "p99_ms": np.percentile(execution_times, 99),
                "min_ms": np.min(execution_times),
                "max_ms": np.max(execution_times),
                "std_ms": np.std(execution_times),
            },
            "by_search_type": {},
            "by_datastore": {},
            "slow_queries": len(
                [
                    m
                    for m in metrics
                    if m.execution_time_ms > self.config.slow_query_threshold_ms
                ]
            ),
            "time_window_minutes": time_window_minutes,
        }

        # Statistics by search type
        for search_type, type_metrics in by_search_type.items():
            type_times = [m.execution_time_ms for m in type_metrics]
            stats["by_search_type"][search_type] = {
                "count": len(type_metrics),
                "success_rate": len([m for m in type_metrics if m.success])
                / len(type_metrics),
                "mean_time_ms": np.mean(type_times),
                "median_time_ms": np.median(type_times),
            }

        # Statistics by datastore
        for datastore, ds_metrics in by_datastore.items():
            ds_times = [m.execution_time_ms for m in ds_metrics]
            stats["by_datastore"][datastore] = {
                "count": len(ds_metrics),
                "success_rate": len([m for m in ds_metrics if m.success])
                / len(ds_metrics),
                "mean_time_ms": np.mean(ds_times),
                "median_time_ms": np.median(ds_times),
            }

        return stats

    async def get_datastore_statistics(
        self, time_window_minutes: int | None = None
    ) -> dict[str, Any]:
        """Get datastore operation statistics."""
        async with self._lock:
            metrics = list(self.datastore_metrics)

        if not metrics:
            return {"total_operations": 0}

        # Filter by time window if specified
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            metrics = [m for m in metrics if m.timestamp >= cutoff]

        if not metrics:
            return {"total_operations": 0}

        # Calculate statistics
        execution_times = [m.execution_time_ms for m in metrics]
        successful_ops = [m for m in metrics if m.success]
        failed_ops = [m for m in metrics if not m.success]

        # Group by operation type
        by_operation = defaultdict(list)
        for m in metrics:
            by_operation[m.operation].append(m)

        # Group by datastore type
        by_datastore = defaultdict(list)
        for m in metrics:
            by_datastore[m.datastore_type].append(m)

        stats = {
            "total_operations": len(metrics),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": len(successful_ops) / len(metrics) if metrics else 0,
            "error_rate": len(failed_ops) / len(metrics) if metrics else 0,
            "execution_time": {
                "mean_ms": np.mean(execution_times),
                "median_ms": np.median(execution_times),
                "p95_ms": np.percentile(execution_times, 95),
                "p99_ms": np.percentile(execution_times, 99),
                "min_ms": np.min(execution_times),
                "max_ms": np.max(execution_times),
            },
            "by_operation": {},
            "by_datastore": {},
            "slow_operations": len(
                [
                    m
                    for m in metrics
                    if m.execution_time_ms > self.config.slow_query_threshold_ms
                ]
            ),
            "time_window_minutes": time_window_minutes,
        }

        # Statistics by operation type
        for operation, op_metrics in by_operation.items():
            op_times = [m.execution_time_ms for m in op_metrics]
            stats["by_operation"][operation] = {
                "count": len(op_metrics),
                "success_rate": len([m for m in op_metrics if m.success])
                / len(op_metrics),
                "mean_time_ms": np.mean(op_times),
                "median_time_ms": np.median(op_times),
            }

        # Statistics by datastore
        for datastore, ds_metrics in by_datastore.items():
            ds_times = [m.execution_time_ms for m in ds_metrics]
            stats["by_datastore"][datastore] = {
                "count": len(ds_metrics),
                "success_rate": len([m for m in ds_metrics if m.success])
                / len(ds_metrics),
                "mean_time_ms": np.mean(ds_times),
                "median_time_ms": np.median(ds_times),
            }

        return stats

    async def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary."""
        search_stats = await self.get_search_statistics(time_window_minutes=60)
        datastore_stats = await self.get_datastore_statistics(time_window_minutes=60)

        return {
            "timestamp": datetime.now().isoformat(),
            "search_performance": search_stats,
            "datastore_performance": datastore_stats,
            "system_health": {
                "search_error_rate": search_stats.get("error_rate", 0),
                "datastore_error_rate": datastore_stats.get("error_rate", 0),
                "slow_queries": search_stats.get("slow_queries", 0),
                "slow_operations": datastore_stats.get("slow_operations", 0),
                "overall_health": self._calculate_health_score(
                    search_stats, datastore_stats
                ),
            },
        }

    def _calculate_health_score(
        self, search_stats: dict[str, Any], datastore_stats: dict[str, Any]
    ) -> str:
        """Calculate overall system health score."""
        search_error_rate = search_stats.get("error_rate", 0)
        datastore_error_rate = datastore_stats.get("error_rate", 0)

        # Simple health scoring
        if search_error_rate > 0.1 or datastore_error_rate > 0.1:
            return "unhealthy"
        elif search_error_rate > 0.05 or datastore_error_rate > 0.05:
            return "degraded"
        else:
            return "healthy"

    async def cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period."""
        cutoff = datetime.now() - timedelta(hours=self.config.retention_hours)

        async with self._lock:
            # Filter search metrics
            self.search_metrics = deque(
                [m for m in self.search_metrics if m.timestamp >= cutoff],
                maxlen=self.config.metrics_buffer_size,
            )

            # Filter datastore metrics
            self.datastore_metrics = deque(
                [m for m in self.datastore_metrics if m.timestamp >= cutoff],
                maxlen=self.config.metrics_buffer_size,
            )

        logger.debug(
            f"Cleaned up metrics older than {self.config.retention_hours} hours"
        )


class PerformanceProfiler:
    """Context manager for profiling RAG operations."""

    def __init__(
        self,
        monitor: PerformanceMonitor,
        operation_type: str,
        operation_name: str,
        metadata: dict[str, Any] | None = None,
    ):
        self.monitor = monitor
        self.operation_type = operation_type
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.success = True
        self.error_message: str | None = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()

        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)

        execution_time_ms = (self.end_time - self.start_time) * 1000

        # Record appropriate metric type
        if self.operation_type == "search":
            metric = SearchMetrics(
                query=self.metadata.get("query", ""),
                search_type=self.metadata.get("search_type", "unknown"),
                execution_time_ms=execution_time_ms,
                results_count=self.metadata.get("results_count", 0),
                timestamp=datetime.now(),
                datastore_type=self.metadata.get("datastore_type", "unknown"),
                success=self.success,
                error_message=self.error_message,
                metadata=self.metadata,
            )
            await self.monitor.record_search_metric(metric)
        else:
            metric = DatastoreMetrics(
                operation=self.operation_name,
                execution_time_ms=execution_time_ms,
                timestamp=datetime.now(),
                datastore_type=self.metadata.get("datastore_type", "unknown"),
                success=self.success,
                document_count=self.metadata.get("document_count"),
                error_message=self.error_message,
            )
            await self.monitor.record_datastore_metric(metric)

        # Re-raise exception if it occurred
        return False


# Global performance monitor instance
_global_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor | None:
    """Get the global performance monitor instance."""
    return _global_monitor


def set_performance_monitor(monitor: PerformanceMonitor) -> None:
    """Set the global performance monitor instance."""
    global _global_monitor
    _global_monitor = monitor


def profile_search(
    query: str,
    search_type: str = "unknown",
    datastore_type: str = "unknown",
    **metadata,
) -> PerformanceProfiler:
    """Create a performance profiler for search operations."""
    monitor = get_performance_monitor()
    if not monitor:
        # Return a no-op profiler if monitoring is disabled
        return NoOpProfiler()

    return PerformanceProfiler(
        monitor=monitor,
        operation_type="search",
        operation_name="search",
        metadata={
            "query": query,
            "search_type": search_type,
            "datastore_type": datastore_type,
            **metadata,
        },
    )


def profile_datastore_operation(
    operation: str, datastore_type: str = "unknown", **metadata
) -> PerformanceProfiler:
    """Create a performance profiler for datastore operations."""
    monitor = get_performance_monitor()
    if not monitor:
        return NoOpProfiler()

    return PerformanceProfiler(
        monitor=monitor,
        operation_type="datastore",
        operation_name=operation,
        metadata={"datastore_type": datastore_type, **metadata},
    )


class NoOpProfiler:
    """No-operation profiler for when monitoring is disabled."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False
