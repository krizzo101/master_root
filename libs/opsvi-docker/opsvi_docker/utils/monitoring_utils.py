"""
Monitoring Utility Functions

Docker monitoring and metrics collection utilities.
Provides performance monitoring and resource tracking capabilities.
"""

import logging
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Thread, Event
import json

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Metric data point."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Alert rule configuration."""

    name: str
    metric: str
    condition: str  # gt, lt, eq, gte, lte
    threshold: float
    duration: int  # seconds
    enabled: bool = True
    actions: List[str] = field(default_factory=list)


class MonitoringUtils:
    """
    Monitoring utility functions.

    Provides monitoring and metrics collection utilities:
    - Resource usage tracking
    - Performance metrics collection
    - Alert rule evaluation
    - Metric aggregation and reporting
    """

    @staticmethod
    def collect_container_metrics(container_stats: Dict[str, Any]) -> List[MetricData]:
        """Collect metrics from container stats."""
        metrics = []
        timestamp = datetime.now()

        try:
            # CPU metrics
            cpu_stats = container_stats.get("cpu_stats", {})
            precpu_stats = container_stats.get("precpu_stats", {})

            cpu_usage = MonitoringUtils._calculate_cpu_usage(cpu_stats, precpu_stats)
            if cpu_usage is not None:
                metrics.append(
                    MetricData(
                        name="container_cpu_usage_percent",
                        value=cpu_usage,
                        unit="percent",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            # Memory metrics
            memory_stats = container_stats.get("memory_stats", {})
            memory_usage = memory_stats.get("usage", 0)
            memory_limit = memory_stats.get("limit", 0)

            if memory_usage > 0:
                metrics.append(
                    MetricData(
                        name="container_memory_usage_bytes",
                        value=float(memory_usage),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            if memory_limit > 0:
                metrics.append(
                    MetricData(
                        name="container_memory_limit_bytes",
                        value=float(memory_limit),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

                memory_usage_percent = (memory_usage / memory_limit) * 100
                metrics.append(
                    MetricData(
                        name="container_memory_usage_percent",
                        value=memory_usage_percent,
                        unit="percent",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            # Network metrics
            networks = container_stats.get("networks", {})
            total_rx_bytes = sum(net.get("rx_bytes", 0) for net in networks.values())
            total_tx_bytes = sum(net.get("tx_bytes", 0) for net in networks.values())

            if total_rx_bytes > 0:
                metrics.append(
                    MetricData(
                        name="container_network_rx_bytes",
                        value=float(total_rx_bytes),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            if total_tx_bytes > 0:
                metrics.append(
                    MetricData(
                        name="container_network_tx_bytes",
                        value=float(total_tx_bytes),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            # Block I/O metrics
            blkio_stats = container_stats.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])

            read_bytes = 0
            write_bytes = 0

            for entry in io_service_bytes:
                if entry.get("op") == "Read":
                    read_bytes += entry.get("value", 0)
                elif entry.get("op") == "Write":
                    write_bytes += entry.get("value", 0)

            if read_bytes > 0:
                metrics.append(
                    MetricData(
                        name="container_disk_read_bytes",
                        value=float(read_bytes),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

            if write_bytes > 0:
                metrics.append(
                    MetricData(
                        name="container_disk_write_bytes",
                        value=float(write_bytes),
                        unit="bytes",
                        timestamp=timestamp,
                        labels={"container_id": container_stats.get("id", "")[:12]},
                    )
                )

        except Exception as e:
            logger.error(f"Error collecting container metrics: {e}")

        return metrics

    @staticmethod
    def _calculate_cpu_usage(
        cpu_stats: Dict[str, Any], precpu_stats: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate CPU usage percentage."""
        try:
            cpu_delta = cpu_stats.get("cpu_usage", {}).get(
                "total_usage", 0
            ) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)

            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            if system_delta > 0 and cpu_delta > 0:
                cpu_count = len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", []))
                if cpu_count == 0:
                    cpu_count = 1

                return (cpu_delta / system_delta) * cpu_count * 100.0

        except Exception as e:
            logger.error(f"Error calculating CPU usage: {e}")

        return None

    @staticmethod
    def collect_system_metrics() -> List[MetricData]:
        """Collect system-level Docker metrics."""
        metrics = []
        timestamp = datetime.now()

        try:
            import subprocess

            # Get Docker system info
            result = subprocess.run(
                ["docker", "system", "df", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)

                    # Images metrics
                    images = data.get("Images", [])
                    if images:
                        total_size = sum(img.get("Size", 0) for img in images)
                        metrics.append(
                            MetricData(
                                name="docker_images_total_size_bytes",
                                value=float(total_size),
                                unit="bytes",
                                timestamp=timestamp,
                            )
                        )

                        metrics.append(
                            MetricData(
                                name="docker_images_count",
                                value=float(len(images)),
                                unit="count",
                                timestamp=timestamp,
                            )
                        )

                    # Containers metrics
                    containers = data.get("Containers", [])
                    if containers:
                        total_size = sum(cont.get("SizeRw", 0) for cont in containers)
                        metrics.append(
                            MetricData(
                                name="docker_containers_total_size_bytes",
                                value=float(total_size),
                                unit="bytes",
                                timestamp=timestamp,
                            )
                        )

                        metrics.append(
                            MetricData(
                                name="docker_containers_count",
                                value=float(len(containers)),
                                unit="count",
                                timestamp=timestamp,
                            )
                        )

                    # Volumes metrics
                    volumes = data.get("Volumes", [])
                    if volumes:
                        total_size = sum(vol.get("Size", 0) for vol in volumes)
                        metrics.append(
                            MetricData(
                                name="docker_volumes_total_size_bytes",
                                value=float(total_size),
                                unit="bytes",
                                timestamp=timestamp,
                            )
                        )

                        metrics.append(
                            MetricData(
                                name="docker_volumes_count",
                                value=float(len(volumes)),
                                unit="count",
                                timestamp=timestamp,
                            )
                        )

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Docker system info: {e}")

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics

    @staticmethod
    def evaluate_alert_rules(
        metrics: List[MetricData],
        rules: List[AlertRule],
        history: Dict[str, List[MetricData]] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate alert rules against metrics."""
        alerts = []

        if history is None:
            history = {}

        for rule in rules:
            if not rule.enabled:
                continue

            # Find metrics matching the rule
            matching_metrics = [m for m in metrics if m.name == rule.metric]

            for metric in matching_metrics:
                # Evaluate condition
                triggered = MonitoringUtils._evaluate_condition(
                    metric.value, rule.condition, rule.threshold
                )

                if triggered:
                    # Check duration requirement
                    rule_key = (
                        f"{rule.name}_{metric.labels.get('container_id', 'system')}"
                    )

                    if rule_key not in history:
                        history[rule_key] = []

                    history[rule_key].append(metric)

                    # Keep only recent history
                    cutoff_time = datetime.now() - timedelta(seconds=rule.duration * 2)
                    history[rule_key] = [
                        m for m in history[rule_key] if m.timestamp > cutoff_time
                    ]

                    # Check if alert should fire
                    recent_metrics = [
                        m
                        for m in history[rule_key]
                        if m.timestamp
                        > datetime.now() - timedelta(seconds=rule.duration)
                    ]

                    if len(recent_metrics) > 0:
                        # Alert should fire
                        alert = {
                            "rule_name": rule.name,
                            "metric_name": metric.name,
                            "metric_value": metric.value,
                            "threshold": rule.threshold,
                            "condition": rule.condition,
                            "duration": rule.duration,
                            "timestamp": metric.timestamp,
                            "labels": metric.labels,
                            "actions": rule.actions,
                            "severity": MonitoringUtils._determine_severity(
                                metric.value, rule.threshold, rule.condition
                            ),
                        }
                        alerts.append(alert)

        return alerts

    @staticmethod
    def _evaluate_condition(value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return abs(value - threshold) < 0.001  # floating point comparison
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    @staticmethod
    def _determine_severity(value: float, threshold: float, condition: str) -> str:
        """Determine alert severity based on how far value exceeds threshold."""
        if condition in ["gt", "gte"]:
            ratio = value / threshold if threshold > 0 else float("inf")
            if ratio > 2.0:
                return "critical"
            elif ratio > 1.5:
                return "warning"
            else:
                return "info"
        elif condition in ["lt", "lte"]:
            ratio = threshold / value if value > 0 else float("inf")
            if ratio > 2.0:
                return "critical"
            elif ratio > 1.5:
                return "warning"
            else:
                return "info"
        else:
            return "info"

    @staticmethod
    def aggregate_metrics(
        metrics: List[MetricData],
        time_window: int = 300,  # 5 minutes
        aggregation: str = "avg",  # avg, sum, min, max, count
    ) -> Dict[str, List[MetricData]]:
        """Aggregate metrics by time window."""
        aggregated = {}

        # Group metrics by name
        by_name = {}
        for metric in metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric)

        # Aggregate each metric type
        for name, metric_list in by_name.items():
            # Sort by timestamp
            metric_list.sort(key=lambda x: x.timestamp)

            # Group by time windows
            windows = {}
            for metric in metric_list:
                window_start = (
                    int(metric.timestamp.timestamp() // time_window) * time_window
                )
                window_key = datetime.fromtimestamp(window_start)

                if window_key not in windows:
                    windows[window_key] = []
                windows[window_key].append(metric)

            # Aggregate each window
            aggregated[name] = []
            for window_start, window_metrics in windows.items():
                if not window_metrics:
                    continue

                values = [m.value for m in window_metrics]

                if aggregation == "avg":
                    agg_value = sum(values) / len(values)
                elif aggregation == "sum":
                    agg_value = sum(values)
                elif aggregation == "min":
                    agg_value = min(values)
                elif aggregation == "max":
                    agg_value = max(values)
                elif aggregation == "count":
                    agg_value = len(values)
                else:
                    agg_value = sum(values) / len(values)  # default to avg

                # Use labels from first metric in window
                labels = window_metrics[0].labels.copy()
                labels["aggregation"] = aggregation
                labels["window_size"] = str(time_window)

                aggregated_metric = MetricData(
                    name=f"{name}_{aggregation}",
                    value=agg_value,
                    unit=window_metrics[0].unit,
                    timestamp=window_start,
                    labels=labels,
                )

                aggregated[name].append(aggregated_metric)

        return aggregated

    @staticmethod
    def format_metrics_report(metrics: List[MetricData]) -> str:
        """Format metrics into a readable report."""
        if not metrics:
            return "No metrics available."

        report = []
        report.append("=== Docker Metrics Report ===")
        report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Metrics: {len(metrics)}")
        report.append("")

        # Group by metric name
        by_name = {}
        for metric in metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric)

        for name, metric_list in sorted(by_name.items()):
            report.append(f"=== {name} ===")

            for metric in sorted(metric_list, key=lambda x: x.timestamp, reverse=True):
                labels_str = ", ".join(f"{k}={v}" for k, v in metric.labels.items())
                if labels_str:
                    labels_str = f" ({labels_str})"

                report.append(
                    f"  {metric.value:.2f} {metric.unit}{labels_str} "
                    f"@ {metric.timestamp.strftime('%H:%M:%S')}"
                )

            report.append("")

        return "\n".join(report)
