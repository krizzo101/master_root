"""
Prometheus metrics exporter for monitoring system performance.
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading

from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    CollectorRegistry, generate_latest,
    start_http_server, CONTENT_TYPE_LATEST
)
from prometheus_client.core import REGISTRY

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"      # Monotonically increasing
    GAUGE = "gauge"          # Can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"      # Similar to histogram with quantiles


@dataclass
class Metric:
    """Metric definition."""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    unit: Optional[str] = None
    
    def __hash__(self):
        return hash(self.name)


class MetricsExporter:
    """Exports metrics in Prometheus format."""
    
    def __init__(self, 
                 namespace: str = "autonomous_agent",
                 port: int = 9090):
        self.namespace = namespace
        self.port = port
        self.registry = CollectorRegistry()
        
        # Metric storage
        self.metrics: Dict[str, Any] = {}
        self.metric_definitions: Dict[str, Metric] = {}
        
        # Time series storage for aggregation
        self.time_series: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Initialize default metrics
        self._init_default_metrics()
        
        # Start metrics server
        self.server_thread = None
        self.lock = threading.Lock()
    
    def _init_default_metrics(self):
        """Initialize default system metrics."""
        # System metrics
        self.register_metric(Metric(
            name="cpu_usage_percent",
            type=MetricType.GAUGE,
            description="CPU usage percentage",
            unit="percent"
        ))
        
        self.register_metric(Metric(
            name="memory_usage_percent",
            type=MetricType.GAUGE,
            description="Memory usage percentage",
            unit="percent"
        ))
        
        self.register_metric(Metric(
            name="memory_usage_bytes",
            type=MetricType.GAUGE,
            description="Memory usage in bytes",
            unit="bytes"
        ))
        
        self.register_metric(Metric(
            name="disk_usage_percent",
            type=MetricType.GAUGE,
            description="Disk usage percentage",
            unit="percent"
        ))
        
        # Agent metrics
        self.register_metric(Metric(
            name="agent_tasks_total",
            type=MetricType.COUNTER,
            description="Total number of tasks processed",
            labels=["status", "agent_type"]
        ))
        
        self.register_metric(Metric(
            name="agent_task_duration_seconds",
            type=MetricType.HISTOGRAM,
            description="Task execution duration",
            labels=["agent_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
        ))
        
        self.register_metric(Metric(
            name="agent_errors_total",
            type=MetricType.COUNTER,
            description="Total number of errors",
            labels=["error_type", "agent_type"]
        ))
        
        # API metrics
        self.register_metric(Metric(
            name="api_requests_total",
            type=MetricType.COUNTER,
            description="Total API requests",
            labels=["method", "endpoint", "status"]
        ))
        
        self.register_metric(Metric(
            name="api_request_duration_seconds",
            type=MetricType.HISTOGRAM,
            description="API request duration",
            labels=["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        ))
        
        # Learning metrics
        self.register_metric(Metric(
            name="learning_patterns_discovered",
            type=MetricType.COUNTER,
            description="Number of patterns discovered",
            labels=["pattern_type"]
        ))
        
        self.register_metric(Metric(
            name="learning_confidence_score",
            type=MetricType.GAUGE,
            description="Current learning confidence score",
            unit="ratio"
        ))
        
        # Resource metrics
        self.register_metric(Metric(
            name="resource_limit_exceeded",
            type=MetricType.COUNTER,
            description="Number of times resource limits were exceeded",
            labels=["resource_type"]
        ))
    
    def register_metric(self, metric: Metric):
        """Register a new metric."""
        with self.lock:
            if metric.name in self.metric_definitions:
                logger.warning(f"Metric {metric.name} already registered")
                return
            
            self.metric_definitions[metric.name] = metric
            
            # Create Prometheus metric
            metric_name = f"{self.namespace}_{metric.name}"
            
            if metric.type == MetricType.COUNTER:
                self.metrics[metric.name] = Counter(
                    metric_name,
                    metric.description,
                    metric.labels,
                    registry=self.registry
                )
            elif metric.type == MetricType.GAUGE:
                self.metrics[metric.name] = Gauge(
                    metric_name,
                    metric.description,
                    metric.labels,
                    registry=self.registry
                )
            elif metric.type == MetricType.HISTOGRAM:
                self.metrics[metric.name] = Histogram(
                    metric_name,
                    metric.description,
                    metric.labels,
                    buckets=metric.buckets or Histogram.DEFAULT_BUCKETS,
                    registry=self.registry
                )
            elif metric.type == MetricType.SUMMARY:
                self.metrics[metric.name] = Summary(
                    metric_name,
                    metric.description,
                    metric.labels,
                    registry=self.registry
                )
            
            logger.debug(f"Registered metric: {metric.name}")
    
    def increment_counter(self, 
                         name: str,
                         value: float = 1.0,
                         labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self.lock:
            if name not in self.metrics:
                logger.warning(f"Metric {name} not found")
                return
            
            metric = self.metrics[name]
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
            
            # Store in time series
            self.time_series[name].append({
                'timestamp': time.time(),
                'value': value,
                'labels': labels
            })
    
    def set_gauge(self,
                 name: str,
                 value: float,
                 labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self.lock:
            if name not in self.metrics:
                logger.warning(f"Metric {name} not found")
                return
            
            metric = self.metrics[name]
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
            
            # Store in time series
            self.time_series[name].append({
                'timestamp': time.time(),
                'value': value,
                'labels': labels
            })
    
    def observe_histogram(self,
                         name: str,
                         value: float,
                         labels: Optional[Dict[str, str]] = None):
        """Observe a value for histogram metric."""
        with self.lock:
            if name not in self.metrics:
                logger.warning(f"Metric {name} not found")
                return
            
            metric = self.metrics[name]
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
            
            # Store in time series
            self.time_series[name].append({
                'timestamp': time.time(),
                'value': value,
                'labels': labels
            })
    
    def observe_summary(self,
                       name: str,
                       value: float,
                       labels: Optional[Dict[str, str]] = None):
        """Observe a value for summary metric."""
        with self.lock:
            if name not in self.metrics:
                logger.warning(f"Metric {name} not found")
                return
            
            metric = self.metrics[name]
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
            
            # Store in time series
            self.time_series[name].append({
                'timestamp': time.time(),
                'value': value,
                'labels': labels
            })
    
    async def collect_system_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("cpu_usage_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("memory_usage_percent", memory.percent)
            self.set_gauge("memory_usage_bytes", memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.set_gauge("disk_usage_percent", disk.percent)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def start_collection_loop(self, interval: float = 10.0):
        """Start automatic metric collection loop."""
        while True:
            await self.collect_system_metrics()
            await asyncio.sleep(interval)
    
    def start_server(self):
        """Start Prometheus metrics server."""
        try:
            # Use the registry we created
            from prometheus_client import make_wsgi_app
            from wsgiref.simple_server import make_server
            
            app = make_wsgi_app(self.registry)
            httpd = make_server('', self.port, app)
            
            def serve():
                logger.info(f"Metrics server started on port {self.port}")
                httpd.serve_forever()
            
            self.server_thread = threading.Thread(target=serve, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format."""
        return generate_latest(self.registry).decode('utf-8')
    
    async def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        metrics_data = {}
        
        # Collect system metrics first
        await self.collect_system_metrics()
        
        with self.lock:
            for name, definition in self.metric_definitions.items():
                if name in self.time_series and self.time_series[name]:
                    # Get latest value
                    latest = self.time_series[name][-1]
                    metrics_data[name] = latest['value']
        
        return metrics_data
    
    def get_time_series(self, 
                       metric_name: str,
                       duration: Optional[timedelta] = None) -> List[Dict[str, Any]]:
        """Get time series data for a metric."""
        with self.lock:
            if metric_name not in self.time_series:
                return []
            
            series = list(self.time_series[metric_name])
            
            if duration:
                cutoff = time.time() - duration.total_seconds()
                series = [s for s in series if s['timestamp'] >= cutoff]
            
            return series
    
    def get_aggregated_metrics(self,
                              metric_name: str,
                              aggregation: str = "avg",
                              duration: Optional[timedelta] = None) -> Optional[float]:
        """Get aggregated metric value."""
        series = self.get_time_series(metric_name, duration)
        
        if not series:
            return None
        
        values = [s['value'] for s in series]
        
        if aggregation == "avg":
            return sum(values) / len(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "count":
            return len(values)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
    
    def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in specified format."""
        if format == "prometheus":
            return self.get_metrics_text()
        elif format == "json":
            import json
            metrics = asyncio.run(self.get_all_metrics())
            return json.dumps(metrics, indent=2)
        else:
            raise ValueError(f"Unknown format: {format}")


# Singleton instance
_metrics_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter() -> MetricsExporter:
    """Get global metrics exporter instance."""
    global _metrics_exporter
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()
        _metrics_exporter.start_server()
    return _metrics_exporter


# Example usage
if __name__ == "__main__":
    async def example():
        # Create exporter
        exporter = MetricsExporter()
        exporter.start_server()
        
        # Simulate some metrics
        for i in range(10):
            # Task completed
            exporter.increment_counter(
                "agent_tasks_total",
                labels={"status": "success", "agent_type": "research"}
            )
            
            # Task duration
            exporter.observe_histogram(
                "agent_task_duration_seconds",
                value=2.5 + i * 0.1,
                labels={"agent_type": "research"}
            )
            
            # API request
            exporter.increment_counter(
                "api_requests_total",
                labels={"method": "POST", "endpoint": "/api/task", "status": "200"}
            )
            
            await asyncio.sleep(1)
        
        # Get metrics
        print("Current metrics:")
        print(await exporter.get_all_metrics())
        
        # Get time series
        print("\nTime series for agent_tasks_total:")
        print(exporter.get_time_series("agent_tasks_total"))
        
        # Get aggregated metrics
        print("\nAverage task duration:")
        print(exporter.get_aggregated_metrics("agent_task_duration_seconds", "avg"))
        
        # Export in Prometheus format
        print("\nPrometheus format:")
        print(exporter.export_metrics("prometheus")[:500])  # First 500 chars
    
    asyncio.run(example())