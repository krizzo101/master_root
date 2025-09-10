#!/usr/bin/env python3
"""
Multi-Agent Monitor - Agent Orchestrator Integration
Provides safety layer and monitoring for orchestrator operations
"""

import asyncio
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import orchestrator functionality
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-orchestrator" / "src"))
from generic_orchestrator import AgentTask, GenericOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class SafetyAlert:
    """Safety alert structure"""

    timestamp: datetime
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'resource', 'error_rate', 'timeout', 'token_usage'
    message: str
    task_id: Optional[str] = None
    metrics: Optional[Dict] = None


@dataclass
class MonitoringMetrics:
    """Monitoring metrics structure"""

    task_count: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time: float = 0.0
    token_usage: int = 0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_rate: float = 0.0
    alerts: List[SafetyAlert] = None

    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


class MultiAgentMonitor:
    """
    Monitor that provides safety layer for agent orchestrator
    """

    def __init__(
        self, orchestrator: GenericOrchestrator, config: Optional[Dict] = None
    ):
        self.orchestrator = orchestrator
        self.config = config or self._default_config()
        self.metrics = MonitoringMetrics()
        self.start_time = datetime.now()
        self.task_history = []
        self.output_dir = Path("./output/monitoring")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Safety thresholds
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 10)
        self.max_error_rate = self.config.get("max_error_rate", 0.3)  # 30%
        self.max_execution_time = self.config.get(
            "max_execution_time", 600
        )  # 10 minutes
        self.token_usage_warning = self.config.get(
            "token_usage_warning", 80
        )  # 80% of pool

        logger.info("🛡️ Multi-Agent Monitor initialized")

    def _default_config(self) -> Dict:
        """Default monitoring configuration"""
        return {
            "max_concurrent_tasks": 10,
            "max_error_rate": 0.3,
            "max_execution_time": 600,
            "token_usage_warning": 80,
            "alert_cooldown": 30,  # seconds
            "metrics_interval": 10,  # seconds
            "auto_recovery": True,
            "safety_checks": True,
        }

    async def safe_execute(self, tasks: List[AgentTask], **kwargs) -> Dict[str, Any]:
        """
        Safely execute tasks with monitoring and safety checks
        """
        logger.info(f"🛡️ Safe execution of {len(tasks)} tasks")

        # Pre-execution safety checks
        if not self._pre_execution_checks(tasks):
            raise RuntimeError("Pre-execution safety checks failed")

        # Start monitoring
        monitor_task = asyncio.create_task(self._monitor_execution())

        try:
            # Execute with monitoring
            start_time = time.time()
            results = await self._execute_with_monitoring(tasks)
            execution_time = time.time() - start_time

            # Update metrics
            self.metrics.task_count += len(tasks)
            self.metrics.avg_execution_time = (
                self.metrics.avg_execution_time * (self.metrics.task_count - len(tasks))
                + execution_time
            ) / self.metrics.task_count

            # Process results
            successful = sum(
                1 for r in results.values() if r.get("status") == "completed"
            )
            failed = len(results) - successful

            self.metrics.successful_tasks += successful
            self.metrics.failed_tasks += failed
            self.metrics.error_rate = (
                self.metrics.failed_tasks / self.metrics.task_count
            )

            # Safety evaluation
            safety_report = self._evaluate_safety(results, execution_time)

            # Generate report
            report = {
                "execution_summary": {
                    "total_tasks": len(tasks),
                    "successful": successful,
                    "failed": failed,
                    "execution_time": execution_time,
                    "error_rate": failed / len(tasks) if tasks else 0,
                },
                "safety_report": safety_report,
                "metrics": asdict(self.metrics),
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

            # Save monitoring report
            self._save_monitoring_report(report)

            logger.info(
                f"✅ Safe execution complete: {successful}/{len(tasks)} successful"
            )
            return report

        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

    def _pre_execution_checks(self, tasks: List[AgentTask]) -> bool:
        """Perform pre-execution safety checks"""
        logger.info("🔍 Running pre-execution safety checks")

        # Check task count
        if len(tasks) > self.max_concurrent_tasks:
            self._add_alert(
                "critical",
                "resource",
                f"Task count ({len(tasks)}) exceeds safety limit ({self.max_concurrent_tasks})",
            )
            return False

        # Check orchestrator health
        if not hasattr(self.orchestrator, "tokens") or not self.orchestrator.tokens:
            self._add_alert(
                "critical", "resource", "No tokens available in orchestrator"
            )
            return False

        # Check recent error rate
        if self.metrics.error_rate > self.max_error_rate:
            self._add_alert(
                "warning",
                "error_rate",
                f"Recent error rate ({self.metrics.error_rate:.2%}) exceeds threshold",
            )

        # Validate task structure
        for task in tasks:
            if not task.task_id or not task.prompt:
                self._add_alert(
                    "warning",
                    "task_validation",
                    f"Task {task.task_id} missing required fields",
                )

        logger.info("✅ Pre-execution checks passed")
        return True

    async def _execute_with_monitoring(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Execute tasks with active monitoring"""
        logger.info("⚡ Executing tasks with active monitoring")

        # Track task start
        for task in tasks:
            self.task_history.append(
                {
                    "task_id": task.task_id,
                    "start_time": datetime.now(),
                    "status": "running",
                }
            )

        # Execute through orchestrator
        results = await self.orchestrator.execute_batch(tasks)

        # Update task history
        for task_id, result in results.items():
            for history_item in self.task_history:
                if history_item["task_id"] == task_id:
                    history_item["end_time"] = datetime.now()
                    history_item["status"] = result.get("status", "unknown")
                    history_item["duration"] = (
                        history_item["end_time"] - history_item["start_time"]
                    ).total_seconds()

        return results

    async def _monitor_execution(self):
        """Background monitoring during execution"""
        try:
            while True:
                await asyncio.sleep(self.config["metrics_interval"])
                self._collect_metrics()
                self._check_safety_conditions()
        except asyncio.CancelledError:
            logger.info("🛡️ Monitoring stopped")

    def _collect_metrics(self):
        """Collect system metrics"""
        try:
            import psutil

            self.metrics.cpu_usage = psutil.cpu_percent()
            self.metrics.memory_usage = psutil.virtual_memory().percent

            # Check token usage
            if hasattr(self.orchestrator, "token_pool"):
                total_tokens = (
                    len(self.orchestrator.tokens) if self.orchestrator.tokens else 0
                )
                available_tokens = (
                    self.orchestrator.token_pool.size()
                    if hasattr(self.orchestrator.token_pool, "size")
                    else total_tokens
                )
                if total_tokens > 0:
                    usage_percent = (
                        (total_tokens - available_tokens) / total_tokens
                    ) * 100
                    if usage_percent > self.token_usage_warning:
                        self._add_alert(
                            "warning",
                            "token_usage",
                            f"Token usage at {usage_percent:.1f}%",
                        )

        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.warning(f"Error collecting metrics: {e}")

    def _check_safety_conditions(self):
        """Check safety conditions during execution"""
        # Check for long-running tasks
        current_time = datetime.now()
        for task_history in self.task_history:
            if task_history["status"] == "running":
                duration = (current_time - task_history["start_time"]).total_seconds()
                if duration > self.max_execution_time:
                    self._add_alert(
                        "critical",
                        "timeout",
                        f"Task {task_history['task_id']} running for {duration:.0f}s",
                    )

        # Check system resources
        if self.metrics.cpu_usage > 90:
            self._add_alert(
                "warning", "resource", f"High CPU usage: {self.metrics.cpu_usage:.1f}%"
            )

        if self.metrics.memory_usage > 85:
            self._add_alert(
                "warning",
                "resource",
                f"High memory usage: {self.metrics.memory_usage:.1f}%",
            )

    def _evaluate_safety(self, results: Dict, execution_time: float) -> Dict[str, Any]:
        """Evaluate safety after execution"""
        safety_score = 1.0
        issues = []

        # Evaluate error rate
        if results:
            failed_count = sum(
                1 for r in results.values() if r.get("status") != "completed"
            )
            error_rate = failed_count / len(results)

            if error_rate > 0.5:
                safety_score *= 0.5
                issues.append(f"High error rate: {error_rate:.2%}")
            elif error_rate > 0.2:
                safety_score *= 0.8
                issues.append(f"Moderate error rate: {error_rate:.2%}")

        # Evaluate execution time
        if execution_time > self.max_execution_time:
            safety_score *= 0.7
            issues.append(f"Execution time exceeded limit: {execution_time:.0f}s")

        # Evaluate alerts
        critical_alerts = [a for a in self.metrics.alerts if a.severity == "critical"]
        if critical_alerts:
            safety_score *= 0.3
            issues.append(f"{len(critical_alerts)} critical alerts")

        return {
            "safety_score": safety_score,
            "safety_level": "safe"
            if safety_score > 0.8
            else "caution"
            if safety_score > 0.5
            else "unsafe",
            "issues": issues,
            "recommendations": self._get_safety_recommendations(safety_score, issues),
        }

    def _get_safety_recommendations(
        self, safety_score: float, issues: List[str]
    ) -> List[str]:
        """Get safety recommendations"""
        recommendations = []

        if safety_score < 0.5:
            recommendations.append("Consider reducing task complexity or count")
            recommendations.append("Review error patterns and fix common issues")

        if "error rate" in " ".join(issues).lower():
            recommendations.append("Implement better error handling and retries")

        if "execution time" in " ".join(issues).lower():
            recommendations.append("Break down long-running tasks into smaller chunks")

        if "critical alerts" in " ".join(issues).lower():
            recommendations.append("Address critical issues before continuing")

        return recommendations

    def _add_alert(
        self, severity: str, category: str, message: str, task_id: Optional[str] = None
    ):
        """Add safety alert"""
        alert = SafetyAlert(
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            task_id=task_id,
        )
        self.metrics.alerts.append(alert)

        # Log alert
        log_level = logging.CRITICAL if severity == "critical" else logging.WARNING
        logger.log(log_level, f"🚨 {severity.upper()}: {message}")

    def _save_monitoring_report(self, report: Dict):
        """Save monitoring report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"monitoring_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"📊 Monitoring report saved: {report_file}")

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "uptime_seconds": uptime,
            "total_tasks_monitored": self.metrics.task_count,
            "success_rate": (
                self.metrics.successful_tasks / self.metrics.task_count
                if self.metrics.task_count > 0
                else 0
            ),
            "current_error_rate": self.metrics.error_rate,
            "active_alerts": len(
                [
                    a
                    for a in self.metrics.alerts
                    if (datetime.now() - a.timestamp).total_seconds() < 300
                ]
            ),
            "safety_status": "operational"
            if self.metrics.error_rate < self.max_error_rate
            else "degraded",
            "metrics": asdict(self.metrics),
        }

    def reset_metrics(self):
        """Reset monitoring metrics"""
        logger.info("🔄 Resetting monitoring metrics")
        self.metrics = MonitoringMetrics()
        self.task_history = []
        self.start_time = datetime.now()


async def main():
    """
    Main entry point for multi-agent monitor integration
    """
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_monitor_integration.py '<task_description>'")
        print(
            "Example: python orchestrator_monitor_integration.py 'Analyze system performance'"
        )
        return

    description = sys.argv[1]

    # Initialize orchestrator and monitor
    orchestrator = GenericOrchestrator(max_parallel=5, use_optimizations=True)
    monitor = MultiAgentMonitor(orchestrator)

    # Create test tasks
    tasks = [
        AgentTask(
            task_id="analysis_task",
            task_type="performance-optimizer",
            prompt=f"Analyze and provide recommendations for: {description}",
        ),
        AgentTask(
            task_id="safety_check",
            task_type="security-architect",
            prompt=f"Evaluate safety considerations for: {description}",
        ),
    ]

    try:
        report = await monitor.safe_execute(tasks)

        print("\n" + "=" * 60)
        print("🛡️ MULTI-AGENT MONITOR REPORT")
        print("=" * 60)
        print(f"Task Description: {description}")
        print(f"Safety Level: {report['safety_report']['safety_level']}")
        print(
            f"Success Rate: {report['execution_summary']['successful']}/{report['execution_summary']['total_tasks']}"
        )
        print(f"Execution Time: {report['execution_summary']['execution_time']:.2f}s")
        print(f"Safety Score: {report['safety_report']['safety_score']:.2f}")

        if report["safety_report"]["issues"]:
            print("\n⚠️ Issues:")
            for issue in report["safety_report"]["issues"]:
                print(f"  - {issue}")

        if report["safety_report"]["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in report["safety_report"]["recommendations"]:
                print(f"  - {rec}")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Monitor execution failed: {e}")
        print(f"❌ Monitoring failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
