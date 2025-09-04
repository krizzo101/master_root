"""
Orchestrator Integration Module
Seamlessly integrates monitoring with existing GenericOrchestrator
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

try:
    from ..generic_orchestrator import AgentTask, GenericOrchestrator
except ImportError:
    # Handle different import paths
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from generic_orchestrator import AgentTask, GenericOrchestrator

from .metrics_collector import MetricsCollector, MetricType, get_global_collector

logger = logging.getLogger(__name__)


class MonitoredGenericOrchestrator(GenericOrchestrator):
    """Enhanced GenericOrchestrator with integrated monitoring"""

    def __init__(
        self,
        output_dir,
        tokens: Optional[List[str]] = None,
        max_parallel: int = 5,
        collector: Optional[MetricsCollector] = None,
    ):
        super().__init__(output_dir, tokens, max_parallel)

        self.collector = collector or get_global_collector()
        self.monitor_enabled = True

        logger.info("MonitoredGenericOrchestrator initialized with monitoring enabled")

    def enable_monitoring(self, enabled: bool = True) -> None:
        """Enable or disable monitoring collection"""
        self.monitor_enabled = enabled
        logger.info("Monitoring %s", "enabled" if enabled else "disabled")

    async def execute_batch(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute tasks with monitoring integration"""
        if self.monitor_enabled:
            # Record batch start
            for task in tasks:
                self.collector.record_task_started(task.task_id)

        # Call parent implementation
        results = await super().execute_batch(tasks)

        if self.monitor_enabled:
            # Record results
            for i, (task, result) in enumerate(zip(tasks, results)):
                if result.get("is_error", False):
                    self.collector.record_task_failed(
                        task.task_id,
                        error=result.get("error", "Unknown error"),
                        metadata={"task_type": task.task_type},
                    )
                else:
                    execution_time = result.get("duration_ms", 0) / 1000.0
                    self.collector.record_task_completed(
                        task.task_id,
                        execution_time=execution_time,
                        metadata={
                            "task_type": task.task_type,
                            "duration_ms": result.get("duration_ms", 0),
                            "num_turns": result.get("num_turns", 0),
                        },
                    )

                # Record token usage if available
                usage = result.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    if input_tokens > 0 or output_tokens > 0:
                        self.collector.record_token_usage(
                            agent_id=f"agent_{i}",
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            metadata={
                                "task_id": task.task_id,
                                "task_type": task.task_type,
                            },
                        )

        return results

    async def execute_with_dependencies(self, tasks: List[AgentTask]) -> List[Dict]:
        """Execute tasks with dependency resolution and monitoring"""
        if self.monitor_enabled:
            # Record execution start
            start_time = time.time()
            self.collector.record_metric(
                self.collector.Metric(
                    metric_type=MetricType.QUEUE_DEPTH,
                    value=len(tasks),
                    metadata={"execution_type": "dependency_resolved"},
                )
            )

        # Call parent implementation
        results = await super().execute_with_dependencies(tasks)

        if self.monitor_enabled:
            # Record execution completion
            end_time = time.time()
            total_time = end_time - start_time

            self.collector.record_metric(
                self.collector.Metric(
                    metric_type=MetricType.THROUGHPUT,
                    value=len(tasks) / max(total_time / 60, 1),  # tasks per minute
                    metadata={
                        "total_tasks": len(tasks),
                        "total_time_seconds": total_time,
                        "execution_type": "dependency_resolved",
                    },
                )
            )

        return results


def integrate_monitoring_with_orchestrator(
    orchestrator: GenericOrchestrator, collector: Optional[MetricsCollector] = None
) -> None:
    """Integrate monitoring into an existing orchestrator instance"""
    collector = collector or get_global_collector()

    # Store original methods
    original_execute_batch = orchestrator.execute_batch
    original_execute_with_dependencies = orchestrator.execute_with_dependencies

    async def monitored_execute_batch(tasks: List[AgentTask]) -> List[Dict]:
        """Wrapper for execute_batch with monitoring"""
        # Record task starts
        for task in tasks:
            collector.record_task_started(task.task_id)

        # Execute tasks
        results = await original_execute_batch(tasks)

        # Record results
        for i, (task, result) in enumerate(zip(tasks, results)):
            if result.get("is_error", False):
                collector.record_task_failed(
                    task.task_id,
                    error=result.get("error", "Unknown error"),
                    metadata={"task_type": task.task_type},
                )
            else:
                execution_time = result.get("duration_ms", 0) / 1000.0
                collector.record_task_completed(
                    task.task_id,
                    execution_time=execution_time,
                    metadata={
                        "task_type": task.task_type,
                        "duration_ms": result.get("duration_ms", 0),
                    },
                )

            # Record token usage
            usage = result.get("usage", {})
            if usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                if input_tokens > 0 or output_tokens > 0:
                    collector.record_token_usage(
                        agent_id=f"agent_{i}",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        metadata={"task_id": task.task_id},
                    )

        return results

    async def monitored_execute_with_dependencies(tasks: List[AgentTask]) -> List[Dict]:
        """Wrapper for execute_with_dependencies with monitoring"""
        start_time = time.time()

        # Record queue depth
        collector.record_metric(
            collector.Metric(
                metric_type=MetricType.QUEUE_DEPTH,
                value=len(tasks),
                metadata={"execution_type": "dependency_resolved"},
            )
        )

        # Execute tasks
        results = await original_execute_with_dependencies(tasks)

        # Record throughput
        end_time = time.time()
        total_time = end_time - start_time
        collector.record_metric(
            collector.Metric(
                metric_type=MetricType.THROUGHPUT,
                value=len(tasks) / max(total_time / 60, 1),
                metadata={"total_tasks": len(tasks), "total_time_seconds": total_time},
            )
        )

        return results

    # Replace methods
    orchestrator.execute_batch = monitored_execute_batch
    orchestrator.execute_with_dependencies = monitored_execute_with_dependencies

    # Add monitoring control
    orchestrator.monitoring_collector = collector

    logger.info("Monitoring integration completed for orchestrator")


class MonitoringContextManager:
    """Context manager for automatic monitoring setup and cleanup"""

    def __init__(
        self,
        orchestrator: Optional[GenericOrchestrator] = None,
        collector: Optional[MetricsCollector] = None,
    ):
        self.orchestrator = orchestrator
        self.collector = collector or get_global_collector()
        self.original_methods = {}

    async def __aenter__(self):
        if self.orchestrator:
            integrate_monitoring_with_orchestrator(self.orchestrator, self.collector)
        return self.collector

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup is automatic when the collector goes out of scope
        pass


# Convenience functions for common integration patterns
async def run_monitored_orchestrator_batch(
    tasks: List[AgentTask],
    output_dir,  # Can be str or Path
    tokens: Optional[List[str]] = None,
    max_parallel: int = 5,
) -> tuple[List[Dict], dict]:
    """Run orchestrator batch with monitoring and return results + metrics summary"""
    collector = get_global_collector()
    orchestrator = MonitoredGenericOrchestrator(
        output_dir=output_dir,
        tokens=tokens,
        max_parallel=max_parallel,
        collector=collector,
    )

    results = await orchestrator.execute_batch(tasks)
    summary = collector.get_summary()

    return results, summary.__dict__


async def run_monitored_orchestrator_with_dependencies(
    tasks: List[AgentTask],
    output_dir: str,
    tokens: Optional[List[str]] = None,
    max_parallel: int = 5,
) -> tuple[List[Dict], dict]:
    """Run orchestrator with dependencies and monitoring, return results + metrics summary"""
    collector = get_global_collector()
    orchestrator = MonitoredGenericOrchestrator(
        output_dir=output_dir,
        tokens=tokens,
        max_parallel=max_parallel,
        collector=collector,
    )

    results = await orchestrator.execute_with_dependencies(tasks)
    summary = collector.get_summary()

    return results, summary.__dict__
