"""
Workflow monitoring for OPSVI Core.

Provides execution tracking, metrics, and debugging capabilities.
"""

from datetime import datetime, timedelta
from typing import Any

from opsvi_foundation import ComponentError, get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class MonitoringError(ComponentError):
    """Raised when monitoring operations fail."""

    pass


class ExecutionMetrics(BaseModel):
    """Metrics for workflow execution."""

    workflow_id: str
    execution_id: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    total_duration: float
    step_durations: dict[str, float] = Field(default_factory=dict)
    memory_usage: float | None = None
    cpu_usage: float | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class ExecutionEvent(BaseModel):
    """Event during workflow execution."""

    execution_id: str
    event_type: str
    step_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkflowMonitor:
    """Monitor for workflow execution."""

    def __init__(self):
        """Initialize the workflow monitor."""
        self._executions: dict[str, dict[str, Any]] = {}
        self._events: list[ExecutionEvent] = []
        self._metrics: list[ExecutionMetrics] = []

    async def start_execution(self, execution_id: str, workflow_id: str) -> None:
        """
        Start monitoring an execution.

        Args:
            execution_id: Execution ID to monitor
            workflow_id: Workflow ID being executed
        """
        self._executions[execution_id] = {
            "workflow_id": workflow_id,
            "start_time": datetime.now(),
            "status": "running",
            "steps": {},
            "events": [],
        }

        event = ExecutionEvent(
            execution_id=execution_id,
            event_type="execution_started",
            data={"workflow_id": workflow_id},
        )
        self._events.append(event)

        logger.info(f"Started monitoring execution: {execution_id}")

    async def end_execution(
        self, execution_id: str, status: str, result: dict[str, Any]
    ) -> None:
        """
        End monitoring an execution.

        Args:
            execution_id: Execution ID to end monitoring
            status: Final execution status
            result: Execution result
        """
        if execution_id not in self._executions:
            return

        execution = self._executions[execution_id]
        execution["end_time"] = datetime.now()
        execution["status"] = status
        execution["result"] = result

        duration = (execution["end_time"] - execution["start_time"]).total_seconds()

        # Calculate metrics
        metrics = ExecutionMetrics(
            workflow_id=execution["workflow_id"],
            execution_id=execution_id,
            total_steps=len(execution["steps"]),
            completed_steps=sum(
                1
                for step in execution["steps"].values()
                if step.get("status") == "completed"
            ),
            failed_steps=sum(
                1
                for step in execution["steps"].values()
                if step.get("status") == "failed"
            ),
            skipped_steps=sum(
                1
                for step in execution["steps"].values()
                if step.get("status") == "skipped"
            ),
            total_duration=duration,
            step_durations={
                step_id: step.get("duration", 0)
                for step_id, step in execution["steps"].items()
            },
        )

        self._metrics.append(metrics)

        event = ExecutionEvent(
            execution_id=execution_id,
            event_type="execution_ended",
            data={"status": status, "duration": duration},
        )
        self._events.append(event)

        logger.info(f"Ended monitoring execution: {execution_id} ({status})")

    async def step_started(self, execution_id: str, step_id: str) -> None:
        """
        Record step start.

        Args:
            execution_id: Execution ID
            step_id: Step ID that started
        """
        if execution_id not in self._executions:
            return

        execution = self._executions[execution_id]
        execution["steps"][step_id] = {
            "start_time": datetime.now(),
            "status": "running",
        }

        event = ExecutionEvent(
            execution_id=execution_id, event_type="step_started", step_id=step_id
        )
        self._events.append(event)

        logger.debug(f"Step started: {execution_id}:{step_id}")

    async def step_completed(
        self, execution_id: str, step_id: str, output: dict[str, Any], duration: float
    ) -> None:
        """
        Record step completion.

        Args:
            execution_id: Execution ID
            step_id: Step ID that completed
            output: Step output
            duration: Step duration
        """
        if execution_id not in self._executions:
            return

        execution = self._executions[execution_id]
        if step_id in execution["steps"]:
            execution["steps"][step_id].update(
                {
                    "end_time": datetime.now(),
                    "status": "completed",
                    "output": output,
                    "duration": duration,
                }
            )

        event = ExecutionEvent(
            execution_id=execution_id,
            event_type="step_completed",
            step_id=step_id,
            data={"output": output, "duration": duration},
        )
        self._events.append(event)

        logger.debug(f"Step completed: {execution_id}:{step_id} ({duration:.2f}s)")

    async def step_failed(
        self, execution_id: str, step_id: str, error: str, duration: float
    ) -> None:
        """
        Record step failure.

        Args:
            execution_id: Execution ID
            step_id: Step ID that failed
            error: Error message
            duration: Step duration
        """
        if execution_id not in self._executions:
            return

        execution = self._executions[execution_id]
        if step_id in execution["steps"]:
            execution["steps"][step_id].update(
                {
                    "end_time": datetime.now(),
                    "status": "failed",
                    "error": error,
                    "duration": duration,
                }
            )

        event = ExecutionEvent(
            execution_id=execution_id,
            event_type="step_failed",
            step_id=step_id,
            data={"error": error, "duration": duration},
        )
        self._events.append(event)

        logger.warning(f"Step failed: {execution_id}:{step_id} - {error}")

    async def step_skipped(self, execution_id: str, step_id: str, reason: str) -> None:
        """
        Record step skip.

        Args:
            execution_id: Execution ID
            step_id: Step ID that was skipped
            reason: Skip reason
        """
        if execution_id not in self._executions:
            return

        execution = self._executions[execution_id]
        execution["steps"][step_id] = {
            "status": "skipped",
            "reason": reason,
            "timestamp": datetime.now(),
        }

        event = ExecutionEvent(
            execution_id=execution_id,
            event_type="step_skipped",
            step_id=step_id,
            data={"reason": reason},
        )
        self._events.append(event)

        logger.debug(f"Step skipped: {execution_id}:{step_id} - {reason}")

    async def get_execution_status(self, execution_id: str) -> dict[str, Any] | None:
        """
        Get execution status.

        Args:
            execution_id: Execution ID to check

        Returns:
            Execution status if found, None otherwise
        """
        return self._executions.get(execution_id)

    async def get_execution_events(self, execution_id: str) -> list[ExecutionEvent]:
        """
        Get events for an execution.

        Args:
            execution_id: Execution ID to get events for

        Returns:
            List of execution events
        """
        return [event for event in self._events if event.execution_id == execution_id]

    async def get_execution_metrics(self, execution_id: str) -> ExecutionMetrics | None:
        """
        Get metrics for an execution.

        Args:
            execution_id: Execution ID to get metrics for

        Returns:
            Execution metrics if found, None otherwise
        """
        for metrics in self._metrics:
            if metrics.execution_id == execution_id:
                return metrics
        return None

    async def list_executions(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        List monitored executions.

        Args:
            workflow_id: Filter by workflow ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of execution statuses
        """
        executions = list(self._executions.values())

        if workflow_id:
            executions = [e for e in executions if e.get("workflow_id") == workflow_id]

        if status:
            executions = [e for e in executions if e.get("status") == status]

        # Sort by start time (newest first)
        executions.sort(key=lambda x: x.get("start_time", datetime.min), reverse=True)

        if limit:
            executions = executions[:limit]

        return executions

    async def get_workflow_metrics(self, workflow_id: str) -> dict[str, Any]:
        """
        Get aggregated metrics for a workflow.

        Args:
            workflow_id: Workflow ID to get metrics for

        Returns:
            Aggregated workflow metrics
        """
        workflow_metrics = [m for m in self._metrics if m.workflow_id == workflow_id]

        if not workflow_metrics:
            return {}

        total_executions = len(workflow_metrics)
        successful_executions = sum(
            1 for m in workflow_metrics if m.completed_steps == m.total_steps
        )
        failed_executions = total_executions - successful_executions

        avg_duration = (
            sum(m.total_duration for m in workflow_metrics) / total_executions
        )
        avg_steps = sum(m.total_steps for m in workflow_metrics) / total_executions

        return {
            "workflow_id": workflow_id,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions
            if total_executions > 0
            else 0,
            "average_duration": avg_duration,
            "average_steps": avg_steps,
            "last_execution": max(m.created_at for m in workflow_metrics),
        }

    async def cleanup_old_executions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old execution data.

        Args:
            max_age_hours: Maximum age in hours to keep

        Returns:
            Number of executions cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0

        # Clean up executions
        old_execution_ids = [
            execution_id
            for execution_id, execution in self._executions.items()
            if execution.get("start_time", datetime.min) < cutoff_time
        ]

        for execution_id in old_execution_ids:
            del self._executions[execution_id]
            cleaned_count += 1

        # Clean up events
        self._events = [
            event for event in self._events if event.timestamp >= cutoff_time
        ]

        # Clean up metrics
        self._metrics = [
            metrics for metrics in self._metrics if metrics.created_at >= cutoff_time
        ]

        logger.info(f"Cleaned up {cleaned_count} old executions")
        return cleaned_count

    async def health_check(self) -> bool:
        """Perform health check on the monitor."""
        try:
            execution_count = len(self._executions)
            event_count = len(self._events)
            metrics_count = len(self._metrics)

            logger.debug(
                f"Monitor health check: {execution_count} executions, {event_count} events, {metrics_count} metrics"
            )
            return True

        except Exception as e:
            logger.error(f"Monitor health check failed: {e}")
            return False
