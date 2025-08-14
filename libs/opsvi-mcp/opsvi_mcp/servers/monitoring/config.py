"""
Configuration for Monitoring & Observability MCP Server
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class PrometheusConfig(BaseModel):
    """Prometheus configuration"""
    
    enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    port: int = Field(default=8000, description="Prometheus metrics port")
    endpoint: str = Field(default="/metrics", description="Metrics endpoint path")
    namespace: str = Field(default="opsvi", description="Metrics namespace")
    subsystem: str = Field(default="monitoring", description="Metrics subsystem")
    default_labels: Dict[str, str] = Field(
        default_factory=lambda: {"service": "monitoring_mcp"},
        description="Default labels for all metrics"
    )
    scrape_interval: int = Field(default=15, description="Scrape interval in seconds")
    retention_time: str = Field(default="15d", description="Metrics retention time")


class OpenTelemetryConfig(BaseModel):
    """OpenTelemetry configuration"""
    
    enabled: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    service_name: str = Field(default="monitoring-mcp", description="Service name for traces")
    endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP endpoint for traces"
    )
    protocol: str = Field(default="grpc", description="Protocol for OTLP (grpc/http)")
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers for OTLP requests"
    )
    insecure: bool = Field(default=True, description="Use insecure connection")
    timeout: int = Field(default=30, description="Timeout for OTLP requests in seconds")
    sample_rate: float = Field(default=1.0, description="Trace sampling rate (0.0-1.0)")
    propagators: List[str] = Field(
        default_factory=lambda: ["tracecontext", "baggage"],
        description="Context propagators to use"
    )


class AlertConfig(BaseModel):
    """Alert configuration"""
    
    enabled: bool = Field(default=True, description="Enable alert management")
    webhook_urls: List[str] = Field(
        default_factory=list,
        description="Webhook URLs for alert notifications"
    )
    email_recipients: List[str] = Field(
        default_factory=list,
        description="Email recipients for alerts"
    )
    slack_channels: List[str] = Field(
        default_factory=list,
        description="Slack channels for alerts"
    )
    default_severity: str = Field(default="warning", description="Default alert severity")
    throttle_minutes: int = Field(default=15, description="Alert throttling period in minutes")
    rules_file: str = Field(
        default="alert_rules.yaml",
        description="Path to alert rules configuration"
    )


class LoggingConfig(BaseModel):
    """Logging aggregation configuration"""
    
    enabled: bool = Field(default=True, description="Enable logging aggregation")
    level: str = Field(default="INFO", description="Default log level")
    format: str = Field(
        default="json",
        description="Log format (json/text)"
    )
    output_dir: str = Field(
        default="/tmp/monitoring_logs",
        description="Directory for log files"
    )
    max_file_size: str = Field(default="100MB", description="Maximum log file size")
    max_files: int = Field(default=10, description="Maximum number of log files to keep")
    aggregation_endpoints: List[str] = Field(
        default_factory=list,
        description="Log aggregation endpoints (e.g., Elasticsearch, Loki)"
    )
    structured_logging: bool = Field(
        default=True,
        description="Enable structured logging"
    )
    include_trace_id: bool = Field(
        default=True,
        description="Include trace ID in logs"
    )


class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    
    enabled: bool = Field(default=True, description="Enable dashboards")
    grafana_url: Optional[str] = Field(
        default="http://localhost:3000",
        description="Grafana URL for dashboards"
    )
    grafana_api_key: Optional[str] = Field(
        default=None,
        description="Grafana API key"
    )
    auto_provision: bool = Field(
        default=True,
        description="Auto-provision dashboards"
    )
    dashboard_dir: str = Field(
        default="dashboards",
        description="Directory containing dashboard definitions"
    )
    refresh_interval: str = Field(default="5s", description="Default dashboard refresh interval")


class PerformanceConfig(BaseModel):
    """Performance monitoring configuration"""
    
    enabled: bool = Field(default=True, description="Enable performance monitoring")
    cpu_threshold: float = Field(default=80.0, description="CPU usage threshold percentage")
    memory_threshold: float = Field(default=85.0, description="Memory usage threshold percentage")
    disk_threshold: float = Field(default=90.0, description="Disk usage threshold percentage")
    latency_threshold_ms: int = Field(default=1000, description="Latency threshold in milliseconds")
    profile_enabled: bool = Field(default=False, description="Enable performance profiling")
    profile_dir: str = Field(
        default="/tmp/profiles",
        description="Directory for performance profiles"
    )


class CustomMetricsConfig(BaseModel):
    """Custom metrics configuration"""
    
    enabled: bool = Field(default=True, description="Enable custom metrics")
    definitions_file: str = Field(
        default="custom_metrics.yaml",
        description="Path to custom metrics definitions"
    )
    export_interval: int = Field(default=60, description="Export interval in seconds")
    aggregation_window: int = Field(default=300, description="Aggregation window in seconds")
    percentiles: List[float] = Field(
        default_factory=lambda: [0.5, 0.95, 0.99],
        description="Percentiles to calculate for histogram metrics"
    )


class MonitoringServerConfig(BaseModel):
    """Main configuration for Monitoring & Observability MCP Server"""
    
    server_name: str = Field(
        default="monitoring-mcp",
        description="Server name"
    )
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=5005, description="Server port")
    
    prometheus: PrometheusConfig = Field(
        default_factory=PrometheusConfig,
        description="Prometheus configuration"
    )
    opentelemetry: OpenTelemetryConfig = Field(
        default_factory=OpenTelemetryConfig,
        description="OpenTelemetry configuration"
    )
    alerts: AlertConfig = Field(
        default_factory=AlertConfig,
        description="Alert configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )
    dashboards: DashboardConfig = Field(
        default_factory=DashboardConfig,
        description="Dashboard configuration"
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig,
        description="Performance monitoring configuration"
    )
    custom_metrics: CustomMetricsConfig = Field(
        default_factory=CustomMetricsConfig,
        description="Custom metrics configuration"
    )
    
    data_dir: str = Field(
        default="/tmp/monitoring_data",
        description="Directory for monitoring data"
    )
    config_reload_interval: int = Field(
        default=60,
        description="Configuration reload interval in seconds"
    )
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    
    @classmethod
    def from_env(cls) -> "MonitoringServerConfig":
        """Create configuration from environment variables"""
        config_dict = {}
        
        # Server configuration
        if host := os.getenv("MONITORING_HOST"):
            config_dict["host"] = host
        if port := os.getenv("MONITORING_PORT"):
            config_dict["port"] = int(port)
        
        # Prometheus configuration
        if prom_enabled := os.getenv("PROMETHEUS_ENABLED"):
            config_dict.setdefault("prometheus", {})["enabled"] = prom_enabled.lower() == "true"
        if prom_port := os.getenv("PROMETHEUS_PORT"):
            config_dict.setdefault("prometheus", {})["port"] = int(prom_port)
        
        # OpenTelemetry configuration
        if otel_enabled := os.getenv("OTEL_ENABLED"):
            config_dict.setdefault("opentelemetry", {})["enabled"] = otel_enabled.lower() == "true"
        if otel_endpoint := os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            config_dict.setdefault("opentelemetry", {})["endpoint"] = otel_endpoint
        if otel_service := os.getenv("OTEL_SERVICE_NAME"):
            config_dict.setdefault("opentelemetry", {})["service_name"] = otel_service
        
        # Logging configuration
        if log_level := os.getenv("LOG_LEVEL"):
            config_dict.setdefault("logging", {})["level"] = log_level
        if log_dir := os.getenv("LOG_DIR"):
            config_dict.setdefault("logging", {})["output_dir"] = log_dir
        
        # Data directory
        if data_dir := os.getenv("MONITORING_DATA_DIR"):
            config_dict["data_dir"] = data_dir
        
        return cls(**config_dict)
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.data_dir,
            self.logging.output_dir,
            self.performance.profile_dir,
            os.path.join(self.data_dir, self.dashboards.dashboard_dir),
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)