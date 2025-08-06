"""
Workflow execution engine for OPSVI Core.

Provides workflow execution, state management, and error handling.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field

from .definition import WorkflowDefinition
from .state import StateManager
from .steps import StepExecutor

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowExecutionError(ComponentError):
    """Raised when workflow execution fails."""

    pass


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""

    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: float | None = Field(
        default=None, description="Execution timeout in seconds"
    )
    parallel_execution: bool = Field(
        default=False, description="Enable parallel step execution"
    )
    error_handling: str = Field(default="stop", description="Error handling strategy")
    state_persistence: bool = Field(
        default=True, description="Enable state persistence"
    )


class WorkflowContext(BaseModel):
    """Context for workflow execution."""

    workflow_id: str
    execution_id: str
    start_time: datetime
    config: WorkflowConfig
    variables: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Result of workflow execution."""

    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: datetime | None = None
    duration: float | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    steps_completed: int = 0
    total_steps: int = 0


class WorkflowEngine(BaseComponent):
    """
    Main workflow execution engine.

    Provides workflow execution, state management, and error handling.
    """

    def __init__(self, config: WorkflowConfig, **kwargs):
        """Initialize the workflow engine."""
        super().__init__(**kwargs)
        self.config = config
        self.active_executions: dict[str, WorkflowContext] = {}
        self.execution_history: list[WorkflowResult] = []

    async def execute_workflow(
        self,
        workflow_definition: "WorkflowDefinition",
        variables: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> WorkflowResult:
        """
        Execute a workflow.

        Args:
            workflow_definition: Workflow definition to execute
            variables: Input variables for the workflow
            execution_id: Optional execution ID

        Returns:
            Workflow execution result

        Raises:
            WorkflowExecutionError: If execution fails
        """
        if execution_id is None:
            execution_id = f"{workflow_definition.id}_{datetime.now().isoformat()}"

        context = WorkflowContext(
            workflow_id=workflow_definition.id,
            execution_id=execution_id,
            start_time=datetime.now(),
            config=self.config,
            variables=variables or {},
        )

        self.active_executions[execution_id] = context

        try:
            logger.info(f"Starting workflow execution: {execution_id}")

            # Initialize workflow state
            state_manager = StateManager()
            await state_manager.initialize(workflow_definition, context)

            # Execute workflow steps
            step_executor = StepExecutor(self.config)
            result = await step_executor.execute(
                workflow_definition, context, state_manager
            )

            # Update execution history
            self.execution_history.append(result)

            logger.info(f"Workflow execution completed: {execution_id}")
            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id}, error: {e}")
            result = WorkflowResult(
                workflow_id=workflow_definition.id,
                execution_id=execution_id,
                status=WorkflowStatus.FAILED,
                start_time=context.start_time,
                end_time=datetime.now(),
                error=str(e),
                total_steps=len(workflow_definition.steps),
            )
            self.execution_history.append(result)
            raise WorkflowExecutionError(f"Workflow execution failed: {e}") from e

        finally:
            # Clean up active execution
            self.active_executions.pop(execution_id, None)

    async def cancel_workflow(self, execution_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            execution_id: Execution ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        if execution_id not in self.active_executions:
            return False

        logger.info(f"Cancelling workflow execution: {execution_id}")

        # Update result status
        for result in self.execution_history:
            if result.execution_id == execution_id:
                result.status = WorkflowStatus.CANCELLED
                result.end_time = datetime.now()
                break

        # Remove from active executions
        self.active_executions.pop(execution_id)
        return True

    async def get_execution_status(self, execution_id: str) -> WorkflowResult | None:
        """
        Get execution status.

        Args:
            execution_id: Execution ID to check

        Returns:
            Workflow result if found, None otherwise
        """
        # Check active executions
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            return WorkflowResult(
                workflow_id=context.workflow_id,
                execution_id=execution_id,
                status=WorkflowStatus.RUNNING,
                start_time=context.start_time,
                total_steps=0,  # Would need to get from definition
            )

        # Check execution history
        for result in self.execution_history:
            if result.execution_id == execution_id:
                return result

        return None

    async def list_executions(
        self,
        workflow_id: str | None = None,
        status: WorkflowStatus | None = None,
        limit: int | None = None,
    ) -> list[WorkflowResult]:
        """
        List workflow executions.

        Args:
            workflow_id: Filter by workflow ID
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of workflow results
        """
        results = []

        # Add active executions
        for context in self.active_executions.values():
            if workflow_id and context.workflow_id != workflow_id:
                continue
            results.append(
                WorkflowResult(
                    workflow_id=context.workflow_id,
                    execution_id=context.execution_id,
                    status=WorkflowStatus.RUNNING,
                    start_time=context.start_time,
                    total_steps=0,
                )
            )

        # Add completed executions
        for result in self.execution_history:
            if workflow_id and result.workflow_id != workflow_id:
                continue
            if status and result.status != status:
                continue
            results.append(result)

        # Sort by start time (newest first)
        results.sort(key=lambda x: x.start_time, reverse=True)

        # Apply limit
        if limit:
            results = results[:limit]

        return results

    async def health_check(self) -> bool:
        """Perform health check on the workflow engine."""
        try:
            # Check if engine is responsive
            active_count = len(self.active_executions)
            history_count = len(self.execution_history)

            logger.debug(
                f"Workflow engine health check: {active_count} active, {history_count} in history"
            )
            return True

        except Exception as e:
            logger.error(f"Workflow engine health check failed: {e}")
            return False
