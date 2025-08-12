"""
Performance monitoring for Claude Code jobs
"""

from datetime import datetime
from typing import Dict, Optional, Any

from .models import PerformanceMetrics
from .parallel_logger import logger


class PerformanceMonitor:
    """Tracks and reports performance metrics for Claude Code jobs"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}

    def create_metrics(self, job_id: str) -> PerformanceMetrics:
        """Create new performance metrics for a job"""
        metrics = PerformanceMetrics(
            job_id=job_id, start_time=datetime.now(), error_count=0
        )
        self.metrics[job_id] = metrics
        return metrics

    def update_metrics(
        self, job_id: str, event: str, data: Optional[Any] = None
    ) -> None:
        """Update metrics for a specific event"""
        metrics = self.metrics.get(job_id)
        if not metrics:
            return

        now = datetime.now()

        if event == "spawned":
            metrics.spawn_time = now
            metrics.spawn_delay = (now - metrics.start_time).total_seconds()

        elif event == "first_output":
            metrics.first_output_time = now

        elif event == "completed":
            metrics.completion_time = now
            metrics.total_duration = (now - metrics.start_time).total_seconds()
            if metrics.first_output_time:
                metrics.execution_duration = (
                    now - metrics.first_output_time
                ).total_seconds()

        elif event == "error":
            metrics.error_count += 1

        elif event == "output_size":
            metrics.output_size = data

        logger.log_performance(job_id, event, metrics)

    def get_metrics(self, job_id: str) -> Optional[PerformanceMetrics]:
        """Get metrics for a specific job"""
        return self.metrics.get(job_id)

    def cleanup_metrics(self, job_id: str) -> None:
        """Remove metrics for a completed job"""
        if job_id in self.metrics:
            del self.metrics[job_id]

    def get_average_duration(self) -> float:
        """Calculate average job duration"""
        completed_metrics = [
            m for m in self.metrics.values() if m.total_duration is not None
        ]

        if not completed_metrics:
            return 0.0

        total = sum(m.total_duration for m in completed_metrics)
        return total / len(completed_metrics)

    def get_parallel_efficiency(self, active_count: int) -> float:
        """Calculate parallel execution efficiency"""
        if active_count <= 1:
            return 1.0

        # Simple efficiency metric based on active job count
        # Could be enhanced with actual throughput measurements
        return min(active_count * 0.85, active_count)
