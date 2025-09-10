#!/usr/bin/env python3
"""
Unified OpsVI Monitoring Platform
Consolidates all monitoring capabilities into a single solution
"""

import asyncio
import json
import logging
import queue
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Import orchestrator functionality
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "agent-orchestrator" / "src")
)
from generic_orchestrator import AgentTask, GenericOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    value: float
    labels: Dict[str, str]
    metric_name: str


@dataclass
class Alert:
    """Alert definition"""

    id: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    description: str
    timestamp: datetime
    source: str
    labels: Dict[str, str]
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""

    collectors_enabled: Dict[str, bool]
    metrics_interval: int = 10
    retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    storage_backend: str = "memory"
    dashboard_port: int = 8080

    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "error_rate": 0.3,
                "response_time": 30.0,
                "cpu_usage": 85.0,
                "memory_usage": 85.0,
                "cost_per_hour": 10.0,
            }


class MetricsCollector:
    """Base class for metrics collectors"""

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.interval = config.get("interval", 10)

    async def collect(self) -> List[MetricPoint]:
        """Collect metrics - override in subclasses"""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        return self.enabled


class OrchestratorCollector(MetricsCollector):
    """Collects metrics from agent orchestrator"""

    def __init__(
        self, config: Dict, orchestrator: Optional[GenericOrchestrator] = None
    ):
        super().__init__("orchestrator", config)
        self.orchestrator = orchestrator
        self.task_history = deque(maxlen=1000)
        self.execution_times = deque(maxlen=100)

    async def collect(self) -> List[MetricPoint]:
        metrics = []
        now = datetime.now()

        if not self.orchestrator:
            return metrics

        # Token usage metrics
        if hasattr(self.orchestrator, "tokens") and self.orchestrator.tokens:
            total_tokens = len(self.orchestrator.tokens)
            available_tokens = (
                self.orchestrator.token_pool.size()
                if hasattr(self.orchestrator.token_pool, "size")
                else total_tokens
            )

            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=total_tokens - available_tokens,
                    labels={"type": "tokens_used"},
                    metric_name="orchestrator_token_usage",
                )
            )

            usage_percent = ((total_tokens - available_tokens) / total_tokens) * 100
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=usage_percent,
                    labels={"type": "tokens_usage_percent"},
                    metric_name="orchestrator_token_usage_percent",
                )
            )

        # Task execution metrics
        recent_tasks = [
            t for t in self.task_history if (now - t["timestamp"]).seconds < 300
        ]

        metrics.append(
            MetricPoint(
                timestamp=now,
                value=len(recent_tasks),
                labels={"timeframe": "5min"},
                metric_name="orchestrator_tasks_recent",
            )
        )

        if recent_tasks:
            successful_tasks = sum(
                1 for t in recent_tasks if t["status"] == "completed"
            )
            error_rate = (len(recent_tasks) - successful_tasks) / len(recent_tasks)

            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=error_rate,
                    labels={"timeframe": "5min"},
                    metric_name="orchestrator_error_rate",
                )
            )

        # Average execution time
        if self.execution_times:
            avg_time = sum(self.execution_times) / len(self.execution_times)
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=avg_time,
                    labels={"type": "average"},
                    metric_name="orchestrator_execution_time",
                )
            )

        return metrics

    def record_task(self, task_id: str, status: str, execution_time: float = None):
        """Record task execution"""
        self.task_history.append(
            {"task_id": task_id, "status": status, "timestamp": datetime.now()}
        )

        if execution_time:
            self.execution_times.append(execution_time)


class SystemCollector(MetricsCollector):
    """Collects system resource metrics"""

    def __init__(self, config: Dict):
        super().__init__("system", config)

    async def collect(self) -> List[MetricPoint]:
        metrics = []
        now = datetime.now()

        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=cpu_percent,
                    labels={"resource": "cpu"},
                    metric_name="system_resource_usage",
                )
            )

            # Memory usage
            memory = psutil.virtual_memory()
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=memory.percent,
                    labels={"resource": "memory"},
                    metric_name="system_resource_usage",
                )
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=disk_percent,
                    labels={"resource": "disk"},
                    metric_name="system_resource_usage",
                )
            )

        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

        return metrics


class ClaudeCollector(MetricsCollector):
    """Collects Claude API usage metrics"""

    def __init__(self, config: Dict):
        super().__init__("claude", config)
        self.api_calls = deque(maxlen=1000)
        self.costs = deque(maxlen=1000)

    async def collect(self) -> List[MetricPoint]:
        metrics = []
        now = datetime.now()

        # Recent API calls
        recent_calls = [
            c for c in self.api_calls if (now - c["timestamp"]).seconds < 3600
        ]

        metrics.append(
            MetricPoint(
                timestamp=now,
                value=len(recent_calls),
                labels={"timeframe": "1hour"},
                metric_name="claude_api_calls",
            )
        )

        # Cost tracking
        recent_costs = [c for c in self.costs if (now - c["timestamp"]).seconds < 3600]
        if recent_costs:
            total_cost = sum(c["amount"] for c in recent_costs)
            metrics.append(
                MetricPoint(
                    timestamp=now,
                    value=total_cost,
                    labels={"timeframe": "1hour", "currency": "usd"},
                    metric_name="claude_api_cost",
                )
            )

        return metrics

    def record_api_call(self, model: str, tokens_used: int, cost: float):
        """Record API call"""
        now = datetime.now()
        self.api_calls.append({"model": model, "tokens": tokens_used, "timestamp": now})
        self.costs.append({"amount": cost, "timestamp": now})


class AlertProcessor:
    """Processes metrics and generates alerts"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alert_history = deque(maxlen=1000)
        self.active_alerts = {}

    def process_metrics(self, metrics: List[MetricPoint]) -> List[Alert]:
        """Process metrics and generate alerts"""
        alerts = []

        for metric in metrics:
            alert = self._check_threshold(metric)
            if alert:
                alerts.append(alert)

        return alerts

    def _check_threshold(self, metric: MetricPoint) -> Optional[Alert]:
        """Check if metric exceeds threshold"""
        thresholds = self.config.alert_thresholds

        # Error rate threshold
        if (
            metric.metric_name == "orchestrator_error_rate"
            and metric.value > thresholds.get("error_rate", 0.3)
        ):
            return Alert(
                id=f"error_rate_{int(time.time())}",
                severity="warning" if metric.value < 0.5 else "critical",
                title="High Error Rate Detected",
                description=f"Error rate is {metric.value:.2%}, above threshold of {thresholds['error_rate']:.2%}",
                timestamp=metric.timestamp,
                source="orchestrator",
                labels=metric.labels,
            )

        # Response time threshold
        if (
            metric.metric_name == "orchestrator_execution_time"
            and metric.value > thresholds.get("response_time", 30)
        ):
            return Alert(
                id=f"response_time_{int(time.time())}",
                severity="warning",
                title="Slow Execution Time",
                description=f"Average execution time is {metric.value:.2f}s, above threshold of {thresholds['response_time']}s",
                timestamp=metric.timestamp,
                source="orchestrator",
                labels=metric.labels,
            )

        # Resource usage thresholds
        if metric.metric_name == "system_resource_usage":
            resource = metric.labels.get("resource", "")
            threshold_key = f"{resource}_usage"
            threshold = thresholds.get(threshold_key, 85)

            if metric.value > threshold:
                return Alert(
                    id=f"{resource}_usage_{int(time.time())}",
                    severity="warning" if metric.value < 90 else "critical",
                    title=f"High {resource.title()} Usage",
                    description=f"{resource.title()} usage is {metric.value:.1f}%, above threshold of {threshold}%",
                    timestamp=metric.timestamp,
                    source="system",
                    labels=metric.labels,
                )

        return None


class UnifiedMonitor:
    """Main unified monitoring platform"""

    def __init__(
        self,
        orchestrator: Optional[GenericOrchestrator] = None,
        config: Optional[MonitoringConfig] = None,
    ):
        self.orchestrator = orchestrator
        self.config = config or MonitoringConfig(
            collectors_enabled={"orchestrator": True, "system": True, "claude": True}
        )

        # Initialize collectors
        self.collectors = {}
        if self.config.collectors_enabled.get("orchestrator", True):
            self.collectors["orchestrator"] = OrchestratorCollector(
                {"enabled": True, "interval": self.config.metrics_interval},
                orchestrator,
            )
        if self.config.collectors_enabled.get("system", True):
            self.collectors["system"] = SystemCollector(
                {"enabled": True, "interval": self.config.metrics_interval}
            )
        if self.config.collectors_enabled.get("claude", True):
            self.collectors["claude"] = ClaudeCollector(
                {"enabled": True, "interval": self.config.metrics_interval}
            )

        # Initialize processors
        self.alert_processor = AlertProcessor(self.config)

        # Storage
        self.metrics_history = deque(maxlen=10000)
        self.alerts_history = deque(maxlen=1000)

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.metrics_queue = queue.Queue()

        # Output directory
        self.output_dir = Path("./output/unified_monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("🔍 Unified OpsVI Monitor initialized")

    def start(self):
        """Start monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        logger.info("📊 Unified monitoring started")

    def stop(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("🛑 Unified monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics from all collectors
                all_metrics = []

                for collector in self.collectors.values():
                    if collector.is_enabled():
                        metrics = asyncio.run(collector.collect())
                        all_metrics.extend(metrics)

                # Store metrics
                self.metrics_history.extend(all_metrics)

                # Process alerts
                alerts = self.alert_processor.process_metrics(all_metrics)
                self.alerts_history.extend(alerts)

                # Log new alerts
                for alert in alerts:
                    log_level = (
                        logging.CRITICAL
                        if alert.severity == "critical"
                        else logging.WARNING
                    )
                    logger.log(log_level, f"🚨 {alert.title}: {alert.description}")

                # Save metrics periodically
                if len(self.metrics_history) % 100 == 0:
                    self._save_metrics()

                time.sleep(self.config.metrics_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.metrics_interval)

    def _save_metrics(self):
        """Save metrics to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = self.output_dir / f"metrics_{timestamp}.json"

            # Convert recent metrics to JSON
            recent_metrics = list(self.metrics_history)[-1000:]  # Last 1000 metrics
            metrics_data = []

            for metric in recent_metrics:
                metrics_data.append(
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "labels": metric.labels,
                    }
                )

            with open(metrics_file, "w") as f:
                json.dump(metrics_data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    async def safe_execute(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute tasks with comprehensive monitoring"""
        logger.info(f"🛡️ Safe execution with unified monitoring: {len(tasks)} tasks")

        if not self.orchestrator:
            raise RuntimeError("No orchestrator configured for safe execution")

        start_time = time.time()

        try:
            # Pre-execution metrics
            pre_metrics = []
            for collector in self.collectors.values():
                if collector.is_enabled():
                    metrics = await collector.collect()
                    pre_metrics.extend(metrics)

            # Execute tasks
            results = await self.orchestrator.execute_batch(tasks)

            execution_time = time.time() - start_time

            # Record execution in orchestrator collector
            if "orchestrator" in self.collectors:
                orchestrator_collector = self.collectors["orchestrator"]
                successful = sum(
                    1 for r in results.values() if r.get("status") == "completed"
                )

                for i, (task_id, result) in enumerate(results.items()):
                    orchestrator_collector.record_task(
                        task_id,
                        result.get("status", "unknown"),
                        execution_time / len(results) if i == 0 else None,
                    )

            # Post-execution metrics
            post_metrics = []
            for collector in self.collectors.values():
                if collector.is_enabled():
                    metrics = await collector.collect()
                    post_metrics.extend(metrics)

            # Generate execution report
            report = {
                "execution_summary": {
                    "total_tasks": len(tasks),
                    "successful": sum(
                        1 for r in results.values() if r.get("status") == "completed"
                    ),
                    "failed": sum(
                        1 for r in results.values() if r.get("status") != "completed"
                    ),
                    "execution_time": execution_time,
                },
                "monitoring_report": {
                    "pre_execution_metrics": len(pre_metrics),
                    "post_execution_metrics": len(post_metrics),
                    "alerts_generated": len(
                        [
                            a
                            for a in self.alerts_history
                            if (datetime.now() - a.timestamp).seconds < 60
                        ]
                    ),
                    "collectors_active": len(
                        [c for c in self.collectors.values() if c.is_enabled()]
                    ),
                },
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

            # Save execution report
            self._save_execution_report(report)

            logger.info(
                f"✅ Safe execution complete: {report['execution_summary']['successful']}/{len(tasks)} successful"
            )
            return report

        except Exception as e:
            logger.error(f"Safe execution failed: {e}")
            raise

    def _save_execution_report(self, report: Dict):
        """Save execution report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"execution_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

    def get_status(self) -> Dict[str, Any]:
        """Get monitoring status"""
        recent_metrics = [
            m
            for m in self.metrics_history
            if (datetime.now() - m.timestamp).seconds < 300
        ]
        recent_alerts = [
            a
            for a in self.alerts_history
            if (datetime.now() - a.timestamp).seconds < 300
        ]

        return {
            "monitoring_active": self.monitoring_active,
            "collectors_active": len(
                [c for c in self.collectors.values() if c.is_enabled()]
            ),
            "recent_metrics": len(recent_metrics),
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len(
                [a for a in recent_alerts if a.severity == "critical"]
            ),
            "total_metrics_collected": len(self.metrics_history),
            "uptime_seconds": time.time(),
            "config": asdict(self.config),
        }

    def get_metrics(
        self, metric_name: Optional[str] = None, hours: int = 1
    ) -> List[Dict]:
        """Get metrics for API/dashboard"""
        cutoff = datetime.now() - timedelta(hours=hours)

        filtered_metrics = [
            m
            for m in self.metrics_history
            if m.timestamp > cutoff
            and (not metric_name or m.metric_name == metric_name)
        ]

        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "metric_name": m.metric_name,
                "value": m.value,
                "labels": m.labels,
            }
            for m in filtered_metrics
        ]

    def get_alerts(
        self, severity: Optional[str] = None, resolved: bool = False
    ) -> List[Dict]:
        """Get alerts for API/dashboard"""
        filtered_alerts = [
            a
            for a in self.alerts_history
            if (not severity or a.severity == severity) and (resolved or not a.resolved)
        ]

        return [asdict(alert) for alert in filtered_alerts]


async def main():
    """Main entry point for unified monitoring demo"""
    if len(sys.argv) < 2:
        print("Usage: python unified_monitor.py '<task_description>'")
        print("Example: python unified_monitor.py 'Monitor system performance'")
        return

    description = sys.argv[1]

    # Initialize orchestrator and unified monitor
    orchestrator = GenericOrchestrator(max_parallel=5, use_optimizations=True)
    monitor = UnifiedMonitor(orchestrator)

    # Start monitoring
    monitor.start()

    # Create test tasks
    tasks = [
        AgentTask(
            task_id="monitoring_test",
            task_type="performance-optimizer",
            prompt=f"Analyze and optimize: {description}",
        ),
        AgentTask(
            task_id="system_check",
            task_type="security-architect",
            prompt=f"Check system health for: {description}",
        ),
    ]

    try:
        # Execute with unified monitoring
        report = await monitor.safe_execute(tasks)

        # Wait for metrics collection
        await asyncio.sleep(5)

        # Get monitoring status
        status = monitor.get_status()
        metrics = monitor.get_metrics(hours=1)
        alerts = monitor.get_alerts()

        print("\n" + "=" * 60)
        print("🔍 UNIFIED OPSVI MONITORING REPORT")
        print("=" * 60)
        print(f"Task Description: {description}")
        print(
            f"Execution Status: {report['execution_summary']['successful']}/{report['execution_summary']['total_tasks']} successful"
        )
        print(f"Execution Time: {report['execution_summary']['execution_time']:.2f}s")
        print(f"Collectors Active: {status['collectors_active']}")
        print(f"Recent Metrics: {status['recent_metrics']}")
        print(f"Recent Alerts: {status['recent_alerts']}")

        if alerts:
            print(f"\n⚠️ Active Alerts:")
            for alert in alerts[:5]:  # Show first 5 alerts
                print(f"  [{alert['severity'].upper()}] {alert['title']}")

        print(f"\n📊 Metrics Summary:")
        metric_types = {}
        for metric in metrics[-10:]:  # Last 10 metrics
            metric_types[metric["metric_name"]] = metric["value"]

        for name, value in metric_types.items():
            print(f"  {name}: {value:.2f}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Unified monitoring demo failed: {e}")
        print(f"❌ Demo failed: {e}")
    finally:
        monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
