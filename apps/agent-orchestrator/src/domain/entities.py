#!/usr/bin/env python3
"""
Domain Entities following DDD principles

Entities have identity and lifecycle, with behavior encapsulated
within their boundaries. They maintain consistency through invariants.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .value_objects import (
    RetryPolicy,
    TaskMetrics,
    TaskPriority,
    TaskResult,
    TaskStatus,
    ValidationResult,
)


class AgentTask:
    """
    Domain entity representing an agent task with behavior.

    This entity encapsulates task logic, validation, execution,
    and retry mechanisms following DDD principles.
    """

    def __init__(
        self,
        task_id: str = None,
        task_type: str = "generic",
        prompt: str = "",
        context: Dict[str, Any] = None,
        dependencies: List[str] = None,
        priority: TaskPriority = None,
        retry_policy: RetryPolicy = None,
        validation_rules: List[Callable] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Initialize agent task entity"""
        self.task_id = task_id or str(uuid.uuid4())
        self.task_type = task_type
        self.prompt = prompt
        self.context = context or {}
        self.dependencies = dependencies or []
        self.priority = priority or TaskPriority.normal()
        self.retry_policy = retry_policy or RetryPolicy()
        self.validation_rules = validation_rules or []
        self.metadata = metadata or {}

        # State management
        self._status = TaskStatus.PENDING
        self._result: Optional[TaskResult] = None
        self._metrics: Optional[TaskMetrics] = None
        self._retry_count = 0
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

        # Execution context
        self._executor: Optional[Callable] = None
        self._validators: List[Callable] = []
        self._event_handlers: Dict[str, List[Callable]] = {}

        # Quality gates
        self._quality_gates: List[str] = []
        self._validation_required = True

    @property
    def status(self) -> TaskStatus:
        """Get current task status"""
        return self._status

    @property
    def result(self) -> Optional[TaskResult]:
        """Get task execution result"""
        return self._result

    @property
    def metrics(self) -> Optional[TaskMetrics]:
        """Get task execution metrics"""
        return self._metrics

    def validate(self) -> ValidationResult:
        """
        Validate task against business rules and invariants.

        Returns validation result with errors and warnings.
        """
        errors = []
        warnings = []

        # Check required fields
        if not self.task_type:
            errors.append("Task type is required")

        if not self.prompt and self.task_type != "noop":
            errors.append("Task prompt is required")

        # Check dependencies exist and are valid
        if self.dependencies:
            for dep_id in self.dependencies:
                if not isinstance(dep_id, str):
                    errors.append(f"Invalid dependency ID: {dep_id}")

        # Check priority constraints
        if self.priority.level < 0 or self.priority.level > 100:
            errors.append(f"Invalid priority level: {self.priority.level}")

        # Run custom validation rules
        for validator in self.validation_rules:
            try:
                result = validator(self)
                if isinstance(result, ValidationResult):
                    if not result.is_valid:
                        errors.extend(result.errors)
                    warnings.extend(result.warnings)
                elif result is False:
                    errors.append(f"Validation rule {validator.__name__} failed")
            except Exception as e:
                errors.append(f"Validation error: {str(e)}")

        # Check for circular dependencies
        if self.task_id in self.dependencies:
            errors.append("Task cannot depend on itself")

        # Warnings for best practices
        if len(self.dependencies) > 10:
            warnings.append(f"High number of dependencies ({len(self.dependencies)})")

        if self.priority.deadline and self.priority.deadline < datetime.utcnow():
            warnings.append("Task deadline is in the past")

        if errors:
            return ValidationResult.invalid(errors=errors, warnings=warnings)

        return ValidationResult.valid(warnings=warnings)

    async def execute(self, executor: Callable = None) -> TaskResult:
        """
        Execute the task with the provided executor.

        Handles validation, execution, metrics collection, and error handling.
        """
        # Use provided executor or stored one
        executor = executor or self._executor
        if not executor:
            return TaskResult.failure(
                error="No executor provided for task execution",
                error_type="ConfigurationError",
            )

        # Validate before execution
        if self._validation_required:
            validation = self.validate()
            if not validation.is_valid:
                self._status = TaskStatus.FAILED
                return TaskResult.failure(
                    error=f"Validation failed: {', '.join(validation.errors)}",
                    error_type="ValidationError",
                )

        # Update status and start tracking
        self._status = TaskStatus.RUNNING
        self._start_time = datetime.utcnow()
        await self._trigger_event("task_started")

        try:
            # Execute the task
            start_time = datetime.utcnow()

            if asyncio.iscoroutinefunction(executor):
                result_data = await executor(self)
            else:
                result_data = await asyncio.get_event_loop().run_in_executor(
                    None, executor, self
                )

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Create successful result
            self._result = TaskResult.success(
                data=result_data,
                execution_time=execution_time,
                metadata={"task_id": self.task_id, "task_type": self.task_type},
            )

            # Update metrics
            self._metrics = TaskMetrics(
                execution_time=execution_time, retry_count=self._retry_count
            )

            # Update status
            self._status = TaskStatus.COMPLETED
            self._end_time = datetime.utcnow()

            await self._trigger_event("task_completed")

            return self._result

        except asyncio.TimeoutError as e:
            self._status = TaskStatus.FAILED
            self._end_time = datetime.utcnow()
            self._result = TaskResult.timeout(
                error=str(e), retry_count=self._retry_count
            )
            await self._trigger_event("task_timeout")
            return self._result

        except Exception as e:
            self._status = TaskStatus.FAILED
            self._end_time = datetime.utcnow()

            # Determine error type
            error_type = type(e).__name__

            self._result = TaskResult.failure(
                error=str(e),
                error_type=error_type,
                retry_count=self._retry_count,
                execution_time=(datetime.utcnow() - self._start_time).total_seconds(),
            )

            await self._trigger_event("task_failed")
            return self._result

    async def retry(self, executor: Callable = None) -> TaskResult:
        """
        Retry task execution based on retry policy.

        Implements exponential backoff and respects retry limits.
        """
        # Check if retry is allowed
        if not self._result:
            return TaskResult.failure(
                error="Cannot retry task that hasn't been executed",
                error_type="InvalidStateError",
            )

        if not self._result.is_retryable():
            return self._result

        if not self.retry_policy.should_retry(
            self._result.error_type, self._retry_count + 1
        ):
            return TaskResult.failure(
                error=f"Max retry attempts reached ({self.retry_policy.max_attempts})",
                error_type="RetryLimitExceeded",
                retry_count=self._retry_count,
            )

        # Calculate and apply retry delay
        delay = self.retry_policy.calculate_delay(self._retry_count + 1)
        if delay > 0:
            await asyncio.sleep(delay)

        # Update retry count and status
        self._retry_count += 1
        self._status = TaskStatus.RETRYING

        await self._trigger_event("task_retrying")

        # Execute with retry
        return await self.execute(executor)

    def set_executor(self, executor: Callable) -> None:
        """Set the executor function for the task"""
        self._executor = executor

    def add_validator(self, validator: Callable) -> None:
        """Add a custom validator function"""
        self._validators.append(validator)

    def add_event_handler(self, event: str, handler: Callable) -> None:
        """Add an event handler for task lifecycle events"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def add_dependency(self, task_id: str) -> None:
        """Add a task dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id: str) -> None:
        """Remove a task dependency"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)

    def is_ready(self) -> bool:
        """Check if task is ready to execute (no pending dependencies)"""
        return self._status == TaskStatus.PENDING and not self.dependencies

    def is_complete(self) -> bool:
        """Check if task execution is complete"""
        return self._status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    def cancel(self) -> TaskResult:
        """Cancel task execution"""
        if self._status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return self._result

        self._status = TaskStatus.CANCELLED
        self._end_time = datetime.utcnow()
        self._result = TaskResult.cancelled(
            reason="Task cancelled by user", metadata={"task_id": self.task_id}
        )

        return self._result

    async def _trigger_event(self, event: str) -> None:
        """Trigger event handlers for given event"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self)
                    else:
                        handler(self)
                except Exception as e:
                    # Log but don't fail on event handler errors
                    print(f"Event handler error for {event}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "prompt": self.prompt,
            "context": self.context,
            "dependencies": self.dependencies,
            "priority": self.priority.to_dict(),
            "retry_policy": self.retry_policy.to_dict(),
            "status": self._status.value,
            "result": self._result.to_dict() if self._result else None,
            "metrics": self._metrics.to_dict() if self._metrics else None,
            "retry_count": self._retry_count,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """String representation of task"""
        return (
            f"AgentTask(id={self.task_id}, type={self.task_type}, "
            f"status={self._status.value}, retry_count={self._retry_count})"
        )
