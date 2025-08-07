"""
Workflow step execution for OPSVI Core.

Provides step execution, retry logic, and error handling.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from opsvi_foundation import ComponentError, get_logger
from pydantic import BaseModel, Field

from .definition import StepDefinition, WorkflowDefinition
from .engine import WorkflowConfig, WorkflowContext, WorkflowResult
from .state import StateManager

logger = get_logger(__name__)


class StepExecutionError(ComponentError):
    """Raised when step execution fails."""

    pass


class StepResult(BaseModel):
    """Result of step execution."""

    step_id: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration: float | None = None
    retry_count: int = 0


class WorkflowStep(ABC):
    """Abstract base class for workflow steps."""

    def __init__(self, step_id: str, name: str, **kwargs):
        """Initialize the workflow step."""
        self.step_id = step_id
        self.name = name
        self.config = kwargs

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the step.

        Args:
            context: Execution context with variables and state

        Returns:
            Step output

        Raises:
            StepExecutionError: If execution fails
        """
        pass

    async def validate(self, context: dict[str, Any]) -> bool:
        """
        Validate step before execution.

        Args:
            context: Execution context

        Returns:
            True if valid, False otherwise
        """
        return True

    @abstractmethod
    async def cleanup(self, context: dict[str, Any]) -> None:
        """
        Clean up after step execution.

        Args:
            context: Execution context
        """
        pass


class TaskStep(WorkflowStep):
    """Task step that executes a specific action."""

    def __init__(
        self,
        step_id: str,
        name: str,
        action: str,
        parameters: dict[str, Any] = None,
        **kwargs,
    ):
        """Initialize the task step."""
        super().__init__(step_id, name, **kwargs)
        self.action = action
        self.parameters = parameters or {}

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the task step."""
        logger.info(f"Executing task step: {self.step_id} - {self.action}")

        # Merge parameters with context variables
        params = self.parameters.copy()
        params.update(context.get("variables", {}))

        # Execute action (placeholder implementation)
        # In a real implementation, this would dispatch to action handlers
        result = {
            "action": self.action,
            "parameters": params,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Task step completed: {self.step_id}")
        return result


class ConditionStep(WorkflowStep):
    """Conditional step that evaluates conditions."""

    def __init__(self, step_id: str, name: str, condition: str, **kwargs):
        """Initialize the condition step."""
        super().__init__(step_id, name, **kwargs)
        self.condition = condition

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the condition step."""
        logger.info(f"Evaluating condition step: {self.step_id}")

        # Evaluate condition (placeholder implementation)
        # In a real implementation, this would use a condition evaluator
        variables = context.get("variables", {})

        # Simple condition evaluation (placeholder)
        result = {
            "condition": self.condition,
            "variables": variables,
            "evaluated": True,  # Placeholder
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Condition step completed: {self.step_id}")
        return result


class WaitStep(WorkflowStep):
    """Wait step that pauses execution."""

    def __init__(self, step_id: str, name: str, duration: float, **kwargs):
        """Initialize the wait step."""
        super().__init__(step_id, name, **kwargs)
        self.duration = duration

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the wait step."""
        logger.info(f"Executing wait step: {self.step_id} for {self.duration}s")

        await asyncio.sleep(self.duration)

        result = {
            "duration": self.duration,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"Wait step completed: {self.step_id}")
        return result


class StepExecutor:
    """Executor for workflow steps."""

    def __init__(self, config: "WorkflowConfig"):
        """Initialize the step executor."""
        self.config = config
        self.step_registry: dict[str, type] = {
            "task": TaskStep,
            "condition": ConditionStep,
            "wait": WaitStep,
        }

    async def execute(
        self,
        workflow_definition: "WorkflowDefinition",
        context: "WorkflowContext",
        state_manager: "StateManager",
    ) -> "WorkflowResult":
        """
        Execute workflow steps.

        Args:
            workflow_definition: Workflow definition
            context: Execution context
            state_manager: State manager

        Returns:
            Workflow execution result
        """
        from .engine import WorkflowResult, WorkflowStatus

        start_time = datetime.now()
        steps_completed = 0
        total_steps = len(workflow_definition.steps)

        try:
            # Execute steps in dependency order
            execution_order = self._determine_execution_order(workflow_definition)

            for step_id in execution_order:
                step_def = workflow_definition.get_step(step_id)
                if not step_def:
                    continue

                # Execute step
                step_result = await self._execute_step(step_def, context, state_manager)

                if step_result.status == "completed":
                    steps_completed += 1
                elif step_result.status == "failed":
                    # Handle step failure based on config
                    if self.config.error_handling == "stop":
                        raise StepExecutionError(
                            f"Step {step_id} failed: {step_result.error}"
                        )
                    # Other error handling strategies could be implemented here

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return WorkflowResult(
                workflow_id=workflow_definition.id,
                execution_id=context.execution_id,
                status=WorkflowStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                steps_completed=steps_completed,
                total_steps=total_steps,
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return WorkflowResult(
                workflow_id=workflow_definition.id,
                execution_id=context.execution_id,
                status=WorkflowStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                error=str(e),
                steps_completed=steps_completed,
                total_steps=total_steps,
            )

    async def _execute_step(
        self,
        step_def: "StepDefinition",
        context: "WorkflowContext",
        state_manager: "StateManager",
    ) -> StepResult:
        """
        Execute a single step.

        Args:
            step_def: Step definition
            context: Execution context
            state_manager: State manager

        Returns:
            Step execution result
        """
        start_time = datetime.now()
        retry_count = 0
        max_retries = (
            step_def.retry_policy.get("max_retries", self.config.max_retries)
            if step_def.retry_policy
            else self.config.max_retries
        )

        while retry_count <= max_retries:
            try:
                # Create step instance
                step_class = self.step_registry.get(step_def.type)
                if not step_class:
                    raise StepExecutionError(f"Unknown step type: {step_def.type}")

                step = step_class(
                    step_id=step_def.id, name=step_def.name, **step_def.parameters
                )

                # Prepare execution context
                exec_context = {
                    "variables": context.variables,
                    "metadata": context.metadata,
                    "step_id": step_def.id,
                    "execution_id": context.execution_id,
                }

                # Validate step
                if not await step.validate(exec_context):
                    raise StepExecutionError(f"Step validation failed: {step_def.id}")

                # Execute step
                output = await step.execute(exec_context)

                # Update state
                await state_manager.update_step_state(
                    context.execution_id,
                    step_def.id,
                    {
                        "status": "completed",
                        "output": output,
                        "start_time": start_time.isoformat(),
                        "end_time": datetime.now().isoformat(),
                    },
                )

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                return StepResult(
                    step_id=step_def.id,
                    status="completed",
                    output=output,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    retry_count=retry_count,
                )

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Step {step_def.id} failed (attempt {retry_count}/{max_retries + 1}): {e}"
                )

                if retry_count <= max_retries:
                    # Wait before retry
                    retry_delay = (
                        step_def.retry_policy.get("delay", 1.0)
                        if step_def.retry_policy
                        else 1.0
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    # Max retries exceeded
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    # Update state
                    await state_manager.update_step_state(
                        context.execution_id,
                        step_def.id,
                        {
                            "status": "failed",
                            "error": str(e),
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "retry_count": retry_count,
                        },
                    )

                    return StepResult(
                        step_id=step_def.id,
                        status="failed",
                        error=str(e),
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        retry_count=retry_count,
                    )

    def _determine_execution_order(
        self, workflow_definition: "WorkflowDefinition"
    ) -> list[str]:
        """
        Determine the order of step execution based on dependencies.

        Args:
            workflow_definition: Workflow definition

        Returns:
            List of step IDs in execution order
        """
        # Topological sort for dependency resolution
        steps = workflow_definition.steps
        step_ids = [step.id for step in steps]

        # Build dependency graph
        graph = {step_id: [] for step_id in step_ids}
        in_degree = {step_id: 0 for step_id in step_ids}

        for step in steps:
            for dep in step.depends_on:
                if dep in step_ids:
                    graph[dep].append(step.id)
                    in_degree[step.id] += 1

        # Topological sort
        execution_order = []
        queue = [step_id for step_id in step_ids if in_degree[step_id] == 0]

        while queue:
            current = queue.pop(0)
            execution_order.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for cycles
        if len(execution_order) != len(step_ids):
            raise StepExecutionError("Circular dependencies detected in workflow steps")

        return execution_order
