"""Performance monitoring module for HECATON system."""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""

    task_id: str
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    memory_start: Optional[int] = None
    memory_peak: Optional[int] = None
    memory_end: Optional[int] = None
    token_usage: Optional[int] = None
    success: Optional[bool] = None
    error: Optional[str] = None

    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark task as complete and calculate final metrics."""
        self.end_time = time.perf_counter()
        self.execution_time = self.end_time - self.start_time
        self.success = success
        self.error = error
        process = psutil.Process(os.getpid())
        self.memory_end = process.memory_info().rss


class PerformanceMonitor:
    """Performance monitoring for HECATON system tasks."""

    def __init__(self):
        """Initialize the performance monitor."""
        self._active_tasks: Dict[str, TaskMetrics] = {}
        self._completed_tasks: Dict[str, TaskMetrics] = {}
        self._process = psutil.Process(os.getpid())
        self._monitor_start_time = time.perf_counter()
        self._monitor_start_memory = self._process.memory_info().rss

    def start_tracking(self, task_id: str) -> None:
        """Start tracking performance for a task.

        Args:
            task_id: Unique identifier for the task
        """
        if task_id in self._active_tasks:
            raise ValueError(f"Task {task_id} is already being tracked")

        start_time = time.perf_counter()
        memory_start = self._process.memory_info().rss

        self._active_tasks[task_id] = TaskMetrics(
            task_id=task_id,
            start_time=start_time,
            memory_start=memory_start,
            memory_peak=memory_start,
        )

    def end_tracking(
        self,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None,
        token_usage: Optional[int] = None,
    ) -> TaskMetrics:
        """End tracking for a task and record final metrics.

        Args:
            task_id: Unique identifier for the task
            success: Whether the task completed successfully
            error: Error message if task failed
            token_usage: Number of tokens used by the task

        Returns:
            TaskMetrics object with final metrics
        """
        if task_id not in self._active_tasks:
            raise ValueError(f"Task {task_id} is not being tracked")

        task_metrics = self._active_tasks.pop(task_id)
        task_metrics.complete(success=success, error=error)

        if token_usage is not None:
            task_metrics.token_usage = token_usage

        # Update peak memory if current memory is higher
        current_memory = self._process.memory_info().rss
        if current_memory > task_metrics.memory_peak:
            task_metrics.memory_peak = current_memory

        self._completed_tasks[task_id] = task_metrics
        return task_metrics

    def update_peak_memory(self, task_id: str) -> None:
        """Update peak memory for an active task.

        Args:
            task_id: Unique identifier for the task
        """
        if task_id in self._active_tasks:
            current_memory = self._process.memory_info().rss
            if current_memory > self._active_tasks[task_id].memory_peak:
                self._active_tasks[task_id].memory_peak = current_memory

    def get_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for a specific task.

        Args:
            task_id: Unique identifier for the task

        Returns:
            TaskMetrics object or None if task not found
        """
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        return self._completed_tasks.get(task_id)

    def get_all_metrics(self) -> Dict[str, TaskMetrics]:
        """Get metrics for all tasks.

        Returns:
            Dictionary of all task metrics (active and completed)
        """
        all_metrics = {}
        all_metrics.update(self._active_tasks)
        all_metrics.update(self._completed_tasks)
        return all_metrics

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate aggregate statistics from all completed tasks.

        Returns:
            Dictionary containing statistical metrics
        """
        if not self._completed_tasks:
            return {
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "min_execution_time": 0.0,
                "max_execution_time": 0.0,
                "total_execution_time": 0.0,
                "avg_memory_usage": 0.0,
                "peak_memory": 0.0,
                "total_token_usage": 0,
            }

        completed_list = list(self._completed_tasks.values())
        successful_tasks = [t for t in completed_list if t.success]
        failed_tasks = [t for t in completed_list if not t.success]

        execution_times = [t.execution_time for t in completed_list if t.execution_time is not None]
        memory_peaks = [t.memory_peak for t in completed_list if t.memory_peak is not None]
        token_usages = [t.token_usage for t in completed_list if t.token_usage is not None]

        statistics = {
            "total_tasks": len(completed_list),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(completed_list) if completed_list else 0.0,
            "avg_execution_time": sum(execution_times) / len(execution_times)
            if execution_times
            else 0.0,
            "min_execution_time": min(execution_times) if execution_times else 0.0,
            "max_execution_time": max(execution_times) if execution_times else 0.0,
            "total_execution_time": sum(execution_times) if execution_times else 0.0,
            "avg_memory_usage": sum(memory_peaks) / len(memory_peaks) if memory_peaks else 0.0,
            "peak_memory": max(memory_peaks) if memory_peaks else 0.0,
            "total_token_usage": sum(token_usages) if token_usages else 0,
        }

        # Add monitor uptime
        statistics["monitor_uptime"] = time.perf_counter() - self._monitor_start_time
        statistics["current_memory"] = self._process.memory_info().rss
        statistics["memory_growth"] = statistics["current_memory"] - self._monitor_start_memory

        return statistics

    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export all metrics and statistics as JSON.

        Args:
            filepath: Optional path to save the JSON file

        Returns:
            JSON string of metrics and statistics
        """
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.calculate_statistics(),
            "active_tasks": {
                task_id: {
                    "task_id": metrics.task_id,
                    "start_time": metrics.start_time,
                    "memory_start": metrics.memory_start,
                    "memory_peak": metrics.memory_peak,
                    "elapsed_time": time.perf_counter() - metrics.start_time,
                }
                for task_id, metrics in self._active_tasks.items()
            },
            "completed_tasks": {
                task_id: asdict(metrics) for task_id, metrics in self._completed_tasks.items()
            },
        }

        json_str = json.dumps(export_data, indent=2, default=str)

        if filepath:
            with open(filepath, "w") as f:
                f.write(json_str)

        return json_str

    def reset(self) -> None:
        """Reset all metrics and clear history."""
        self._active_tasks.clear()
        self._completed_tasks.clear()
        self._monitor_start_time = time.perf_counter()
        self._monitor_start_memory = self._process.memory_info().rss

    def get_active_tasks(self) -> List[str]:
        """Get list of currently active task IDs.

        Returns:
            List of active task IDs
        """
        return list(self._active_tasks.keys())

    def get_completed_tasks(self) -> List[str]:
        """Get list of completed task IDs.

        Returns:
            List of completed task IDs
        """
        return list(self._completed_tasks.keys())
