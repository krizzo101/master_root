#!/usr/bin/env python3
"""
Metrics Collector Component
Handles resource tracking, performance metrics, and reporting
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

logger = logging.getLogger(__name__)


@dataclass
class TaskMetrics:
    """Metrics for a single task"""

    task_id: str
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    memory_used: Optional[float] = None
    cpu_percent: Optional[float] = None
    status: str = "pending"
    error_count: int = 0
    retry_count: int = 0


@dataclass
class WorkflowMetrics:
    """Aggregated metrics for entire workflow"""

    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    total_execution_time: Optional[float] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    peak_memory_mb: float = 0
    average_task_time: float = 0
    total_cpu_time: float = 0
    deliverables_count: int = 0
    file_operations: Dict[str, int] = field(
        default_factory=lambda: {"created": 0, "modified": 0, "deleted": 0}
    )


class MetricsCollector:
    """
    Collects and manages performance metrics
    Extracted from GenericOrchestrator
    """

    def __init__(self, output_dir: Path, workflow_id: str):
        self.output_dir = output_dir.resolve()
        self.metrics_dir = self.output_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        self.workflow_id = workflow_id
        self.process = psutil.Process()

        # Initialize tracking
        self.workflow_start_time = time.time()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.initial_cpu_time = self.process.cpu_times()
        self.peak_memory = self.initial_memory

        # Task metrics
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.task_completion_times: List[float] = []

        # Workflow metrics
        self.workflow_metrics = WorkflowMetrics(
            workflow_id=workflow_id, start_time=self.workflow_start_time
        )

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []

        # File tracking
        self.deliverables: Set[str] = set()
        self.initial_file_count = self._count_files()

        logger.info(f"MetricsCollector initialized for workflow: {workflow_id}")

    def _count_files(self) -> int:
        """Count files in output directory"""
        if self.output_dir.exists():
            return len(list(self.output_dir.rglob("*")))
        return 0

    def start_task(self, task_id: str):
        """Record task start"""
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id, start_time=time.time()
        )
        self._update_resource_usage()
        logger.debug(f"Started tracking task {task_id}")

    def end_task(
        self, task_id: str, status: str = "completed", error: Optional[str] = None
    ):
        """Record task completion"""
        if task_id not in self.task_metrics:
            logger.warning(f"Task {task_id} not found in metrics")
            return

        metric = self.task_metrics[task_id]
        metric.end_time = time.time()
        metric.execution_time = metric.end_time - metric.start_time
        metric.status = status

        if status == "failed" and error:
            metric.error_count += 1

        # Update resource usage
        self._update_resource_usage()
        metric.memory_used = self.process.memory_info().rss / 1024 / 1024
        metric.cpu_percent = self.process.cpu_percent()

        # Update workflow metrics
        self.task_completion_times.append(metric.execution_time)
        if status == "completed":
            self.workflow_metrics.completed_tasks += 1
        elif status == "failed":
            self.workflow_metrics.failed_tasks += 1

        logger.debug(f"Ended tracking task {task_id}: {status}")

    def retry_task(self, task_id: str):
        """Record task retry"""
        if task_id in self.task_metrics:
            self.task_metrics[task_id].retry_count += 1

    def _update_resource_usage(self):
        """Update resource usage metrics"""
        try:
            current_memory = self.process.memory_info().rss / 1024 / 1024
            self.peak_memory = max(self.peak_memory, current_memory)
            self.workflow_metrics.peak_memory_mb = self.peak_memory

            # Update CPU time
            cpu_times = self.process.cpu_times()
            self.workflow_metrics.total_cpu_time = (
                cpu_times.user
                + cpu_times.system
                - self.initial_cpu_time.user
                - self.initial_cpu_time.system
            )
        except Exception as e:
            logger.warning(f"Failed to update resource usage: {e}")

    def log_audit_action(self, action: str, details: Dict[str, Any] = None):
        """Log an audit action"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {},
            "workflow_id": self.workflow_id,
        }
        self.audit_log.append(audit_entry)
        logger.debug(f"Audit: {action} - {details}")

    def track_deliverable(self, file_path: str, operation: str = "created"):
        """Track a deliverable file"""
        self.deliverables.add(file_path)

        if operation in self.workflow_metrics.file_operations:
            self.workflow_metrics.file_operations[operation] += 1

        self.log_audit_action(
            f"deliverable_{operation}",
            {"file": file_path, "timestamp": datetime.now().isoformat()},
        )

    def scan_for_deliverables(self) -> List[str]:
        """Scan output directory for new deliverables"""
        deliverables = []

        # Common deliverable patterns
        patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.md",
            "*.txt",
            "*.html",
            "*.css",
            "*.jsx",
            "*.tsx",
            "requirements.txt",
            "package.json",
            "Dockerfile",
            "docker-compose.yml",
        ]

        for pattern in patterns:
            for file_path in self.output_dir.rglob(pattern):
                # Skip common non-deliverable directories
                if any(
                    skip in str(file_path)
                    for skip in [
                        "__pycache__",
                        ".git",
                        "node_modules",
                        ".pytest_cache",
                        "metrics",
                        "logs",
                        "checkpoints",
                        "messages",
                    ]
                ):
                    continue

                rel_path = file_path.relative_to(self.output_dir)
                deliverable_path = str(rel_path)

                if deliverable_path not in self.deliverables:
                    self.track_deliverable(deliverable_path, "discovered")
                    deliverables.append(deliverable_path)

        return deliverables

    def calculate_eta(self, completed_tasks: int, total_tasks: int) -> Optional[int]:
        """Calculate estimated time to completion in seconds"""
        if not self.task_completion_times or completed_tasks == 0:
            return None

        if completed_tasks >= total_tasks:
            return 0

        avg_task_time = sum(self.task_completion_times) / len(
            self.task_completion_times
        )
        remaining_tasks = total_tasks - completed_tasks
        eta_seconds = int(avg_task_time * remaining_tasks)

        return eta_seconds

    def get_task_metrics(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific task"""
        if task_id in self.task_metrics:
            return asdict(self.task_metrics[task_id])
        return None

    def get_all_task_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all tasks"""
        return [asdict(metric) for metric in self.task_metrics.values()]

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get aggregated workflow metrics"""
        # Update final metrics
        self.workflow_metrics.total_tasks = len(self.task_metrics)

        if self.task_completion_times:
            self.workflow_metrics.average_task_time = sum(
                self.task_completion_times
            ) / len(self.task_completion_times)

        if self.workflow_metrics.start_time:
            current_time = time.time()
            self.workflow_metrics.total_execution_time = (
                current_time - self.workflow_metrics.start_time
            )

        self.workflow_metrics.deliverables_count = len(self.deliverables)

        return asdict(self.workflow_metrics)

    def get_resource_metrics(self) -> Dict[str, Any]:
        """Get current resource usage metrics"""
        self._update_resource_usage()

        return {
            "current_memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "peak_memory_mb": self.peak_memory,
            "memory_increase_mb": self.peak_memory - self.initial_memory,
            "cpu_percent": self.process.cpu_percent(),
            "total_cpu_time": self.workflow_metrics.total_cpu_time,
            "num_threads": self.process.num_threads(),
            "num_files": self._count_files() - self.initial_file_count,
        }

    def generate_completion_report(self) -> Dict[str, Any]:
        """Generate comprehensive completion report"""
        self.scan_for_deliverables()

        workflow_metrics = self.get_workflow_metrics()
        resource_metrics = self.get_resource_metrics()

        # Calculate success rate
        total_tasks = workflow_metrics["total_tasks"]
        completed_tasks = workflow_metrics["completed_tasks"]
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        report = {
            "workflow_id": self.workflow_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": workflow_metrics["failed_tasks"],
                "success_rate": f"{success_rate:.1f}%",
                "total_execution_time": workflow_metrics["total_execution_time"],
                "average_task_time": workflow_metrics["average_task_time"],
            },
            "resources": resource_metrics,
            "deliverables": {
                "count": len(self.deliverables),
                "files": list(self.deliverables),
                "operations": workflow_metrics["file_operations"],
            },
            "task_metrics": self.get_all_task_metrics(),
            "audit_log": self.audit_log[-100:],  # Last 100 audit entries
        }

        return report

    async def save_metrics(self):
        """Save all metrics to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save workflow metrics
        workflow_file = self.metrics_dir / f"workflow_metrics_{timestamp}.json"
        workflow_file.write_text(json.dumps(self.get_workflow_metrics(), indent=2))

        # Save task metrics
        tasks_file = self.metrics_dir / f"task_metrics_{timestamp}.json"
        tasks_file.write_text(json.dumps(self.get_all_task_metrics(), indent=2))

        # Save completion report
        report_file = self.metrics_dir / f"completion_report_{timestamp}.json"
        report = self.generate_completion_report()
        report_file.write_text(json.dumps(report, indent=2))

        # Save audit log
        audit_file = self.metrics_dir / f"audit_log_{timestamp}.json"
        audit_file.write_text(json.dumps(self.audit_log, indent=2))

        logger.info(f"Saved metrics to {self.metrics_dir}")

    def get_progress_stats(self) -> Dict[str, Any]:
        """Get current progress statistics"""
        total = len(self.task_metrics)
        completed = sum(
            1 for m in self.task_metrics.values() if m.status == "completed"
        )
        failed = sum(1 for m in self.task_metrics.values() if m.status == "failed")
        running = sum(1 for m in self.task_metrics.values() if m.status == "running")
        pending = total - completed - failed - running

        progress = (completed / total * 100) if total > 0 else 0
        eta = self.calculate_eta(completed, total)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_percent": progress,
            "eta_seconds": eta,
            "elapsed_time": time.time() - self.workflow_start_time,
        }

    def finalize(self):
        """Finalize metrics collection"""
        self.workflow_metrics.end_time = time.time()
        self.workflow_metrics.total_execution_time = (
            self.workflow_metrics.end_time - self.workflow_metrics.start_time
        )

        # Final resource update
        self._update_resource_usage()

        # Final scan for deliverables
        self.scan_for_deliverables()

        logger.info(f"Finalized metrics for workflow {self.workflow_id}")
