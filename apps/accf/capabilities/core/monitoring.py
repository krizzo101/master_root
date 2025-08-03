"""
CloudWatch Metrics and Monitoring System

Provides comprehensive monitoring and observability for the ACCF Research Agent.
"""

import boto3
import time
import logging
import psutil
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Metric data structure for CloudWatch"""

    metric_name: str
    value: float
    unit: str
    dimensions: Dict[str, str]
    timestamp: datetime


class CloudWatchMetrics:
    """CloudWatch metrics collection and reporting"""

    def __init__(
        self, namespace: str = "ACCF/ResearchAgent", region: str = "us-east-1"
    ):
        self.namespace = namespace
        self.region = region
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.metrics_buffer: List[MetricData] = []
        self.buffer_size = 20  # Batch size for CloudWatch API calls

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """Put a single metric to CloudWatch"""
        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Namespace": self.namespace,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self.cloudwatch.put_metric_data(
                Namespace=self.namespace, MetricData=[metric_data]
            )

            logger.debug(f"Metric sent: {metric_name}={value} {unit}")

        except Exception as e:
            logger.error(f"Failed to send metric {metric_name}: {e}")

    def put_metrics_batch(self, metrics: List[MetricData]):
        """Put multiple metrics in a single API call"""
        try:
            metric_data = []
            for metric in metrics:
                data = {
                    "MetricName": metric.metric_name,
                    "Value": metric.value,
                    "Unit": metric.unit,
                    "Timestamp": metric.timestamp,
                }

                if metric.dimensions:
                    data["Dimensions"] = [
                        {"Name": k, "Value": v} for k, v in metric.dimensions.items()
                    ]

                metric_data.append(data)

            # CloudWatch accepts max 20 metrics per call
            for i in range(0, len(metric_data), self.buffer_size):
                batch = metric_data[i : i + self.buffer_size]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace, MetricData=batch
                )

            logger.debug(f"Sent {len(metrics)} metrics in batch")

        except Exception as e:
            logger.error(f"Failed to send metrics batch: {e}")

    @contextmanager
    def timer(self, metric_name: str, dimensions: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.put_metric(f"{metric_name}_duration", duration, "Seconds", dimensions)
            self.put_metric(f"{metric_name}_count", 1, "Count", dimensions)

    def record_system_metrics(self):
        """Record system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.put_metric("cpu_usage", cpu_percent, "Percent")

            # Memory usage
            memory = psutil.virtual_memory()
            self.put_metric("memory_usage", memory.percent, "Percent")
            self.put_metric(
                "memory_available", memory.available / (1024**3), "Gigabytes"
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            self.put_metric("disk_usage", disk.percent, "Percent")
            self.put_metric("disk_available", disk.free / (1024**3), "Gigabytes")

            # Network I/O
            net_io = psutil.net_io_counters()
            self.put_metric("network_bytes_sent", net_io.bytes_sent, "Bytes")
            self.put_metric("network_bytes_recv", net_io.bytes_recv, "Bytes")

        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")


class HealthChecker:
    """Health check and system status monitoring"""

    def __init__(self, metrics: CloudWatchMetrics):
        self.metrics = metrics
        self.health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "checks": {},
        }

    async def check_neo4j_connection(self) -> bool:
        """Check Neo4j database connectivity"""
        try:
            from neo4j import GraphDatabase
            from capabilities.core.config import get_settings

            settings = get_settings()
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )

            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()

            driver.close()
            return True

        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

    async def check_openai_connection(self) -> bool:
        """Check OpenAI API connectivity"""
        try:
            import openai
            from capabilities.core.config import get_settings

            settings = get_settings()
            openai.api_key = settings.openai_api_key

            # Simple API call to test connectivity
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )

            return True

        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {}

        # System metrics
        self.metrics.record_system_metrics()

        # Database connectivity
        neo4j_healthy = await self.check_neo4j_connection()
        checks["neo4j"] = {
            "status": "healthy" if neo4j_healthy else "unhealthy",
            "timestamp": datetime.utcnow(),
        }
        self.metrics.put_metric("neo4j_healthy", 1 if neo4j_healthy else 0)

        # OpenAI connectivity
        openai_healthy = await self.check_openai_connection()
        checks["openai"] = {
            "status": "healthy" if openai_healthy else "unhealthy",
            "timestamp": datetime.utcnow(),
        }
        self.metrics.put_metric("openai_healthy", 1 if openai_healthy else 0)

        # Overall health status
        all_healthy = neo4j_healthy and openai_healthy
        overall_status = "healthy" if all_healthy else "unhealthy"

        self.health_status = {
            "status": overall_status,
            "timestamp": datetime.utcnow(),
            "checks": checks,
            "version": "1.0.0",  # Add version tracking
        }

        self.metrics.put_metric("overall_health", 1 if all_healthy else 0)

        return self.health_status


class PerformanceMonitor:
    """Performance monitoring and alerting"""

    def __init__(self, metrics: CloudWatchMetrics):
        self.metrics = metrics
        self.performance_thresholds = {
            "response_time_p95": 250,  # milliseconds
            "error_rate": 0.01,  # 1%
            "cpu_usage": 80,  # percent
            "memory_usage": 85,  # percent
        }

    def record_request_metrics(
        self, endpoint: str, duration: float, status_code: int, error: bool = False
    ):
        """Record request-level metrics"""
        dimensions = {"endpoint": endpoint}

        # Response time
        self.metrics.put_metric(
            "response_time", duration * 1000, "Milliseconds", dimensions
        )

        # Request count
        self.metrics.put_metric("request_count", 1, "Count", dimensions)

        # Error count
        if error or status_code >= 400:
            self.metrics.put_metric("error_count", 1, "Count", dimensions)

        # Status code distribution
        self.metrics.put_metric(f"status_{status_code}", 1, "Count", dimensions)

    def check_performance_alerts(self) -> List[str]:
        """Check for performance threshold violations"""
        alerts = []

        # This would typically query CloudWatch for recent metrics
        # For now, we'll return a placeholder
        logger.info("Performance alert check completed")

        return alerts


class AgentMetrics:
    """Agent-specific metrics collection"""

    def __init__(self, metrics: CloudWatchMetrics):
        self.metrics = metrics

    def record_agent_execution(
        self, agent_name: str, duration: float, success: bool, result_count: int = 0
    ):
        """Record agent execution metrics"""
        dimensions = {"agent": agent_name}

        self.metrics.put_metric(
            "agent_execution_duration", duration, "Seconds", dimensions
        )
        self.metrics.put_metric("agent_execution_count", 1, "Count", dimensions)
        self.metrics.put_metric(
            "agent_success", 1 if success else 0, "Count", dimensions
        )

        if result_count > 0:
            self.metrics.put_metric(
                "agent_result_count", result_count, "Count", dimensions
            )

    def record_research_metrics(
        self, query_type: str, duration: float, sources_found: int, quality_score: float
    ):
        """Record research-specific metrics"""
        dimensions = {"query_type": query_type}

        self.metrics.put_metric("research_duration", duration, "Seconds", dimensions)
        self.metrics.put_metric("sources_found", sources_found, "Count", dimensions)
        self.metrics.put_metric(
            "research_quality_score", quality_score, "None", dimensions
        )


# Global monitoring instance
_metrics = None
_health_checker = None
_performance_monitor = None
_agent_metrics = None


def get_monitoring() -> (
    tuple[CloudWatchMetrics, HealthChecker, PerformanceMonitor, AgentMetrics]
):
    """Get global monitoring instances"""
    global _metrics, _health_checker, _performance_monitor, _agent_metrics

    if _metrics is None:
        _metrics = CloudWatchMetrics()
        _health_checker = HealthChecker(_metrics)
        _performance_monitor = PerformanceMonitor(_metrics)
        _agent_metrics = AgentMetrics(_metrics)

    return _metrics, _health_checker, _performance_monitor, _agent_metrics


async def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    _, health_checker, _, _ = get_monitoring()
    return await health_checker.perform_health_check()
