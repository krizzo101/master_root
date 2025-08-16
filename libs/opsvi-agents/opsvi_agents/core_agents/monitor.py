"""MonitorAgent - System monitoring."""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics
from collections import deque
import structlog

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult


logger = structlog.get_logger()


class MetricType(Enum):
    """Types of metrics to monitor."""
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    RESOURCE = "resource"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Monitored metric."""
    name: str
    type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "unit": self.unit,
            "tags": self.tags
        }


@dataclass
class Alert:
    """Monitoring alert."""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    metric: Optional[Metric] = None
    threshold: Optional[float] = None
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "resolved": self.resolved
        }


@dataclass
class HealthCheck:
    """System health check."""
    component: str
    healthy: bool
    message: str = ""
    checks: Dict[str, bool] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "healthy": self.healthy,
            "message": self.message,
            "checks": self.checks,
            "timestamp": self.timestamp
        }


@dataclass
class MonitoringReport:
    """Monitoring report."""
    id: str
    period_start: float
    period_end: float
    metrics: List[Metric] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    health_checks: List[HealthCheck] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "duration": self.period_end - self.period_start,
            "metrics_count": len(self.metrics),
            "alerts_count": len(self.alerts),
            "health_checks": [h.to_dict() for h in self.health_checks],
            "summary": self.summary
        }


class MonitorAgent(BaseAgent):
    """Monitors system health and performance."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize monitor agent."""
        super().__init__(config or AgentConfig(
            name="MonitorAgent",
            description="System monitoring",
            capabilities=["monitor", "alert", "health_check", "track", "report"],
            max_retries=1,
            timeout=30
        ))
        self.metrics: Dict[str, deque] = {}  # Store recent metrics
        self.alerts: Dict[str, Alert] = {}
        self.thresholds: Dict[str, float] = {}
        self.health_status: Dict[str, HealthCheck] = {}
        self.reports: Dict[str, MonitoringReport] = {}
        self._alert_counter = 0
        self._report_counter = 0
        self._initialize_defaults()
    
    def initialize(self) -> bool:
        """Initialize the monitor agent."""
        logger.info("monitor_agent_initialized", agent=self.config.name)
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring task."""
        action = task.get("action", "monitor")
        
        if action == "monitor":
            return self._monitor_system(task)
        elif action == "track":
            return self._track_metric(task)
        elif action == "alert":
            return self._check_alerts(task)
        elif action == "health_check":
            return self._perform_health_check(task)
        elif action == "set_threshold":
            return self._set_threshold(task)
        elif action == "get_metrics":
            return self._get_metrics(task)
        elif action == "generate_report":
            return self._generate_report(task)
        elif action == "clear_alerts":
            return self._clear_alerts(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def monitor(self,
               target: str,
               metrics: List[MetricType],
               duration: int = 60) -> MonitoringReport:
        """Monitor a target."""
        result = self.execute({
            "action": "monitor",
            "target": target,
            "metrics": [m.value for m in metrics],
            "duration": duration
        })
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        return result["report"]
    
    def _initialize_defaults(self):
        """Initialize default thresholds."""
        self.thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "latency": 1000,  # 1000ms
            "cpu_usage": 80,  # 80%
            "memory_usage": 90,  # 90%
            "availability": 99.9  # 99.9%
        }
    
    def _monitor_system(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor system metrics."""
        target = task.get("target", "system")
        metrics_list = task.get("metrics", ["performance"])
        duration = task.get("duration", 60)
        
        start_time = time.time()
        collected_metrics = []
        triggered_alerts = []
        
        # Collect metrics
        for metric_name in metrics_list:
            metric_type = MetricType[metric_name.upper()] if metric_name.upper() in MetricType.__members__ else MetricType.CUSTOM
            
            # Simulate metric collection
            value = self._collect_metric(target, metric_type)
            
            metric = Metric(
                name=f"{target}_{metric_name}",
                type=metric_type,
                value=value
            )
            
            collected_metrics.append(metric)
            
            # Store metric
            if metric.name not in self.metrics:
                self.metrics[metric.name] = deque(maxlen=1000)
            self.metrics[metric.name].append(metric)
            
            # Check for alerts
            alert = self._check_threshold(metric)
            if alert:
                triggered_alerts.append(alert)
        
        # Perform health check
        health = self._check_health(target)
        
        # Create report
        self._report_counter += 1
        report = MonitoringReport(
            id=f"report_{self._report_counter}",
            period_start=start_time,
            period_end=time.time(),
            metrics=collected_metrics,
            alerts=triggered_alerts,
            health_checks=[health] if health else []
        )
        
        # Generate summary
        report.summary = self._generate_summary(collected_metrics, triggered_alerts)
        
        # Store report
        self.reports[report.id] = report
        
        logger.info("monitoring_completed",
                   target=target,
                   metrics_count=len(collected_metrics),
                   alerts_count=len(triggered_alerts))
        
        return {
            "report": report,
            "report_id": report.id,
            "summary": report.summary
        }
    
    def _track_metric(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Track a specific metric."""
        name = task.get("name", "")
        value = task.get("value")
        metric_type = task.get("type", "custom")
        tags = task.get("tags", {})
        
        if not name or value is None:
            return {"error": "Name and value are required"}
        
        type_enum = MetricType[metric_type.upper()] if metric_type.upper() in MetricType.__members__ else MetricType.CUSTOM
        
        metric = Metric(
            name=name,
            type=type_enum,
            value=float(value),
            tags=tags
        )
        
        # Store metric
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=1000)
        self.metrics[name].append(metric)
        
        # Check for alerts
        alert = self._check_threshold(metric)
        
        return {
            "metric": metric.to_dict(),
            "alert": alert.to_dict() if alert else None
        }
    
    def _check_alerts(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check for alerts."""
        active_alerts = []
        resolved_alerts = []
        
        # Check all metrics against thresholds
        for metric_name, metric_history in self.metrics.items():
            if metric_history:
                latest = metric_history[-1]
                alert = self._check_threshold(latest)
                
                if alert:
                    active_alerts.append(alert)
                    self.alerts[alert.id] = alert
                else:
                    # Check if previous alert can be resolved
                    for alert_id, existing_alert in self.alerts.items():
                        if existing_alert.metric and existing_alert.metric.name == metric_name and not existing_alert.resolved:
                            existing_alert.resolved = True
                            resolved_alerts.append(existing_alert)
        
        return {
            "active_alerts": [a.to_dict() for a in active_alerts],
            "resolved_alerts": [a.to_dict() for a in resolved_alerts],
            "total_active": len(active_alerts)
        }
    
    def _perform_health_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform health check."""
        component = task.get("component", "system")
        checks = task.get("checks", ["connectivity", "resources", "performance"])
        
        health_results = {}
        all_healthy = True
        
        for check in checks:
            # Simulate health checks
            if check == "connectivity":
                health_results[check] = True
            elif check == "resources":
                health_results[check] = self._check_resources()
            elif check == "performance":
                health_results[check] = self._check_performance()
            else:
                health_results[check] = True
            
            if not health_results[check]:
                all_healthy = False
        
        health = HealthCheck(
            component=component,
            healthy=all_healthy,
            message="All checks passed" if all_healthy else "Some checks failed",
            checks=health_results
        )
        
        # Store health status
        self.health_status[component] = health
        
        return {
            "health_check": health.to_dict(),
            "healthy": all_healthy
        }
    
    def _set_threshold(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Set alert threshold."""
        metric_name = task.get("metric")
        threshold = task.get("threshold")
        
        if not metric_name or threshold is None:
            return {"error": "Metric name and threshold are required"}
        
        self.thresholds[metric_name] = float(threshold)
        
        return {
            "metric": metric_name,
            "threshold": threshold,
            "set": True
        }
    
    def _get_metrics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get metrics data."""
        metric_name = task.get("metric")
        limit = task.get("limit", 100)
        
        if metric_name and metric_name in self.metrics:
            metrics = list(self.metrics[metric_name])[-limit:]
            
            # Calculate statistics
            if metrics:
                values = [m.value for m in metrics]
                stats = {
                    "count": len(values),
                    "mean": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0
                }
            else:
                stats = {}
            
            return {
                "metrics": [m.to_dict() for m in metrics],
                "statistics": stats
            }
        else:
            # Return all metric names
            return {
                "available_metrics": list(self.metrics.keys()),
                "count": len(self.metrics)
            }
    
    def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monitoring report."""
        period = task.get("period", 3600)  # Default 1 hour
        include_alerts = task.get("include_alerts", True)
        include_health = task.get("include_health", True)
        
        end_time = time.time()
        start_time = end_time - period
        
        # Collect metrics from period
        period_metrics = []
        for metric_history in self.metrics.values():
            for metric in metric_history:
                if start_time <= metric.timestamp <= end_time:
                    period_metrics.append(metric)
        
        # Collect alerts from period
        period_alerts = []
        if include_alerts:
            for alert in self.alerts.values():
                if start_time <= alert.timestamp <= end_time:
                    period_alerts.append(alert)
        
        # Get latest health checks
        health_checks = []
        if include_health:
            health_checks = list(self.health_status.values())
        
        # Create report
        self._report_counter += 1
        report = MonitoringReport(
            id=f"report_{self._report_counter}",
            period_start=start_time,
            period_end=end_time,
            metrics=period_metrics,
            alerts=period_alerts,
            health_checks=health_checks
        )
        
        # Generate summary
        report.summary = self._generate_summary(period_metrics, period_alerts)
        
        # Store report
        self.reports[report.id] = report
        
        return {
            "report": report.to_dict(),
            "report_id": report.id
        }
    
    def _clear_alerts(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Clear resolved alerts."""
        clear_all = task.get("clear_all", False)
        alert_ids = task.get("alert_ids", [])
        
        cleared = []
        
        if clear_all:
            for alert in self.alerts.values():
                if alert.resolved:
                    cleared.append(alert.id)
            
            for alert_id in cleared:
                del self.alerts[alert_id]
        else:
            for alert_id in alert_ids:
                if alert_id in self.alerts:
                    del self.alerts[alert_id]
                    cleared.append(alert_id)
        
        return {
            "cleared": cleared,
            "remaining": len(self.alerts)
        }
    
    def _collect_metric(self, target: str, metric_type: MetricType) -> float:
        """Collect metric value (simulated)."""
        import random
        
        if metric_type == MetricType.PERFORMANCE:
            return random.uniform(70, 100)
        elif metric_type == MetricType.ERROR_RATE:
            return random.uniform(0, 0.1)
        elif metric_type == MetricType.THROUGHPUT:
            return random.uniform(100, 1000)
        elif metric_type == MetricType.LATENCY:
            return random.uniform(10, 2000)
        elif metric_type == MetricType.AVAILABILITY:
            return random.uniform(99, 100)
        elif metric_type == MetricType.RESOURCE:
            return random.uniform(20, 95)
        else:
            return random.uniform(0, 100)
    
    def _check_threshold(self, metric: Metric) -> Optional[Alert]:
        """Check if metric exceeds threshold."""
        threshold_key = metric.name.split("_")[-1]  # Get last part of name
        
        if threshold_key in self.thresholds:
            threshold = self.thresholds[threshold_key]
            
            # Determine if threshold is exceeded
            exceeded = False
            if metric.type in [MetricType.ERROR_RATE, MetricType.LATENCY, MetricType.RESOURCE]:
                exceeded = metric.value > threshold
            elif metric.type == MetricType.AVAILABILITY:
                exceeded = metric.value < threshold
            
            if exceeded:
                self._alert_counter += 1
                severity = self._determine_severity(metric, threshold)
                
                return Alert(
                    id=f"alert_{self._alert_counter}",
                    name=f"{metric.name}_threshold",
                    severity=severity,
                    message=f"{metric.name} value {metric.value} exceeds threshold {threshold}",
                    metric=metric,
                    threshold=threshold
                )
        
        return None
    
    def _determine_severity(self, metric: Metric, threshold: float) -> AlertSeverity:
        """Determine alert severity."""
        deviation = abs(metric.value - threshold) / threshold if threshold != 0 else 1
        
        if deviation > 0.5:
            return AlertSeverity.CRITICAL
        elif deviation > 0.25:
            return AlertSeverity.ERROR
        elif deviation > 0.1:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def _check_health(self, target: str) -> HealthCheck:
        """Check system health."""
        checks = {
            "connectivity": True,
            "resources": self._check_resources(),
            "performance": self._check_performance()
        }
        
        return HealthCheck(
            component=target,
            healthy=all(checks.values()),
            message="System healthy" if all(checks.values()) else "Issues detected",
            checks=checks
        )
    
    def _check_resources(self) -> bool:
        """Check resource availability."""
        # Simulate resource check
        if "resource" in self.metrics:
            recent = list(self.metrics["resource"])[-10:]
            if recent:
                avg = statistics.mean([m.value for m in recent])
                return avg < 80  # Less than 80% usage
        return True
    
    def _check_performance(self) -> bool:
        """Check performance metrics."""
        # Simulate performance check
        if "performance" in self.metrics:
            recent = list(self.metrics["performance"])[-10:]
            if recent:
                avg = statistics.mean([m.value for m in recent])
                return avg > 70  # Greater than 70% performance
        return True
    
    def _generate_summary(self, metrics: List[Metric], alerts: List[Alert]) -> Dict[str, Any]:
        """Generate monitoring summary."""
        summary = {
            "total_metrics": len(metrics),
            "total_alerts": len(alerts),
            "alert_breakdown": {}
        }
        
        # Count alerts by severity
        for severity in AlertSeverity:
            count = sum(1 for a in alerts if a.severity == severity)
            if count > 0:
                summary["alert_breakdown"][severity.value] = count
        
        # Calculate metric averages
        if metrics:
            metric_values = {}
            for metric in metrics:
                if metric.type.value not in metric_values:
                    metric_values[metric.type.value] = []
                metric_values[metric.type.value].append(metric.value)
            
            summary["metric_averages"] = {
                k: statistics.mean(v) for k, v in metric_values.items()
            }
        
        return summary
    
    def shutdown(self) -> bool:
        """Shutdown the monitor agent."""
        logger.info("monitor_agent_shutdown",
                   metrics_tracked=len(self.metrics),
                   active_alerts=len(self.alerts),
                   reports_generated=len(self.reports))
        self.metrics.clear()
        self.alerts.clear()
        self.health_status.clear()
        self.reports.clear()
        return True