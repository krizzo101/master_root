"""
Data models for Monitoring & Observability MCP Server
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics"""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AlertState(str, Enum):
    """Alert states"""
    
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"


class TraceStatus(str, Enum):
    """Trace span status"""
    
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class HealthStatus(str, Enum):
    """Health check status"""
    
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MetricPoint(BaseModel):
    """A single metric data point"""
    
    timestamp: datetime = Field(description="Timestamp of the metric")
    value: float = Field(description="Metric value")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels"
    )


class Metric(BaseModel):
    """Metric definition"""
    
    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Metric type")
    description: str = Field(description="Metric description")
    unit: Optional[str] = Field(default=None, description="Metric unit")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Metric labels"
    )
    value: Optional[float] = Field(default=None, description="Current value (for gauges)")
    count: Optional[int] = Field(default=None, description="Count (for counters)")
    sum: Optional[float] = Field(default=None, description="Sum (for histograms/summaries)")
    buckets: Optional[Dict[float, int]] = Field(
        default=None,
        description="Histogram buckets"
    )
    quantiles: Optional[Dict[float, float]] = Field(
        default=None,
        description="Summary quantiles"
    )


class TraceSpan(BaseModel):
    """OpenTelemetry trace span"""
    
    trace_id: str = Field(description="Trace ID")
    span_id: str = Field(description="Span ID")
    parent_span_id: Optional[str] = Field(default=None, description="Parent span ID")
    operation_name: str = Field(description="Operation name")
    service_name: str = Field(description="Service name")
    start_time: datetime = Field(description="Span start time")
    end_time: Optional[datetime] = Field(default=None, description="Span end time")
    duration_ms: Optional[float] = Field(default=None, description="Duration in milliseconds")
    status: TraceStatus = Field(default=TraceStatus.UNSET, description="Span status")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Span attributes"
    )
    events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Span events"
    )
    links: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Span links"
    )


class Alert(BaseModel):
    """Alert definition"""
    
    id: str = Field(description="Alert ID")
    name: str = Field(description="Alert name")
    severity: AlertSeverity = Field(description="Alert severity")
    state: AlertState = Field(default=AlertState.PENDING, description="Alert state")
    message: str = Field(description="Alert message")
    description: Optional[str] = Field(default=None, description="Detailed description")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Alert labels"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Alert annotations"
    )
    fired_at: Optional[datetime] = Field(default=None, description="When alert was fired")
    resolved_at: Optional[datetime] = Field(default=None, description="When alert was resolved")
    last_notification: Optional[datetime] = Field(
        default=None,
        description="Last notification time"
    )
    fingerprint: str = Field(description="Alert fingerprint for deduplication")


class LogEntry(BaseModel):
    """Log entry"""
    
    timestamp: datetime = Field(description="Log timestamp")
    level: str = Field(description="Log level")
    message: str = Field(description="Log message")
    logger: str = Field(description="Logger name")
    trace_id: Optional[str] = Field(default=None, description="Associated trace ID")
    span_id: Optional[str] = Field(default=None, description="Associated span ID")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Log attributes"
    )
    exception: Optional[str] = Field(default=None, description="Exception information")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")


class Dashboard(BaseModel):
    """Dashboard definition"""
    
    id: str = Field(description="Dashboard ID")
    uid: Optional[str] = Field(default=None, description="Dashboard UID")
    title: str = Field(description="Dashboard title")
    description: Optional[str] = Field(default=None, description="Dashboard description")
    tags: List[str] = Field(default_factory=list, description="Dashboard tags")
    panels: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dashboard panels"
    )
    variables: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dashboard variables"
    )
    time_range: Dict[str, str] = Field(
        default_factory=lambda: {"from": "now-6h", "to": "now"},
        description="Default time range"
    )
    refresh_interval: str = Field(default="5s", description="Refresh interval")
    editable: bool = Field(default=True, description="Whether dashboard is editable")
    version: int = Field(default=1, description="Dashboard version")


class PerformanceSnapshot(BaseModel):
    """Performance monitoring snapshot"""
    
    timestamp: datetime = Field(description="Snapshot timestamp")
    cpu_percent: float = Field(description="CPU usage percentage")
    memory_percent: float = Field(description="Memory usage percentage")
    memory_mb: float = Field(description="Memory usage in MB")
    disk_percent: float = Field(description="Disk usage percentage")
    disk_gb: float = Field(description="Disk usage in GB")
    network_sent_mb: float = Field(description="Network sent in MB")
    network_recv_mb: float = Field(description="Network received in MB")
    open_files: int = Field(description="Number of open files")
    thread_count: int = Field(description="Number of threads")
    process_count: int = Field(description="Number of processes")
    latency_p50_ms: Optional[float] = Field(default=None, description="P50 latency in ms")
    latency_p95_ms: Optional[float] = Field(default=None, description="P95 latency in ms")
    latency_p99_ms: Optional[float] = Field(default=None, description="P99 latency in ms")


class HealthCheck(BaseModel):
    """Health check result"""
    
    service: str = Field(description="Service name")
    status: HealthStatus = Field(description="Health status")
    timestamp: datetime = Field(description="Check timestamp")
    checks: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Individual health checks"
    )
    message: Optional[str] = Field(default=None, description="Health check message")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details"
    )


class CollectMetricsRequest(BaseModel):
    """Request to collect metrics"""
    
    metric_names: Optional[List[str]] = Field(
        default=None,
        description="Specific metrics to collect (None for all)"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Label filters"
    )
    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for metrics"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="End time for metrics"
    )


class CreateAlertRequest(BaseModel):
    """Request to create an alert"""
    
    name: str = Field(description="Alert name")
    severity: AlertSeverity = Field(description="Alert severity")
    message: str = Field(description="Alert message")
    description: Optional[str] = Field(default=None, description="Detailed description")
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Alert labels"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict,
        description="Alert annotations"
    )


class StartTraceRequest(BaseModel):
    """Request to start a trace"""
    
    operation_name: str = Field(description="Operation name")
    service_name: Optional[str] = Field(default=None, description="Service name")
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Initial attributes"
    )
    parent_trace_id: Optional[str] = Field(
        default=None,
        description="Parent trace ID for distributed tracing"
    )


class CreateDashboardRequest(BaseModel):
    """Request to create a dashboard"""
    
    title: str = Field(description="Dashboard title")
    description: Optional[str] = Field(default=None, description="Dashboard description")
    tags: List[str] = Field(default_factory=list, description="Dashboard tags")
    panels: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dashboard panels"
    )
    variables: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dashboard variables"
    )
    time_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Default time range"
    )


class LogAggregationRequest(BaseModel):
    """Request for log aggregation"""
    
    query: Optional[str] = Field(default=None, description="Log query")
    level: Optional[str] = Field(default=None, description="Log level filter")
    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for logs"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="End time for logs"
    )
    trace_id: Optional[str] = Field(default=None, description="Filter by trace ID")
    limit: int = Field(default=100, description="Maximum number of logs to return")
    aggregate_by: Optional[str] = Field(
        default=None,
        description="Field to aggregate by"
    )


class CustomMetricDefinition(BaseModel):
    """Custom metric definition"""
    
    name: str = Field(description="Metric name")
    type: MetricType = Field(description="Metric type")
    description: str = Field(description="Metric description")
    unit: Optional[str] = Field(default=None, description="Metric unit")
    labels: List[str] = Field(
        default_factory=list,
        description="Required labels"
    )
    expression: Optional[str] = Field(
        default=None,
        description="Metric calculation expression"
    )
    aggregation: Optional[str] = Field(
        default=None,
        description="Aggregation method"
    )
    buckets: Optional[List[float]] = Field(
        default=None,
        description="Histogram buckets"
    )
    quantiles: Optional[List[float]] = Field(
        default=None,
        description="Summary quantiles"
    )


class MonitoringResponse(BaseModel):
    """Generic monitoring response"""
    
    success: bool = Field(description="Whether operation was successful")
    message: str = Field(description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")