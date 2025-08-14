"""Metrics collection middleware for opsvi-core."""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Awaitable
from datetime import datetime

from opsvi_foundation.middleware import Middleware, Request, Response

logger = logging.getLogger(__name__)


@dataclass
class MetricsSummary:
    """Summary of collected metrics."""
    
    total_requests: int = 0
    total_errors: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    paths: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    methods: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class MetricsMiddleware(Middleware):
    """Middleware for collecting request metrics."""
    
    def __init__(
        self,
        name: str = "MetricsMiddleware",
        bucket_duration: int = 60,  # seconds
        max_buckets: int = 60,  # Keep 1 hour of data
        collect_paths: bool = True,
        collect_status_codes: bool = True
    ):
        """Initialize metrics middleware.
        
        Args:
            name: Name of the middleware
            bucket_duration: Duration of each metrics bucket (seconds)
            max_buckets: Maximum number of buckets to keep
            collect_paths: Whether to collect path metrics
            collect_status_codes: Whether to collect status code metrics
        """
        super().__init__(name)
        self.bucket_duration = bucket_duration
        self.max_buckets = max_buckets
        self.collect_paths = collect_paths
        self.collect_status_codes = collect_status_codes
        
        self._buckets: List[Dict[str, Any]] = []
        self._current_bucket: Optional[Dict[str, Any]] = None
        self._start_time = time.time()
    
    def _get_current_bucket(self) -> Dict[str, Any]:
        """Get or create current metrics bucket."""
        current_time = time.time()
        bucket_index = int(current_time / self.bucket_duration)
        
        if not self._current_bucket or self._current_bucket["index"] != bucket_index:
            # Create new bucket
            self._current_bucket = {
                "index": bucket_index,
                "start_time": bucket_index * self.bucket_duration,
                "requests": 0,
                "errors": 0,
                "total_duration": 0.0,
                "durations": [],
                "status_codes": defaultdict(int),
                "paths": defaultdict(int),
                "methods": defaultdict(int),
            }
            
            # Add to buckets list
            self._buckets.append(self._current_bucket)
            
            # Remove old buckets
            if len(self._buckets) > self.max_buckets:
                self._buckets = self._buckets[-self.max_buckets:]
        
        return self._current_bucket
    
    async def process(
        self,
        request: Request,
        next_handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()
        bucket = self._get_current_bucket()
        
        try:
            response = await next_handler(request)
            
            # Record metrics
            duration = time.time() - start_time
            bucket["requests"] += 1
            bucket["total_duration"] += duration
            bucket["durations"].append(duration)
            
            if self.collect_status_codes:
                bucket["status_codes"][response.status] += 1
            
            if self.collect_paths:
                bucket["paths"][request.path] += 1
            
            bucket["methods"][request.method] += 1
            
            # Update global metrics
            self._metrics["requests_processed"] += 1
            self._metrics["total_time"] += duration
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            bucket["errors"] += 1
            bucket["total_duration"] += duration
            bucket["durations"].append(duration)
            
            if self.collect_paths:
                bucket["paths"][request.path] += 1
            
            bucket["methods"][request.method] += 1
            
            # Update global metrics
            self._metrics["errors"] += 1
            self._metrics["total_time"] += duration
            
            raise
    
    def get_summary(self, last_n_buckets: Optional[int] = None) -> MetricsSummary:
        """Get metrics summary.
        
        Args:
            last_n_buckets: Number of recent buckets to include (None for all)
            
        Returns:
            Metrics summary
        """
        buckets = self._buckets
        if last_n_buckets:
            buckets = self._buckets[-last_n_buckets:]
        
        if not buckets:
            return MetricsSummary()
        
        summary = MetricsSummary()
        all_durations = []
        
        for bucket in buckets:
            summary.total_requests += bucket["requests"]
            summary.total_errors += bucket["errors"]
            summary.total_duration += bucket["total_duration"]
            all_durations.extend(bucket["durations"])
            
            for status, count in bucket["status_codes"].items():
                summary.status_codes[status] += count
            
            for path, count in bucket["paths"].items():
                summary.paths[path] += count
            
            for method, count in bucket["methods"].items():
                summary.methods[method] += count
        
        if all_durations:
            summary.avg_duration = summary.total_duration / len(all_durations)
            summary.min_duration = min(all_durations)
            summary.max_duration = max(all_durations)
        
        # Calculate rates
        time_span = len(buckets) * self.bucket_duration
        if time_span > 0:
            summary.requests_per_second = summary.total_requests / time_span
        
        if summary.total_requests > 0:
            summary.error_rate = summary.total_errors / summary.total_requests
        
        return summary
    
    def get_percentiles(
        self,
        percentiles: List[float] = [0.5, 0.9, 0.95, 0.99]
    ) -> Dict[float, float]:
        """Get response time percentiles.
        
        Args:
            percentiles: List of percentiles to calculate (0-1)
            
        Returns:
            Dictionary of percentile: duration
        """
        all_durations = []
        for bucket in self._buckets:
            all_durations.extend(bucket["durations"])
        
        if not all_durations:
            return {p: 0.0 for p in percentiles}
        
        all_durations.sort()
        result = {}
        
        for p in percentiles:
            index = int(len(all_durations) * p)
            if index >= len(all_durations):
                index = len(all_durations) - 1
            result[p] = all_durations[index]
        
        return result


class PrometheusMetricsMiddleware(MetricsMiddleware):
    """Middleware for Prometheus-compatible metrics."""
    
    def __init__(
        self,
        name: str = "PrometheusMetricsMiddleware",
        namespace: str = "opsvi",
        subsystem: str = "http",
        **kwargs
    ):
        """Initialize Prometheus metrics middleware.
        
        Args:
            name: Name of the middleware
            namespace: Prometheus namespace
            subsystem: Prometheus subsystem
            **kwargs: Additional arguments for MetricsMiddleware
        """
        super().__init__(name, **kwargs)
        self.namespace = namespace
        self.subsystem = subsystem
    
    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        lines = []
        summary = self.get_summary()
        percentiles = self.get_percentiles()
        
        # Request total
        metric_name = f"{self.namespace}_{self.subsystem}_requests_total"
        lines.append(f"# HELP {metric_name} Total number of HTTP requests")
        lines.append(f"# TYPE {metric_name} counter")
        lines.append(f"{metric_name} {summary.total_requests}")
        
        # Error total
        metric_name = f"{self.namespace}_{self.subsystem}_errors_total"
        lines.append(f"# HELP {metric_name} Total number of HTTP errors")
        lines.append(f"# TYPE {metric_name} counter")
        lines.append(f"{metric_name} {summary.total_errors}")
        
        # Request duration
        metric_name = f"{self.namespace}_{self.subsystem}_request_duration_seconds"
        lines.append(f"# HELP {metric_name} HTTP request duration in seconds")
        lines.append(f"# TYPE {metric_name} summary")
        
        for percentile, value in percentiles.items():
            quantile = percentile
            lines.append(f'{metric_name}{{quantile="{quantile}"}} {value}')
        
        lines.append(f"{metric_name}_sum {summary.total_duration}")
        lines.append(f"{metric_name}_count {summary.total_requests}")
        
        # Status codes
        metric_name = f"{self.namespace}_{self.subsystem}_requests_by_status"
        lines.append(f"# HELP {metric_name} HTTP requests by status code")
        lines.append(f"# TYPE {metric_name} counter")
        
        for status, count in summary.status_codes.items():
            lines.append(f'{metric_name}{{status="{status}"}} {count}')
        
        # Methods
        metric_name = f"{self.namespace}_{self.subsystem}_requests_by_method"
        lines.append(f"# HELP {metric_name} HTTP requests by method")
        lines.append(f"# TYPE {metric_name} counter")
        
        for method, count in summary.methods.items():
            lines.append(f'{metric_name}{{method="{method}"}} {count}')
        
        return "\n".join(lines)


__all__ = [
    "MetricsSummary",
    "MetricsMiddleware",
    "PrometheusMetricsMiddleware",
]