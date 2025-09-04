#!/usr/bin/env python3
"""
Monitoring and alerting for real-time chat log ingestion system.
Provides health checks, metrics collection, and dashboard functionality.
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    open_files: int
    timestamp: str


@dataclass
class IngestionMetrics:
    """Ingestion-specific metrics."""

    files_processed_per_minute: float
    entries_processed_per_minute: float
    average_processing_time_ms: float
    queue_size: int
    queue_capacity: int
    buffer_size: int
    active_watchers: int
    circuit_breaker_status: Dict[str, str]
    timestamp: str


@dataclass
class HealthStatus:
    """Overall health status."""

    is_healthy: bool
    status: str  # 'healthy', 'degraded', 'unhealthy'
    uptime_seconds: float
    last_activity: str
    issues: List[str]
    timestamp: str


class MetricsCollector:
    """Collects system and application metrics."""

    def __init__(self):
        self.start_time = time.time()
        self.metrics_history = []
        self.max_history_size = 1000  # Keep last 1000 metrics points

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Network I/O (if available)
        network_io = {"bytes_sent": 0, "bytes_recv": 0}
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                }
        except Exception:
            pass  # Network stats not available

        # Open files count
        open_files = 0
        try:
            process = psutil.Process()
            open_files = len(process.open_files())
        except Exception:
            pass

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            network_io=network_io,
            open_files=open_files,
            timestamp=datetime.now().isoformat(),
        )

    def collect_ingestion_metrics(self, service) -> IngestionMetrics:
        """Collect ingestion-specific metrics."""
        try:
            pipeline_stats = service.coordinator.pipeline.get_stats()

            # Calculate rates
            uptime_minutes = pipeline_stats.get("uptime_seconds", 0) / 60
            files_per_minute = pipeline_stats.get("files_per_minute", 0)
            entries_per_minute = pipeline_stats.get("entries_per_minute", 0)

            # Get queue and buffer info
            queue_size = service.ingestion_queue.qsize()
            buffer_size = service.coordinator.pipeline.buffer.size

            # Circuit breaker statuses
            circuit_breakers = {}
            if hasattr(service.coordinator.pipeline, "fault_tolerance"):
                ft_status = service.coordinator.pipeline.fault_tolerance.get_status()
                circuit_breakers = {
                    name: status["state"]
                    for name, status in ft_status.get("circuit_breakers", {}).items()
                }

            return IngestionMetrics(
                files_processed_per_minute=files_per_minute,
                entries_processed_per_minute=entries_per_minute,
                average_processing_time_ms=pipeline_stats.get("correlation_time_ms", 0),
                queue_size=queue_size,
                queue_capacity=service.config.queue_size,
                buffer_size=buffer_size,
                active_watchers=len(service.watcher.observers)
                if service.watcher
                else 0,
                circuit_breaker_status=circuit_breakers,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"Error collecting ingestion metrics: {e}")
            return IngestionMetrics(
                files_processed_per_minute=0,
                entries_processed_per_minute=0,
                average_processing_time_ms=0,
                queue_size=0,
                queue_capacity=0,
                buffer_size=0,
                active_watchers=0,
                circuit_breaker_status={},
                timestamp=datetime.now().isoformat(),
            )

    def store_metrics(
        self, system_metrics: SystemMetrics, ingestion_metrics: IngestionMetrics
    ):
        """Store metrics in history."""
        metric_point = {
            "system": asdict(system_metrics),
            "ingestion": asdict(ingestion_metrics),
            "timestamp": datetime.now().isoformat(),
        }

        self.metrics_history.append(metric_point)

        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

    def get_metrics_summary(self, hours: int = 1) -> Dict:
        """Get metrics summary for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_metrics = [
            m
            for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]

        if not recent_metrics:
            return {"error": "No metrics available for specified period"}

        # Calculate averages
        avg_cpu = sum(m["system"]["cpu_percent"] for m in recent_metrics) / len(
            recent_metrics
        )
        avg_memory = sum(m["system"]["memory_percent"] for m in recent_metrics) / len(
            recent_metrics
        )
        avg_files_per_min = sum(
            m["ingestion"]["files_processed_per_minute"] for m in recent_metrics
        ) / len(recent_metrics)
        avg_entries_per_min = sum(
            m["ingestion"]["entries_processed_per_minute"] for m in recent_metrics
        ) / len(recent_metrics)

        return {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "files_per_minute": avg_files_per_min,
                "entries_per_minute": avg_entries_per_min,
            },
            "latest": recent_metrics[-1] if recent_metrics else None,
        }


class HealthChecker:
    """Performs health checks on the ingestion system."""

    def __init__(self):
        self.last_health_check = None
        self.health_history = []
        self.max_history_size = 100

    def check_health(self, service) -> HealthStatus:
        """Perform comprehensive health check."""
        issues = []
        timestamp = datetime.now().isoformat()

        # Check if service is running
        if not service.running:
            issues.append("Service is not running")

        # Check queue size
        queue_size = service.ingestion_queue.qsize()
        queue_capacity = service.config.queue_size

        if queue_size > queue_capacity * 0.9:
            issues.append(f"Queue nearly full: {queue_size}/{queue_capacity}")
        elif queue_size > queue_capacity * 0.7:
            issues.append(f"Queue size high: {queue_size}/{queue_capacity}")

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                issues.append(f"Moderate CPU usage: {cpu_percent:.1f}%")

            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 75:
                issues.append(f"Moderate memory usage: {memory_percent:.1f}%")

        except Exception as e:
            issues.append(f"Could not check system resources: {e}")

        # Check watchers
        if service.watcher:
            active_watchers = len(service.watcher.observers)
            if active_watchers == 0:
                issues.append("No active file watchers")
        else:
            issues.append("File watcher not initialized")

        # Check recent activity
        try:
            pipeline_stats = service.coordinator.pipeline.get_stats()
            uptime = pipeline_stats.get("uptime_seconds", 0)
            files_processed = pipeline_stats.get("files_processed", 0)

            if uptime > 300 and files_processed == 0:  # 5 minutes with no files
                issues.append("No files processed in the last 5 minutes")

        except Exception as e:
            issues.append(f"Could not check activity: {e}")

        # Determine overall health status
        if not issues:
            status = "healthy"
            is_healthy = True
        elif any("High" in issue or "nearly full" in issue for issue in issues):
            status = "unhealthy"
            is_healthy = False
        else:
            status = "degraded"
            is_healthy = True  # Still functional but with warnings

        uptime_seconds = time.time() - service.start_time if service.start_time else 0
        last_activity = service.stats.get("last_health_check", timestamp)

        health_status = HealthStatus(
            is_healthy=is_healthy,
            status=status,
            uptime_seconds=uptime_seconds,
            last_activity=last_activity,
            issues=issues,
            timestamp=timestamp,
        )

        self.last_health_check = health_status
        self._store_health_status(health_status)

        return health_status

    def _store_health_status(self, health_status: HealthStatus):
        """Store health status in history."""
        self.health_history.append(asdict(health_status))

        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size :]

    def get_health_trends(self, hours: int = 24) -> Dict:
        """Analyze health trends over time."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_health = [
            h
            for h in self.health_history
            if datetime.fromisoformat(h["timestamp"]) > cutoff_time
        ]

        if not recent_health:
            return {"error": "No health data available for specified period"}

        # Calculate trends
        healthy_count = sum(1 for h in recent_health if h["is_healthy"])
        degraded_count = sum(1 for h in recent_health if h["status"] == "degraded")
        unhealthy_count = sum(1 for h in recent_health if not h["is_healthy"])

        # Common issues
        all_issues = []
        for h in recent_health:
            all_issues.extend(h["issues"])

        issue_counts = {}
        for issue in all_issues:
            # Normalize issue messages
            normalized = issue.split(":")[0]  # Remove specific values
            issue_counts[normalized] = issue_counts.get(normalized, 0) + 1

        return {
            "period_hours": hours,
            "total_checks": len(recent_health),
            "health_distribution": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
            },
            "health_percentage": (healthy_count / len(recent_health)) * 100,
            "common_issues": sorted(
                issue_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "latest_status": recent_health[-1] if recent_health else None,
        }


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        self.alert_rules = {
            "queue_full": {
                "threshold": 0.9,
                "severity": "critical",
                "message": "Ingestion queue is nearly full",
            },
            "high_cpu": {
                "threshold": 85,
                "severity": "warning",
                "message": "High CPU usage detected",
            },
            "high_memory": {
                "threshold": 85,
                "severity": "warning",
                "message": "High memory usage detected",
            },
            "no_activity": {
                "threshold": 600,  # 10 minutes
                "severity": "warning",
                "message": "No processing activity detected",
            },
            "circuit_breaker_open": {
                "threshold": 1,
                "severity": "critical",
                "message": "Circuit breaker is open",
            },
        }
        self.active_alerts = {}
        self.alert_history = []

    def check_alerts(self, metrics: Dict, health_status: HealthStatus) -> List[Dict]:
        """Check for alert conditions."""
        current_alerts = []
        timestamp = datetime.now().isoformat()

        # Queue full alert
        if "ingestion" in metrics:
            queue_size = metrics["ingestion"].get("queue_size", 0)
            queue_capacity = metrics["ingestion"].get("queue_capacity", 1)
            queue_ratio = queue_size / queue_capacity if queue_capacity > 0 else 0

            if queue_ratio >= self.alert_rules["queue_full"]["threshold"]:
                alert = self._create_alert(
                    "queue_full",
                    f"Queue usage: {queue_size}/{queue_capacity} ({queue_ratio:.1%})",
                    timestamp,
                )
                current_alerts.append(alert)

        # System resource alerts
        if "system" in metrics:
            cpu_percent = metrics["system"].get("cpu_percent", 0)
            memory_percent = metrics["system"].get("memory_percent", 0)

            if cpu_percent >= self.alert_rules["high_cpu"]["threshold"]:
                alert = self._create_alert(
                    "high_cpu", f"CPU usage: {cpu_percent:.1f}%", timestamp
                )
                current_alerts.append(alert)

            if memory_percent >= self.alert_rules["high_memory"]["threshold"]:
                alert = self._create_alert(
                    "high_memory", f"Memory usage: {memory_percent:.1f}%", timestamp
                )
                current_alerts.append(alert)

        # Circuit breaker alerts
        if "ingestion" in metrics:
            cb_status = metrics["ingestion"].get("circuit_breaker_status", {})
            for cb_name, state in cb_status.items():
                if state == "open":
                    alert = self._create_alert(
                        "circuit_breaker_open",
                        f"Circuit breaker '{cb_name}' is open",
                        timestamp,
                    )
                    current_alerts.append(alert)

        # Update active alerts
        self._update_active_alerts(current_alerts)

        return current_alerts

    def _create_alert(self, rule_name: str, details: str, timestamp: str) -> Dict:
        """Create alert dictionary."""
        rule = self.alert_rules[rule_name]
        return {
            "rule": rule_name,
            "severity": rule["severity"],
            "message": rule["message"],
            "details": details,
            "timestamp": timestamp,
            "id": f"{rule_name}_{timestamp}",
        }

    def _update_active_alerts(self, current_alerts: List[Dict]):
        """Update active alerts tracking."""
        # Add new alerts
        for alert in current_alerts:
            alert_key = alert["rule"]
            if alert_key not in self.active_alerts:
                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)
                logger.warning(f"ALERT: {alert['message']} - {alert['details']}")

        # Remove resolved alerts
        current_rules = {alert["rule"] for alert in current_alerts}
        resolved_rules = set(self.active_alerts.keys()) - current_rules

        for rule in resolved_rules:
            resolved_alert = self.active_alerts.pop(rule)
            logger.info(f"ALERT RESOLVED: {resolved_alert['message']}")

        # Trim alert history
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    def get_alert_summary(self) -> Dict:
        """Get alert summary."""
        return {
            "active_alerts": list(self.active_alerts.values()),
            "total_active": len(self.active_alerts),
            "critical_count": len(
                [a for a in self.active_alerts.values() if a["severity"] == "critical"]
            ),
            "warning_count": len(
                [a for a in self.active_alerts.values() if a["severity"] == "warning"]
            ),
            "recent_history": self.alert_history[-10:],  # Last 10 alerts
        }


class MonitoringDashboard:
    """Web dashboard for monitoring the ingestion system."""

    def __init__(self, service):
        self.service = service
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.running = False

    async def start_monitoring(self):
        """Start monitoring loop."""
        logger.info("Starting monitoring dashboard")
        self.running = True

        while self.running:
            try:
                # Collect metrics
                system_metrics = self.metrics_collector.collect_system_metrics()
                ingestion_metrics = self.metrics_collector.collect_ingestion_metrics(
                    self.service
                )

                # Store metrics
                self.metrics_collector.store_metrics(system_metrics, ingestion_metrics)

                # Check health
                health_status = self.health_checker.check_health(self.service)

                # Check alerts
                metrics_dict = {
                    "system": asdict(system_metrics),
                    "ingestion": asdict(ingestion_metrics),
                }
                alerts = self.alert_manager.check_alerts(metrics_dict, health_status)

                # Log summary periodically
                await self._log_monitoring_summary(health_status, alerts)

                await asyncio.sleep(60)  # Monitor every minute

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)

    def stop_monitoring(self):
        """Stop monitoring."""
        logger.info("Stopping monitoring dashboard")
        self.running = False

    async def _log_monitoring_summary(
        self, health_status: HealthStatus, alerts: List[Dict]
    ):
        """Log monitoring summary."""
        # Log every 5 minutes
        if int(time.time()) % 300 == 0:
            summary = self.get_dashboard_data()
            logger.info(
                f"Monitoring Summary - "
                f"Status: {health_status.status}, "
                f"Active Alerts: {len(alerts)}, "
                f"Files/min: {summary['ingestion_metrics']['files_processed_per_minute']:.1f}, "
                f"Queue: {summary['ingestion_metrics']['queue_size']}"
            )

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data."""
        # Get latest metrics
        latest_metrics = (
            self.metrics_collector.metrics_history[-1]
            if self.metrics_collector.metrics_history
            else {}
        )

        # Get health status
        health_status = self.health_checker.last_health_check

        # Get alerts
        alert_summary = self.alert_manager.get_alert_summary()

        # Get trends
        metrics_summary = self.metrics_collector.get_metrics_summary(hours=1)
        health_trends = self.health_checker.get_health_trends(hours=24)

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": latest_metrics.get("system", {}),
            "ingestion_metrics": latest_metrics.get("ingestion", {}),
            "health_status": asdict(health_status) if health_status else {},
            "alerts": alert_summary,
            "trends": {"metrics": metrics_summary, "health": health_trends},
            "service_info": {
                "uptime_seconds": time.time() - self.service.start_time
                if self.service.start_time
                else 0,
                "running": self.service.running,
                "config": {
                    "queue_size": self.service.config.queue_size,
                    "watch_enabled": self.service.config.watch_enabled,
                    "batch_size": self.service.config.batch_size,
                },
            },
        }

    def export_dashboard_data(self, file_path: str):
        """Export dashboard data to JSON file."""
        data = self.get_dashboard_data()

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Dashboard data exported to {file_path}")


# Utility functions for external monitoring systems
def create_prometheus_metrics(dashboard: MonitoringDashboard) -> str:
    """Create Prometheus-compatible metrics."""
    data = dashboard.get_dashboard_data()

    metrics = []

    # System metrics
    if "system_metrics" in data:
        sys_metrics = data["system_metrics"]
        metrics.append(
            f"chat_ingestion_cpu_percent {sys_metrics.get('cpu_percent', 0)}"
        )
        metrics.append(
            f"chat_ingestion_memory_percent {sys_metrics.get('memory_percent', 0)}"
        )
        metrics.append(
            f"chat_ingestion_disk_percent {sys_metrics.get('disk_usage_percent', 0)}"
        )
        metrics.append(f"chat_ingestion_open_files {sys_metrics.get('open_files', 0)}")

    # Ingestion metrics
    if "ingestion_metrics" in data:
        ing_metrics = data["ingestion_metrics"]
        metrics.append(
            f"chat_ingestion_files_per_minute {ing_metrics.get('files_processed_per_minute', 0)}"
        )
        metrics.append(
            f"chat_ingestion_entries_per_minute {ing_metrics.get('entries_processed_per_minute', 0)}"
        )
        metrics.append(f"chat_ingestion_queue_size {ing_metrics.get('queue_size', 0)}")
        metrics.append(
            f"chat_ingestion_buffer_size {ing_metrics.get('buffer_size', 0)}"
        )
        metrics.append(
            f"chat_ingestion_active_watchers {ing_metrics.get('active_watchers', 0)}"
        )

    # Health status
    health_status = data.get("health_status", {})
    is_healthy = 1 if health_status.get("is_healthy", False) else 0
    metrics.append(f"chat_ingestion_healthy {is_healthy}")

    # Alerts
    alerts = data.get("alerts", {})
    metrics.append(f"chat_ingestion_active_alerts {alerts.get('total_active', 0)}")
    metrics.append(f"chat_ingestion_critical_alerts {alerts.get('critical_count', 0)}")

    return "\n".join(metrics)


if __name__ == "__main__":
    # Test monitoring functionality
    logging.basicConfig(level=logging.INFO)

    # Create mock service for testing
    class MockService:
        def __init__(self):
            self.running = True
            self.start_time = time.time()
            self.stats = {}
            self.ingestion_queue = type("Queue", (), {"qsize": lambda: 10})()
            self.config = type("Config", (), {"queue_size": 100})()
            self.watcher = type("Watcher", (), {"observers": [1, 2, 3]})()
            self.coordinator = type(
                "Coordinator",
                (),
                {
                    "pipeline": type(
                        "Pipeline",
                        (),
                        {
                            "get_stats": lambda: {
                                "uptime_seconds": 300,
                                "files_per_minute": 5.2,
                                "entries_per_minute": 150.0,
                                "files_processed": 26,
                                "correlation_time_ms": 45.0,
                            },
                            "buffer": type("Buffer", (), {"size": 5})(),
                        },
                    )()
                },
            )()

    mock_service = MockService()

    # Test metrics collection
    collector = MetricsCollector()
    system_metrics = collector.collect_system_metrics()
    ingestion_metrics = collector.collect_ingestion_metrics(mock_service)

    print("System Metrics:")
    print(json.dumps(asdict(system_metrics), indent=2))

    print("\nIngestion Metrics:")
    print(json.dumps(asdict(ingestion_metrics), indent=2))

    # Test health check
    health_checker = HealthChecker()
    health_status = health_checker.check_health(mock_service)

    print("\nHealth Status:")
    print(json.dumps(asdict(health_status), indent=2))

    # Test dashboard
    dashboard = MonitoringDashboard(mock_service)
    dashboard_data = dashboard.get_dashboard_data()

    print("\nDashboard Data Summary:")
    print(f"Service Running: {dashboard_data['service_info']['running']}")
    print(f"Health Status: {dashboard_data['health_status'].get('status', 'unknown')}")
    print(
        f"Files/min: {dashboard_data['ingestion_metrics'].get('files_processed_per_minute', 0):.1f}"
    )
