#!/usr/bin/env python3
"""
Performance Monitoring System for Auto Rules Generation

This module provides comprehensive performance monitoring and optimization
capabilities for the auto rules generation system.
"""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional

import psutil

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""

    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    file_count: int
    rule_count: int
    cache_hits: int
    cache_misses: int
    error_count: int
    timestamp: datetime


@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerts."""

    max_execution_time: float = 30.0  # seconds
    max_memory_usage: float = 512.0  # MB
    max_cpu_usage: float = 80.0  # percent
    max_file_count: int = 1000  # files
    min_cache_hit_rate: float = 0.7  # 70%


class PerformanceMonitor:
    """Comprehensive performance monitor for auto rules generation."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the performance monitor."""
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.output_dir = output_dir or Path("performance_logs")
        self.output_dir.mkdir(exist_ok=True)

        self.metrics_history: List[PerformanceMetrics] = []
        self.thresholds = PerformanceThresholds()
        self.monitoring_active = False
        self.cache_stats = {"hits": 0, "misses": 0}

        # Performance tracking
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.start_cpu: Optional[float] = None

        self.logger.log_info("Performance monitor initialized")

    @contextmanager
    def monitor_performance(self, operation_name: str):
        """Context manager for monitoring performance of operations."""
        self.start_monitoring(operation_name)
        try:
            yield
        finally:
            self.stop_monitoring(operation_name)

    def start_monitoring(self, operation_name: str):
        """Start monitoring performance."""
        self.monitoring_active = True
        self.start_time = time.time()

        process = psutil.Process(os.getpid())
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = process.cpu_percent()

        self.logger.log_info(f"Started performance monitoring for: {operation_name}")

    def stop_monitoring(
        self, operation_name: str, file_count: int = 0, rule_count: int = 0
    ):
        """Stop monitoring and record metrics."""
        if not self.monitoring_active or self.start_time is None:
            return

        end_time = time.time()
        execution_time = end_time - self.start_time

        process = psutil.Process(os.getpid())
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()

        memory_usage = end_memory - (self.start_memory or 0)
        cpu_usage = (end_cpu + (self.start_cpu or 0)) / 2

        metrics = PerformanceMetrics(
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            file_count=file_count,
            rule_count=rule_count,
            cache_hits=self.cache_stats["hits"],
            cache_misses=self.cache_stats["misses"],
            error_count=0,  # Will be updated by error tracking
            timestamp=datetime.now(),
        )

        self.metrics_history.append(metrics)
        self._check_thresholds(metrics, operation_name)
        self._save_metrics(metrics, operation_name)

        self.monitoring_active = False
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None

        self.logger.log_info(f"Stopped performance monitoring for: {operation_name}")

    def _check_thresholds(self, metrics: PerformanceMetrics, operation_name: str):
        """Check if performance metrics exceed thresholds."""
        alerts = []

        if metrics.execution_time > self.thresholds.max_execution_time:
            alerts.append(
                f"Execution time {metrics.execution_time:.2f}s exceeds threshold {self.thresholds.max_execution_time}s"
            )

        if metrics.memory_usage_mb > self.thresholds.max_memory_usage:
            alerts.append(
                f"Memory usage {metrics.memory_usage_mb:.2f}MB exceeds threshold {self.thresholds.max_memory_usage}MB"
            )

        if metrics.cpu_usage_percent > self.thresholds.max_cpu_usage:
            alerts.append(
                f"CPU usage {metrics.cpu_usage_percent:.1f}% exceeds threshold {self.thresholds.max_cpu_usage}%"
            )

        if metrics.file_count > self.thresholds.max_file_count:
            alerts.append(
                f"File count {metrics.file_count} exceeds threshold {self.thresholds.max_file_count}"
            )

        total_cache_requests = metrics.cache_hits + metrics.cache_misses
        if total_cache_requests > 0:
            cache_hit_rate = metrics.cache_hits / total_cache_requests
            if cache_hit_rate < self.thresholds.min_cache_hit_rate:
                alerts.append(
                    f"Cache hit rate {cache_hit_rate:.2f} below threshold {self.thresholds.min_cache_hit_rate}"
                )

        if alerts:
            self.logger.log_warning(
                f"Performance alerts for {operation_name}: {'; '.join(alerts)}"
            )

    def _save_metrics(self, metrics: PerformanceMetrics, operation_name: str):
        """Save metrics to file."""
        timestamp_str = metrics.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"performance_{operation_name}_{timestamp_str}.json"
        filepath = self.output_dir / filename

        metrics_data = asdict(metrics)
        metrics_data["operation_name"] = operation_name

        with open(filepath, "w") as f:
            json.dump(metrics_data, f, indent=2, default=str)

        self.logger.log_info(f"Performance metrics saved to: {filepath}")

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_stats["hits"] += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_stats["misses"] += 1

    def record_error(self):
        """Record an error occurrence."""
        if self.monitoring_active and self.metrics_history:
            self.metrics_history[-1].error_count += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.metrics_history:
            return {"message": "No performance data available"}

        recent_metrics = self.metrics_history[-10:]  # Last 10 operations

        summary = {
            "total_operations": len(self.metrics_history),
            "recent_operations": len(recent_metrics),
            "average_execution_time": sum(m.execution_time for m in recent_metrics)
            / len(recent_metrics),
            "average_memory_usage": sum(m.memory_usage_mb for m in recent_metrics)
            / len(recent_metrics),
            "average_cpu_usage": sum(m.cpu_usage_percent for m in recent_metrics)
            / len(recent_metrics),
            "total_cache_hits": sum(m.cache_hits for m in self.metrics_history),
            "total_cache_misses": sum(m.cache_misses for m in self.metrics_history),
            "total_errors": sum(m.error_count for m in self.metrics_history),
        }

        # Calculate cache hit rate
        total_cache_requests = (
            summary["total_cache_hits"] + summary["total_cache_misses"]
        )
        if total_cache_requests > 0:
            summary["cache_hit_rate"] = (
                summary["total_cache_hits"] / total_cache_requests
            )
        else:
            summary["cache_hit_rate"] = 0.0

        return summary

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        summary = self.get_performance_summary()

        if "message" in summary:
            return f"Performance Report:\n{summary['message']}"

        report = f"""
📊 PERFORMANCE REPORT
{'='*50}

📈 SUMMARY:
- Total Operations: {summary['total_operations']}
- Recent Operations: {summary['recent_operations']}
- Average Execution Time: {summary['average_execution_time']:.2f}s
- Average Memory Usage: {summary['average_memory_usage']:.2f}MB
- Average CPU Usage: {summary['average_cpu_usage']:.1f}%
- Cache Hit Rate: {summary['cache_hit_rate']:.2%}
- Total Errors: {summary['total_errors']}

{'='*50}

🎯 THRESHOLDS:
- Max Execution Time: {self.thresholds.max_execution_time}s
- Max Memory Usage: {self.thresholds.max_memory_usage}MB
- Max CPU Usage: {self.thresholds.max_cpu_usage}%
- Max File Count: {self.thresholds.max_file_count}
- Min Cache Hit Rate: {self.thresholds.min_cache_hit_rate:.0%}

{'='*50}

📋 RECENT OPERATIONS:
"""

        recent_metrics = self.metrics_history[-5:]  # Last 5 operations
        for i, metrics in enumerate(recent_metrics, 1):
            report += f"""
Operation {i}:
- Execution Time: {metrics.execution_time:.2f}s
- Memory Usage: {metrics.memory_usage_mb:.2f}MB
- CPU Usage: {metrics.cpu_usage_percent:.1f}%
- File Count: {metrics.file_count}
- Rule Count: {metrics.rule_count}
- Cache Hits: {metrics.cache_hits}
- Cache Misses: {metrics.cache_misses}
- Errors: {metrics.error_count}
- Timestamp: {metrics.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report

    def optimize_performance(self) -> List[str]:
        """Analyze performance and suggest optimizations."""
        suggestions = []
        summary = self.get_performance_summary()

        if "message" in summary:
            return ["No performance data available for optimization suggestions"]

        # Check execution time
        if summary["average_execution_time"] > self.thresholds.max_execution_time * 0.8:
            suggestions.append(
                "Consider implementing caching for frequently accessed data"
            )
            suggestions.append("Optimize file scanning algorithms")
            suggestions.append(
                "Implement parallel processing for independent operations"
            )

        # Check memory usage
        if summary["average_memory_usage"] > self.thresholds.max_memory_usage * 0.8:
            suggestions.append("Implement memory-efficient data structures")
            suggestions.append("Add garbage collection calls at strategic points")
            suggestions.append(
                "Consider streaming large files instead of loading entirely"
            )

        # Check cache performance
        if summary["cache_hit_rate"] < self.thresholds.min_cache_hit_rate:
            suggestions.append("Expand cache coverage for frequently accessed patterns")
            suggestions.append("Implement smarter cache invalidation strategies")
            suggestions.append("Consider pre-computing common rule patterns")

        # Check error rate
        if summary["total_errors"] > 0:
            suggestions.append("Improve error handling and recovery mechanisms")
            suggestions.append("Add more robust input validation")
            suggestions.append("Implement retry mechanisms for transient failures")

        return suggestions

    def clear_history(self):
        """Clear performance history."""
        self.metrics_history.clear()
        self.logger.log_info("Performance history cleared")

    def export_metrics(self, filepath: Path):
        """Export all metrics to a file."""
        metrics_data = {
            "export_timestamp": datetime.now().isoformat(),
            "thresholds": asdict(self.thresholds),
            "metrics": [asdict(m) for m in self.metrics_history],
        }

        with open(filepath, "w") as f:
            json.dump(metrics_data, f, indent=2, default=str)

        self.logger.log_info(f"Performance metrics exported to: {filepath}")


class PerformanceDecorator:
    """Decorator for automatically monitoring function performance."""

    def __init__(
        self, monitor: PerformanceMonitor, operation_name: Optional[str] = None
    ):
        """Initialize the decorator."""
        self.monitor = monitor
        self.operation_name = operation_name

    def __call__(self, func: Callable):
        """Decorate a function with performance monitoring."""

        def wrapper(*args, **kwargs):
            operation_name = self.operation_name or func.__name__

            with self.monitor.monitor_performance(operation_name):
                try:
                    result = func(*args, **kwargs)

                    # Try to extract file and rule counts from result
                    file_count = 0
                    rule_count = 0

                    if hasattr(result, "generated_rules"):
                        rule_count = (
                            len(result.generated_rules) if result.generated_rules else 0
                        )

                    if (
                        hasattr(result, "codebase_metadata")
                        and result.codebase_metadata
                    ):
                        file_count = result.codebase_metadata.file_count

                    self.monitor.stop_monitoring(operation_name, file_count, rule_count)
                    return result

                except Exception:
                    self.monitor.record_error()
                    self.monitor.stop_monitoring(operation_name)
                    raise

        return wrapper


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global global_monitor
    if global_monitor is None:
        global_monitor = PerformanceMonitor()
    return global_monitor


def monitor_performance(operation_name: Optional[str] = None):
    """Decorator for monitoring function performance."""
    monitor = get_performance_monitor()
    return PerformanceDecorator(monitor, operation_name)


if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()

    # Monitor a function
    @monitor_performance("test_operation")
    def test_function():
        time.sleep(1)  # Simulate work
        return {"result": "success"}

    # Run the function
    result = test_function()

    # Generate report
    report = monitor.generate_performance_report()
    print(report)

    # Get optimization suggestions
    suggestions = monitor.optimize_performance()
    print("\nOptimization Suggestions:")
    for suggestion in suggestions:
        print(f"- {suggestion}")
