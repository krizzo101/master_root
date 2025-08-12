"""
Workflow Orchestrator for Multi-Agent Systems

This module provides the core orchestration engine for managing complex
multi-agent workflows with support for sequential, parallel, and conditional
execution patterns.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from typing import Any

from ..agents.base_agent import BaseAgent
from ..common.types import (
    AgentId,
    Message,
    MessageType,
    WorkflowId,
    WorkflowStatus,
)
from ..communication.message_broker import MessageBroker


class ExecutionPattern(Enum):
    """Workflow execution patterns."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"


class WorkflowStep:
    """Represents a single step in a workflow."""

    def __init__(
        self,
        step_id: str,
        agent_id: AgentId,
        task_type: str,
        task_data: dict[str, Any],
        dependencies: list[str] | None = None,
        conditions: dict[str, Any] | None = None,
        timeout: float | None = None,
    ):
        self.step_id = step_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.task_data = task_data
        self.dependencies = dependencies or []
        self.conditions = conditions or {}
        self.timeout = timeout
        self.status = WorkflowStatus.PENDING
        self.result: Any | None = None
        self.error: str | None = None
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert step to dictionary representation."""
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "task_data": self.task_data,
            "dependencies": self.dependencies,
            "conditions": self.conditions,
            "timeout": self.timeout,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class Workflow:
    """Represents a complete workflow with multiple steps."""

    def __init__(
        self,
        workflow_id: WorkflowId,
        name: str,
        steps: list[WorkflowStep],
        execution_pattern: ExecutionPattern = ExecutionPattern.SEQUENTIAL,
        max_retries: int = 3,
        timeout: float | None = None,
    ):
        self.workflow_id = workflow_id
        self.name = name
        self.steps = {step.step_id: step for step in steps}
        self.execution_pattern = execution_pattern
        self.max_retries = max_retries
        self.timeout = timeout
        self.status = WorkflowStatus.PENDING
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.results: dict[str, Any] = {}
        self.errors: list[str] = []

    def get_ready_steps(self) -> list[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready_steps = []

        for step in self.steps.values():
            if step.status != WorkflowStatus.PENDING:
                continue

            # Check if all dependencies are completed
            dependencies_satisfied = all(
                self.steps[dep_id].status == WorkflowStatus.COMPLETED
                for dep_id in step.dependencies
                if dep_id in self.steps
            )

            if dependencies_satisfied:
                ready_steps.append(step)

        return ready_steps

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return all(
            step.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            for step in self.steps.values()
        )

    def has_failed_steps(self) -> bool:
        """Check if workflow has any failed steps."""
        return any(step.status == WorkflowStatus.FAILED for step in self.steps.values())


class WorkflowOrchestrator:
    """
    Core orchestration engine for multi-agent workflows.

    Manages the execution of complex workflows involving multiple agents,
    supporting various execution patterns and providing comprehensive
    monitoring and error handling capabilities.
    """

    def __init__(
        self, message_broker: MessageBroker, logger: logging.Logger | None = None
    ):
        """
        Initialize the workflow orchestrator.

        Args:
            message_broker: Message broker for agent communication
            logger: Optional logger instance
        """
        self.message_broker = message_broker
        self.logger = logger or logging.getLogger(__name__)

        # Agent registry
        self.agents: dict[AgentId, BaseAgent] = {}

        # Workflow management
        self.workflows: dict[WorkflowId, Workflow] = {}
        self.active_workflows: set[WorkflowId] = set()

        # Execution tracking
        self.execution_history: list[dict[str, Any]] = []
        self.metrics: dict[str, Any] = {
            "workflows_executed": 0,
            "workflows_successful": 0,
            "workflows_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
        }

        # Event handlers
        self.event_handlers: dict[str, list[Callable]] = {}

        self.logger.info("WorkflowOrchestrator initialized")

    async def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register
        """
        self.agents[agent.agent_id] = agent
        agent.set_message_broker(self.message_broker)
        await agent.start()
        self.logger.info(f"Registered agent: {agent.agent_id}")

    async def unregister_agent(self, agent_id: AgentId) -> None:
        """
        Unregister an agent from the orchestrator.

        Args:
            agent_id: ID of agent to unregister
        """
        if agent_id in self.agents:
            await self.agents[agent_id].stop()
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")

    def create_workflow(
        self,
        name: str,
        steps: list[dict[str, Any]],
        execution_pattern: ExecutionPattern = ExecutionPattern.SEQUENTIAL,
        max_retries: int = 3,
        timeout: float | None = None,
    ) -> WorkflowId:
        """
        Create a new workflow.

        Args:
            name: Workflow name
            steps: List of step definitions
            execution_pattern: Execution pattern for the workflow
            max_retries: Maximum retry attempts
            timeout: Overall workflow timeout

        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())

        # Convert step definitions to WorkflowStep objects
        workflow_steps = []
        for i, step_def in enumerate(steps):
            step = WorkflowStep(
                step_id=step_def.get("step_id", f"step_{i}"),
                agent_id=step_def["agent_id"],
                task_type=step_def["task_type"],
                task_data=step_def.get("task_data", {}),
                dependencies=step_def.get("dependencies", []),
                conditions=step_def.get("conditions", {}),
                timeout=step_def.get("timeout"),
            )
            workflow_steps.append(step)

        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            steps=workflow_steps,
            execution_pattern=execution_pattern,
            max_retries=max_retries,
            timeout=timeout,
        )

        self.workflows[workflow_id] = workflow
        self.logger.info(f"Created workflow: {workflow_id} ({name})")

        return workflow_id

    async def execute_workflow(self, workflow_id: WorkflowId) -> dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute

        Returns:
            Execution results
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflows[workflow_id]

        if workflow_id in self.active_workflows:
            raise ValueError(f"Workflow already active: {workflow_id}")

        self.active_workflows.add(workflow_id)
        workflow.status = WorkflowStatus.RUNNING
        workflow.start_time = datetime.now()

        self.logger.info(f"Starting workflow execution: {workflow_id}")

        try:
            # Execute based on pattern
            if workflow.execution_pattern == ExecutionPattern.SEQUENTIAL:
                await self._execute_sequential(workflow)
            elif workflow.execution_pattern == ExecutionPattern.PARALLEL:
                await self._execute_parallel(workflow)
            elif workflow.execution_pattern == ExecutionPattern.CONDITIONAL:
                await self._execute_conditional(workflow)
            elif workflow.execution_pattern == ExecutionPattern.PIPELINE:
                await self._execute_pipeline(workflow)

            # Determine final status
            if workflow.has_failed_steps():
                workflow.status = WorkflowStatus.FAILED
                self.metrics["workflows_failed"] += 1
            else:
                workflow.status = WorkflowStatus.COMPLETED
                self.metrics["workflows_successful"] += 1

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(str(e))
            self.metrics["workflows_failed"] += 1
            self.logger.error(f"Workflow execution failed: {workflow_id}, Error: {e}")

        finally:
            workflow.end_time = datetime.now()
            self.active_workflows.discard(workflow_id)

            # Update metrics
            execution_time = (workflow.end_time - workflow.start_time).total_seconds()
            self.metrics["workflows_executed"] += 1
            self.metrics["total_execution_time"] += execution_time
            self.metrics["average_execution_time"] = (
                self.metrics["total_execution_time"]
                / self.metrics["workflows_executed"]
            )

            # Record execution history
            self.execution_history.append(
                {
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "execution_time": execution_time,
                    "start_time": workflow.start_time.isoformat(),
                    "end_time": workflow.end_time.isoformat(),
                    "steps_completed": len(
                        [
                            s
                            for s in workflow.steps.values()
                            if s.status == WorkflowStatus.COMPLETED
                        ]
                    ),
                    "steps_failed": len(
                        [
                            s
                            for s in workflow.steps.values()
                            if s.status == WorkflowStatus.FAILED
                        ]
                    ),
                    "errors": workflow.errors,
                }
            )

            self.logger.info(f"Workflow execution completed: {workflow_id}")

        return self._get_workflow_results(workflow)

    async def _execute_sequential(self, workflow: Workflow) -> None:
        """Execute workflow steps sequentially."""
        remaining_steps = list(workflow.steps.values())

        while remaining_steps:
            ready_steps = [
                step
                for step in remaining_steps
                if all(
                    workflow.steps[dep].status == WorkflowStatus.COMPLETED
                    for dep in step.dependencies
                    if dep in workflow.steps
                )
            ]

            if not ready_steps:
                break

            # Execute one step at a time
            step = ready_steps[0]
            await self._execute_step(workflow, step)
            remaining_steps.remove(step)

    async def _execute_parallel(self, workflow: Workflow) -> None:
        """Execute workflow steps in parallel where possible."""
        remaining_steps = list(workflow.steps.values())

        while remaining_steps:
            ready_steps = [
                step
                for step in remaining_steps
                if all(
                    workflow.steps[dep].status == WorkflowStatus.COMPLETED
                    for dep in step.dependencies
                    if dep in workflow.steps
                )
            ]

            if not ready_steps:
                break

            # Execute all ready steps in parallel
            tasks = [self._execute_step(workflow, step) for step in ready_steps]
            await asyncio.gather(*tasks, return_exceptions=True)

            for step in ready_steps:
                remaining_steps.remove(step)

    async def _execute_conditional(self, workflow: Workflow) -> None:
        """Execute workflow with conditional logic."""
        remaining_steps = list(workflow.steps.values())

        while remaining_steps:
            ready_steps = []

            for step in remaining_steps:
                # Check dependencies
                deps_satisfied = all(
                    workflow.steps[dep].status == WorkflowStatus.COMPLETED
                    for dep in step.dependencies
                    if dep in workflow.steps
                )

                if not deps_satisfied:
                    continue

                # Check conditions
                if step.conditions:
                    conditions_met = await self._evaluate_conditions(
                        step.conditions, workflow
                    )
                    if not conditions_met:
                        step.status = WorkflowStatus.SKIPPED
                        remaining_steps.remove(step)
                        continue

                ready_steps.append(step)

            if not ready_steps:
                break

            # Execute ready steps
            tasks = [self._execute_step(workflow, step) for step in ready_steps]
            await asyncio.gather(*tasks, return_exceptions=True)

            for step in ready_steps:
                remaining_steps.remove(step)

    async def _execute_pipeline(self, workflow: Workflow) -> None:
        """Execute workflow as a pipeline (sequential with data flow)."""
        steps_by_order = sorted(
            workflow.steps.values(), key=lambda s: len(s.dependencies)
        )

        pipeline_data = {}

        for step in steps_by_order:
            # Pass data from previous steps
            step.task_data["pipeline_data"] = pipeline_data

            await self._execute_step(workflow, step)

            # Store result for next steps
            if step.result is not None:
                pipeline_data[step.step_id] = step.result

    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Execute a single workflow step."""
        if step.agent_id not in self.agents:
            step.status = WorkflowStatus.FAILED
            step.error = f"Agent not found: {step.agent_id}"
            return

        agent = self.agents[step.agent_id]
        step.status = WorkflowStatus.RUNNING
        step.start_time = datetime.now()

        try:
            # Create task message
            task_message = Message(
                message_id=str(uuid.uuid4()),
                sender_id="orchestrator",
                recipient_id=step.agent_id,
                message_type=MessageType.TASK,
                content={
                    "task_id": str(uuid.uuid4()),
                    "task_type": step.task_type,
                    "task_data": step.task_data,
                    "workflow_id": workflow.workflow_id,
                    "step_id": step.step_id,
                },
                timestamp=datetime.now(),
            )

            # Execute with timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    agent.execute_task(task_message.content), timeout=step.timeout
                )
            else:
                result = await agent.execute_task(task_message.content)

            step.result = result
            step.status = WorkflowStatus.COMPLETED

        except asyncio.TimeoutError:
            step.status = WorkflowStatus.FAILED
            step.error = "Task execution timeout"
        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.error = str(e)

        finally:
            step.end_time = datetime.now()

    async def _evaluate_conditions(
        self, conditions: dict[str, Any], workflow: Workflow
    ) -> bool:
        """Evaluate conditional expressions."""
        # Simple condition evaluation - can be extended
        for condition_type, condition_value in conditions.items():
            if condition_type == "step_result":
                step_id, expected_value = condition_value
                if step_id in workflow.steps:
                    step = workflow.steps[step_id]
                    if step.result != expected_value:
                        return False
            elif condition_type == "step_status":
                step_id, expected_status = condition_value
                if step_id in workflow.steps:
                    step = workflow.steps[step_id]
                    if step.status.value != expected_status:
                        return False

        return True

    def _get_workflow_results(self, workflow: Workflow) -> dict[str, Any]:
        """Get comprehensive workflow results."""
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "execution_pattern": workflow.execution_pattern.value,
            "start_time": (
                workflow.start_time.isoformat() if workflow.start_time else None
            ),
            "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
            "execution_time": (
                (workflow.end_time - workflow.start_time).total_seconds()
                if workflow.start_time and workflow.end_time
                else None
            ),
            "steps": {
                step_id: step.to_dict() for step_id, step in workflow.steps.items()
            },
            "results": {
                step_id: step.result
                for step_id, step in workflow.steps.items()
                if step.result is not None
            },
            "errors": workflow.errors,
        }

    def get_workflow_status(self, workflow_id: WorkflowId) -> dict[str, Any] | None:
        """Get current status of a workflow."""
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        return self._get_workflow_results(workflow)

    def get_active_workflows(self) -> list[WorkflowId]:
        """Get list of currently active workflows."""
        return list(self.active_workflows)

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics."""
        return self.metrics.copy()

    def get_execution_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get workflow execution history."""
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()

    async def cancel_workflow(self, workflow_id: WorkflowId) -> bool:
        """Cancel an active workflow."""
        if workflow_id not in self.active_workflows:
            return False

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELLED

        # Cancel running steps
        for step in workflow.steps.values():
            if step.status == WorkflowStatus.RUNNING:
                step.status = WorkflowStatus.CANCELLED

        self.active_workflows.discard(workflow_id)
        self.logger.info(f"Cancelled workflow: {workflow_id}")

        return True

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and all agents."""
        self.logger.info("Shutting down WorkflowOrchestrator")

        # Cancel active workflows
        for workflow_id in list(self.active_workflows):
            await self.cancel_workflow(workflow_id)

        # Stop all agents
        for agent_id in list(self.agents.keys()):
            await self.unregister_agent(agent_id)

        self.logger.info("WorkflowOrchestrator shutdown complete")
