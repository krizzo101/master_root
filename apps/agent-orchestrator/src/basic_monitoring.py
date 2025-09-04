"""
Basic Monitoring System
Real-time monitoring that integrates with working GenericOrchestrator
Built on proven orchestrator foundation
"""
import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from generic_orchestrator import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class TaskMetrics:
    """Metrics for individual task execution"""

    task_id: str
    task_type: str
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    retry_count: int = 0
    quality_gate_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    """System-wide execution metrics"""

    timestamp: float
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    avg_task_duration: float
    system_load: float
    memory_usage: float
    throughput: float  # tasks per minute

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskMonitor:
    """Monitor for individual task execution"""

    def __init__(self, task: AgentTask):
        self.task = task
        self.metrics = TaskMetrics(task_id=task.task_id, task_type=task.task_type)
        self.checkpoints = []

    def start(self):
        """Start monitoring task"""
        self.metrics.start_time = time.time()
        self.metrics.status = "running"
        logger.info(f"Task monitor started for {self.task.task_id}")

    def end(self, status: str, error: Optional[str] = None):
        """End monitoring task"""
        self.metrics.end_time = time.time()
        self.metrics.status = status
        self.metrics.error_message = error

        if self.metrics.start_time:
            self.metrics.duration = self.metrics.end_time - self.metrics.start_time

        logger.info(
            f"Task monitor ended for {self.task.task_id}: {status} ({self.metrics.duration:.2f}s)"
        )

    def add_checkpoint(self, name: str, data: Any = None):
        """Add checkpoint during task execution"""
        checkpoint = {"name": name, "timestamp": time.time(), "data": data}
        self.checkpoints.append(checkpoint)
        logger.debug(f"Checkpoint '{name}' added for task {self.task.task_id}")

    def update_quality_gates(self, results: Dict[str, Any]):
        """Update quality gate results"""
        self.metrics.quality_gate_results = results

    def get_metrics(self) -> TaskMetrics:
        """Get current task metrics"""
        return self.metrics


class RealTimeMonitor:
    """Real-time monitoring system for orchestrator execution"""

    def __init__(self, output_dir: Path, history_size: int = 1000):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Task monitoring
        self.task_monitors: Dict[str, TaskMonitor] = {}
        self.task_metrics_history = deque(maxlen=history_size)

        # System metrics
        self.system_metrics_history = deque(maxlen=history_size)
        self.start_time = time.time()

        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0,
            "avg_duration": 0.0,
            "throughput": 0.0,
            "peak_concurrent": 0,
        }

        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_task = None

        logger.info(f"Real-time monitor initialized with output dir: {output_dir}")

    def register_event_callback(self, event: str, callback: Callable):
        """Register callback for monitoring events"""
        self.event_callbacks[event].append(callback)
        logger.debug(f"Registered callback for event: {event}")

    async def _trigger_event(self, event: str, data: Any):
        """Trigger event callbacks"""
        for callback in self.event_callbacks[event]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in event callback for {event}: {e}")

    def start_task_monitoring(self, task: AgentTask) -> TaskMonitor:
        """Start monitoring a specific task"""
        monitor = TaskMonitor(task)
        self.task_monitors[task.task_id] = monitor
        monitor.start()

        self.stats["total_tasks"] += 1
        self.stats["active_tasks"] += 1
        self.stats["peak_concurrent"] = max(
            self.stats["peak_concurrent"], self.stats["active_tasks"]
        )

        asyncio.create_task(
            self._trigger_event(
                "task_started",
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "timestamp": time.time(),
                },
            )
        )

        return monitor

    def end_task_monitoring(
        self, task_id: str, status: str, error: Optional[str] = None
    ):
        """End monitoring for a specific task"""
        if task_id not in self.task_monitors:
            logger.warning(f"No monitor found for task {task_id}")
            return

        monitor = self.task_monitors[task_id]
        monitor.end(status, error)

        # Update statistics
        self.stats["active_tasks"] -= 1
        if status == "completed":
            self.stats["completed_tasks"] += 1
        else:
            self.stats["failed_tasks"] += 1

        # Update average duration
        if monitor.metrics.duration:
            total_completed = self.stats["completed_tasks"] + self.stats["failed_tasks"]
            if total_completed > 1:
                self.stats["avg_duration"] = (
                    self.stats["avg_duration"] * (total_completed - 1)
                    + monitor.metrics.duration
                ) / total_completed
            else:
                self.stats["avg_duration"] = monitor.metrics.duration

        # Store metrics in history
        self.task_metrics_history.append(monitor.get_metrics())

        asyncio.create_task(
            self._trigger_event(
                "task_completed",
                {
                    "task_id": task_id,
                    "status": status,
                    "duration": monitor.metrics.duration,
                    "timestamp": time.time(),
                },
            )
        )

        # Clean up
        del self.task_monitors[task_id]

    def start_system_monitoring(self, interval: float = 5.0):
        """Start system-wide monitoring"""
        if self.monitoring_active:
            logger.warning("System monitoring already active")
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(
            self._system_monitoring_loop(interval)
        )
        logger.info(f"System monitoring started with {interval}s interval")

    def stop_system_monitoring(self):
        """Stop system-wide monitoring"""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()

        logger.info("System monitoring stopped")

    async def _system_monitoring_loop(self, interval: float):
        """System monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                current_time = time.time()
                runtime = current_time - self.start_time

                # Calculate throughput (tasks per minute)
                throughput = (
                    (self.stats["completed_tasks"] + self.stats["failed_tasks"])
                    / (runtime / 60)
                    if runtime > 0
                    else 0
                )

                system_metrics = SystemMetrics(
                    timestamp=current_time,
                    active_tasks=self.stats["active_tasks"],
                    completed_tasks=self.stats["completed_tasks"],
                    failed_tasks=self.stats["failed_tasks"],
                    total_tasks=self.stats["total_tasks"],
                    avg_task_duration=self.stats["avg_duration"],
                    system_load=0.0,  # Would implement actual system load monitoring
                    memory_usage=0.0,  # Would implement actual memory monitoring
                    throughput=throughput,
                )

                self.system_metrics_history.append(system_metrics)

                # Trigger system metrics event
                await self._trigger_event("system_metrics", system_metrics.to_dict())

                # Save periodic snapshots
                if (
                    len(self.system_metrics_history) % 12 == 0
                ):  # Every minute if 5s interval
                    await self.save_monitoring_snapshot()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def save_monitoring_snapshot(self):
        """Save current monitoring state to disk"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.stats.copy(),
                "recent_system_metrics": [
                    m.to_dict() for m in list(self.system_metrics_history)[-10:]
                ],
                "recent_task_metrics": [
                    m.to_dict() for m in list(self.task_metrics_history)[-50:]
                ],
                "active_tasks": list(self.task_monitors.keys()),
            }

            snapshot_file = (
                self.output_dir / f"monitoring_snapshot_{int(time.time())}.json"
            )
            with open(snapshot_file, "w") as f:
                json.dump(snapshot, f, indent=2)

            logger.debug(f"Monitoring snapshot saved to {snapshot_file}")

        except Exception as e:
            logger.error(f"Error saving monitoring snapshot: {e}")

    def get_current_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        runtime = time.time() - self.start_time
        return {
            **self.stats,
            "runtime_seconds": runtime,
            "throughput_per_minute": (
                self.stats["completed_tasks"] + self.stats["failed_tasks"]
            )
            / (runtime / 60)
            if runtime > 0
            else 0,
            "success_rate": (
                self.stats["completed_tasks"]
                / max(1, self.stats["completed_tasks"] + self.stats["failed_tasks"])
            )
            * 100,
            "active_task_ids": list(self.task_monitors.keys()),
        }

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for specific task"""
        if task_id in self.task_monitors:
            return self.task_monitors[task_id].get_metrics()

        # Check history
        for metrics in reversed(self.task_metrics_history):
            if metrics.task_id == task_id:
                return metrics

        return None

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators"""
        stats = self.get_current_stats()

        # Determine health status
        health_score = 100
        warnings = []

        # Check failure rate
        if stats["success_rate"] < 80:
            health_score -= 20
            warnings.append("High failure rate detected")

        # Check if tasks are taking too long
        if stats["avg_duration"] > 300:  # 5 minutes
            health_score -= 15
            warnings.append("Tasks taking longer than expected")

        # Check for stalled tasks
        stalled_tasks = []
        current_time = time.time()
        for task_id, monitor in self.task_monitors.items():
            if (
                monitor.metrics.start_time
                and (current_time - monitor.metrics.start_time) > 600
            ):  # 10 minutes
                stalled_tasks.append(task_id)

        if stalled_tasks:
            health_score -= 25
            warnings.append(f"Stalled tasks detected: {stalled_tasks}")

        status = (
            "healthy"
            if health_score >= 80
            else "warning"
            if health_score >= 60
            else "critical"
        )

        return {
            "status": status,
            "health_score": health_score,
            "warnings": warnings,
            "statistics": stats,
            "stalled_tasks": stalled_tasks,
        }

    async def generate_monitoring_report(self) -> str:
        """Generate human-readable monitoring report"""
        stats = self.get_current_stats()
        health = self.get_system_health()

        report = [
            "=== Real-Time Monitoring Report ===",
            f"Status: {health['status'].upper()} (Health Score: {health['health_score']}/100)",
            f"Runtime: {stats['runtime_seconds']:.1f} seconds",
            "",
            "Task Statistics:",
            f"  Total Tasks: {stats['total_tasks']}",
            f"  Completed: {stats['completed_tasks']}",
            f"  Failed: {stats['failed_tasks']}",
            f"  Active: {stats['active_tasks']}",
            f"  Peak Concurrent: {stats['peak_concurrent']}",
            "",
            "Performance Metrics:",
            f"  Success Rate: {stats['success_rate']:.1f}%",
            f"  Average Duration: {stats['avg_duration']:.2f}s",
            f"  Throughput: {stats['throughput_per_minute']:.1f} tasks/min",
            "",
        ]

        # Add warnings if any
        if health["warnings"]:
            report.append("Warnings:")
            for warning in health["warnings"]:
                report.append(f"  ⚠️  {warning}")
            report.append("")

        # Add active tasks
        if stats["active_task_ids"]:
            report.append("Active Tasks:")
            for task_id in stats["active_task_ids"]:
                monitor = self.task_monitors[task_id]
                runtime = time.time() - (monitor.metrics.start_time or time.time())
                report.append(
                    f"  🔄 {task_id} ({monitor.metrics.task_type}) - {runtime:.1f}s"
                )
            report.append("")

        return "\n".join(report)


class MonitoringHooks:
    """Integration hooks for connecting monitoring with GenericOrchestrator"""

    def __init__(self, monitor: RealTimeMonitor):
        self.monitor = monitor

    def create_orchestrator_hooks(self):
        """Create hooks for GenericOrchestrator integration"""

        async def pre_execute_hook(task: AgentTask):
            """Pre-execution hook for monitoring"""
            task_monitor = self.monitor.start_task_monitoring(task)
            # Store monitor in task context for later reference
            task.context["task_monitor"] = task_monitor

        async def post_execute_hook(task: AgentTask):
            """Post-execution hook for monitoring"""
            status = task.status
            error = task.error
            self.monitor.end_task_monitoring(task.task_id, status, error)

        return pre_execute_hook, post_execute_hook


# Testing function
async def test_basic_monitoring():
    """Test basic monitoring system"""
    import tempfile
    from pathlib import Path

    print("Testing basic monitoring system...")

    # Create monitor
    output_dir = Path(tempfile.mkdtemp(prefix="monitoring_test_"))
    monitor = RealTimeMonitor(output_dir)

    # Start system monitoring
    monitor.start_system_monitoring(interval=1.0)

    # Create test tasks
    test_tasks = [
        AgentTask(
            task_id="test_task_1", task_type="research", prompt="Test research task"
        ),
        AgentTask(task_id="test_task_2", task_type="code", prompt="Test code task"),
    ]

    # Simulate task execution
    print("\nSimulating task execution...")
    for task in test_tasks:
        task_monitor = monitor.start_task_monitoring(task)

        # Simulate some work
        await asyncio.sleep(1.0)

        # Add checkpoint
        task_monitor.add_checkpoint("halfway", {"progress": 50})

        # Simulate more work
        await asyncio.sleep(1.0)

        # End monitoring
        status = "completed" if task.task_id == "test_task_1" else "failed"
        error = "Test error" if status == "failed" else None
        monitor.end_task_monitoring(task.task_id, status, error)

    # Wait for metrics collection
    await asyncio.sleep(2.0)

    # Generate report
    report = await monitor.generate_monitoring_report()
    print("\n" + report)

    # Show health
    health = monitor.get_system_health()
    print(f"\nSystem Health: {health['status']} ({health['health_score']}/100)")

    # Stop monitoring
    monitor.stop_system_monitoring()

    print(f"\nMonitoring data saved to: {output_dir}")
    return monitor


if __name__ == "__main__":
    asyncio.run(test_basic_monitoring())
