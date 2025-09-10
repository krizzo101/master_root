#!/usr/bin/env python3
"""
Metrics collection and monitoring for IDE Context Bridge.

Provides performance metrics, health checks, and observability features.
"""

import asyncio
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point."""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics container."""

    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    p95_time: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))

    def update(self, duration: float):
        """Update statistics with new duration."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.avg_time = self.total_time / self.count

        self.recent_times.append(duration)

        # Calculate P95
        if len(self.recent_times) >= 5:
            sorted_times = sorted(self.recent_times)
            p95_index = int(0.95 * len(sorted_times))
            self.p95_time = sorted_times[min(p95_index, len(sorted_times) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "total_time": self.total_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0.0,
            "max_time": self.max_time,
            "avg_time": self.avg_time,
            "p95_time": self.p95_time,
        }


class Counter:
    """Thread-safe counter metric."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.value = 0
        self._lock = threading.Lock()

    def increment(self, amount: int = 1):
        """Increment counter."""
        with self._lock:
            self.value += amount

    def get_value(self) -> int:
        """Get current value."""
        with self._lock:
            return self.value

    def reset(self):
        """Reset counter to zero."""
        with self._lock:
            self.value = 0


class Gauge:
    """Thread-safe gauge metric."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.value = 0.0
        self._lock = threading.Lock()

    def set(self, value: float):
        """Set gauge value."""
        with self._lock:
            self.value = value

    def add(self, amount: float):
        """Add to gauge value."""
        with self._lock:
            self.value += amount

    def get_value(self) -> float:
        """Get current value."""
        with self._lock:
            return self.value


class Histogram:
    """Thread-safe histogram metric."""

    def __init__(self, name: str, description: str = "", buckets: List[float] = None):
        self.name = name
        self.description = description
        self.buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ]
        self.bucket_counts = [0] * len(self.buckets)
        self.count = 0
        self.sum = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float):
        """Record observation."""
        with self._lock:
            self.count += 1
            self.sum += value

            # Update bucket counts
            for i, bucket in enumerate(self.buckets):
                if value <= bucket:
                    self.bucket_counts[i] += 1

    def get_value(self) -> Dict[str, Any]:
        """Get histogram data."""
        with self._lock:
            return {
                "count": self.count,
                "sum": self.sum,
                "buckets": dict(zip(self.buckets, self.bucket_counts)),
            }


class MetricsCollector:
    """Main metrics collection and reporting system."""

    def __init__(self, enable_detailed_metrics: bool = False):
        self.enable_detailed_metrics = enable_detailed_metrics

        # Metric storage
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.performance_stats: Dict[str, PerformanceStats] = defaultdict(
            PerformanceStats
        )

        # Time series data
        self.time_series: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.max_points_per_metric = 1000

        # Health status
        self.health_checks: Dict[str, Callable] = {}
        self.health_status = "healthy"
        self.last_health_check = datetime.now()

        # Initialize default metrics
        self._initialize_default_metrics()

        # Start background tasks
        self._start_background_tasks()

    def _initialize_default_metrics(self):
        """Initialize default metrics."""
        # Request metrics
        self.counters["http_requests_total"] = Counter(
            "http_requests_total", "Total HTTP requests"
        )
        self.counters["websocket_connections_total"] = Counter(
            "websocket_connections_total", "Total WebSocket connections"
        )
        self.counters["context_updates_total"] = Counter(
            "context_updates_total", "Total context updates"
        )
        self.counters["suggestions_generated_total"] = Counter(
            "suggestions_generated_total", "Total suggestions generated"
        )
        self.counters["searches_performed_total"] = Counter(
            "searches_performed_total", "Total searches performed"
        )

        # Current state gauges
        self.gauges["active_websocket_connections"] = Gauge(
            "active_websocket_connections", "Current active WebSocket connections"
        )
        self.gauges["active_sessions"] = Gauge(
            "active_sessions", "Current active sessions"
        )
        self.gauges["cache_size"] = Gauge("cache_size", "Current cache size")

        # Performance histograms
        self.histograms["request_duration_seconds"] = Histogram(
            "request_duration_seconds", "HTTP request duration in seconds"
        )
        self.histograms["suggestion_generation_duration_seconds"] = Histogram(
            "suggestion_generation_duration_seconds",
            "Suggestion generation duration in seconds",
        )
        self.histograms["search_duration_seconds"] = Histogram(
            "search_duration_seconds", "Search duration in seconds"
        )
        self.histograms["context_update_duration_seconds"] = Histogram(
            "context_update_duration_seconds", "Context update duration in seconds"
        )

    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        # Cleanup task
        cleanup_thread = threading.Thread(target=self._cleanup_old_metrics, daemon=True)
        cleanup_thread.start()

    def _cleanup_old_metrics(self):
        """Clean up old metric data."""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=1)

                # Clean time series data
                for metric_name in list(self.time_series.keys()):
                    points = self.time_series[metric_name]
                    self.time_series[metric_name] = [
                        point for point in points if point.timestamp > cutoff_time
                    ]

                    # Remove empty metrics
                    if not self.time_series[metric_name]:
                        del self.time_series[metric_name]

                time.sleep(300)  # Run every 5 minutes

            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                time.sleep(60)

    # Counter methods
    def increment_counter(
        self, name: str, amount: int = 1, labels: Dict[str, str] = None
    ):
        """Increment a counter metric."""
        if name not in self.counters:
            self.counters[name] = Counter(name)

        self.counters[name].increment(amount)

        # Record time series if detailed metrics enabled
        if self.enable_detailed_metrics:
            self._record_time_series(name, amount, labels or {})

    def get_counter_value(self, name: str) -> int:
        """Get counter value."""
        return self.counters.get(name, Counter("")).get_value()

    # Gauge methods
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name)

        self.gauges[name].set(value)

        # Record time series if detailed metrics enabled
        if self.enable_detailed_metrics:
            self._record_time_series(name, value, labels or {})

    def add_to_gauge(self, name: str, amount: float):
        """Add to gauge value."""
        if name not in self.gauges:
            self.gauges[name] = Gauge(name)

        self.gauges[name].add(amount)

    def get_gauge_value(self, name: str) -> float:
        """Get gauge value."""
        return self.gauges.get(name, Gauge("")).get_value()

    # Histogram methods
    def observe_histogram(self, name: str, value: float):
        """Record histogram observation."""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name)

        self.histograms[name].observe(value)

    def get_histogram_value(self, name: str) -> Dict[str, Any]:
        """Get histogram data."""
        return self.histograms.get(name, Histogram("")).get_value()

    # Performance tracking
    def record_performance(
        self, operation: str, duration: float, labels: Dict[str, str] = None
    ):
        """Record performance metrics."""
        self.performance_stats[operation].update(duration)

        # Also record in histogram
        histogram_name = f"{operation}_duration_seconds"
        self.observe_histogram(histogram_name, duration)

    def get_performance_stats(self, operation: str) -> Dict[str, Any]:
        """Get performance statistics."""
        return self.performance_stats.get(operation, PerformanceStats()).to_dict()

    # Request tracking
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.increment_counter("http_requests_total")
        self.observe_histogram("request_duration_seconds", duration)

        # Record by status code
        if status_code >= 400:
            self.increment_counter("http_requests_errors_total")

        # Record performance
        self.record_performance(f"http_{method.lower()}", duration)

    def record_websocket_connection(self, connected: bool = True):
        """Record WebSocket connection event."""
        if connected:
            self.increment_counter("websocket_connections_total")
            self.add_to_gauge("active_websocket_connections", 1)
        else:
            self.add_to_gauge("active_websocket_connections", -1)

    def record_context_update(self, duration: float):
        """Record context update metrics."""
        self.increment_counter("context_updates_total")
        self.record_performance("context_update", duration)

    def record_suggestion_generation(self, count: int, duration: float):
        """Record suggestion generation metrics."""
        self.increment_counter("suggestions_generated_total", count)
        self.record_performance("suggestion_generation", duration)

    def record_search(self, result_count: int, duration: float):
        """Record search metrics."""
        self.increment_counter("searches_performed_total")
        self.record_performance("search", duration)
        self.set_gauge("last_search_results", result_count)

    # Time series recording
    def _record_time_series(
        self, metric_name: str, value: float, labels: Dict[str, str]
    ):
        """Record time series data point."""
        point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels)

        self.time_series[metric_name].append(point)

        # Limit number of points
        if len(self.time_series[metric_name]) > self.max_points_per_metric:
            self.time_series[metric_name].pop(0)

    def get_time_series(
        self, metric_name: str, minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get time series data for a metric."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        points = [
            {
                "timestamp": point.timestamp.isoformat(),
                "value": point.value,
                "labels": point.labels,
            }
            for point in self.time_series.get(metric_name, [])
            if point.timestamp > cutoff_time
        ]

        return points

    # Health checks
    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.health_checks[name] = check_func

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_healthy = True

        for name, check_func in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()

                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                }

                if not result:
                    overall_healthy = False

            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                overall_healthy = False

        self.health_status = "healthy" if overall_healthy else "unhealthy"
        self.last_health_check = datetime.now()

        return {
            "overall_status": self.health_status,
            "last_check": self.last_health_check.isoformat(),
            "checks": results,
        }

    # Export methods
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            "counters": {
                name: counter.get_value() for name, counter in self.counters.items()
            },
            "gauges": {name: gauge.get_value() for name, gauge in self.gauges.items()},
            "histograms": {
                name: histogram.get_value()
                for name, histogram in self.histograms.items()
            },
            "performance": {
                name: stats.to_dict() for name, stats in self.performance_stats.items()
            },
            "health_status": self.health_status,
            "last_health_check": self.last_health_check.isoformat(),
        }

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counters
        for name, counter in self.counters.items():
            lines.append(f"# HELP {name} {counter.description}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter.get_value()}")

        # Gauges
        for name, gauge in self.gauges.items():
            lines.append(f"# HELP {name} {gauge.description}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {gauge.get_value()}")

        # Histograms
        for name, histogram in self.histograms.items():
            data = histogram.get_value()
            lines.append(f"# HELP {name} {histogram.description}")
            lines.append(f"# TYPE {name} histogram")

            for bucket, count in data["buckets"].items():
                lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')

            lines.append(f"{name}_count {data['count']}")
            lines.append(f"{name}_sum {data['sum']}")

        return "\n".join(lines) + "\n"

    def get_json_metrics(self) -> str:
        """Export metrics as JSON."""
        return json.dumps(self.get_all_metrics(), indent=2, default=str)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_requests": self.get_counter_value("http_requests_total"),
            "websocket_connections": self.get_counter_value(
                "websocket_connections_total"
            ),
            "active_connections": self.get_gauge_value("active_websocket_connections"),
            "context_updates": self.get_counter_value("context_updates_total"),
            "suggestions_generated": self.get_counter_value(
                "suggestions_generated_total"
            ),
            "searches_performed": self.get_counter_value("searches_performed_total"),
            "health_status": self.health_status,
            "uptime_seconds": time.time() - self._start_time
            if hasattr(self, "_start_time")
            else 0,
        }

    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        for counter in self.counters.values():
            counter.reset()

        for gauge in self.gauges.values():
            gauge.set(0)

        self.performance_stats.clear()
        self.time_series.clear()


# Context manager for timing operations
class TimedOperation:
    """Context manager for timing operations."""

    def __init__(self, metrics_collector: MetricsCollector, operation_name: str):
        self.metrics_collector = metrics_collector
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics_collector.record_performance(self.operation_name, duration)


def timed_operation(metrics_collector: MetricsCollector, operation_name: str):
    """Decorator for timing operations."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    metrics_collector.record_performance(operation_name, duration)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    metrics_collector.record_performance(operation_name, duration)

            return sync_wrapper

    return decorator


if __name__ == "__main__":
    # Test metrics functionality
    print("Testing IDE Context Bridge Metrics...")

    metrics = MetricsCollector(enable_detailed_metrics=True)

    # Test counters
    metrics.increment_counter("test_counter", 5)
    metrics.increment_counter("test_counter", 3)
    print(f"Test counter value: {metrics.get_counter_value('test_counter')}")

    # Test gauges
    metrics.set_gauge("test_gauge", 42.5)
    metrics.add_to_gauge("test_gauge", 7.5)
    print(f"Test gauge value: {metrics.get_gauge_value('test_gauge')}")

    # Test histograms
    for value in [0.1, 0.5, 1.2, 0.3, 0.8]:
        metrics.observe_histogram("test_histogram", value)
    print(f"Test histogram: {metrics.get_histogram_value('test_histogram')}")

    # Test performance tracking
    with TimedOperation(metrics, "test_operation"):
        time.sleep(0.1)

    print(f"Performance stats: {metrics.get_performance_stats('test_operation')}")

    # Test Prometheus export
    print("\nPrometheus format sample:")
    prometheus_output = metrics.get_prometheus_metrics()
    print(
        prometheus_output[:500] + "..."
        if len(prometheus_output) > 500
        else prometheus_output
    )

    print("\nMetrics test completed!")
