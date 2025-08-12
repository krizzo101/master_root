"""
Workflow Coordination Interface

Provides integration between the workflow engine and agent coordination layer
for the AI-Powered Development Workflow System.

This module enables workflows to interact with the agent registry and message bus,
allowing workflows to be executed by agents and coordinate multi-agent tasks.

Author: ST-Agent-4 (Workflow Developer)
Created: 2025-01-27
Assignment: Integration of workflow engine with agent coordination layer
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .agent_registry import AgentRegistry, get_registry, RegistrationStatus
from .message_bus import MessageBus, get_message_bus, MessagePriority, SubscriptionType
from ..agents.base_agent import AgentMessage, MessageType


class WorkflowExecutionStatus(Enum):
    """Workflow execution status in multi-agent context."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    WAITING_FOR_AGENTS = "waiting_for_agents"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapabilityMatch(Enum):
    """Agent capability matching levels."""

    EXACT = "exact"
    PARTIAL = "partial"
    FALLBACK = "fallback"
    NO_MATCH = "no_match"


@dataclass
class WorkflowAgentAssignment:
    """Assignment of workflow step to agent."""

    step_id: str
    agent_id: str
    capability_match: AgentCapabilityMatch
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "assigned"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class WorkflowCoordinationContext:
    """Context for workflow coordination across agents."""

    workflow_id: str
    workflow_definition: Dict[str, Any]
    execution_status: WorkflowExecutionStatus
    agent_assignments: List[WorkflowAgentAssignment] = field(default_factory=list)
    coordination_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowCoordinator:
    """
    Coordinator for integrating workflow engine with agent coordination layer.

    This class bridges the workflow engine with the agent registry and message bus,
    enabling workflows to be executed across multiple agents in a coordinated manner.
    """

    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        message_bus: Optional[MessageBus] = None,
    ):
        """
        Initialize workflow coordinator.

        Args:
            agent_registry: Agent registry instance (uses global if None)
            message_bus: Message bus instance (uses global if None)
        """
        self.logger = logging.getLogger(__name__)
        self.agent_registry = agent_registry or get_registry()
        self.message_bus = message_bus or get_message_bus()

        # Workflow coordination state
        self._active_workflows: Dict[str, WorkflowCoordinationContext] = {}
        self._step_handlers: Dict[str, Callable] = {}
        self._running = False

        # Subscribe to workflow-related messages
        self._subscription_id = None

        self.logger.info("Workflow coordinator initialized")

    async def start(self) -> None:
        """Start workflow coordination services."""
        if self._running:
            return

        self._running = True

        # Subscribe to workflow messages
        self._subscription_id = self.message_bus.subscribe(
            subscriber_id="workflow_coordinator",
            subscription_type=SubscriptionType.TYPE,
            handler=self._handle_workflow_message,
            filter_criteria={"message_type": MessageType.TASK_REQUEST},
        )

        self.logger.info("Workflow coordinator started")

    async def stop(self) -> None:
        """Stop workflow coordination services."""
        if not self._running:
            return

        self._running = False

        # Unsubscribe from messages
        if self._subscription_id:
            self.message_bus.unsubscribe("workflow_coordinator", SubscriptionType.TYPE)

        # Cancel active workflows
        for workflow_id in list(self._active_workflows.keys()):
            await self.cancel_workflow(workflow_id)

        self.logger.info("Workflow coordinator stopped")

    async def execute_workflow(
        self,
        workflow_definition: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
    ) -> str:
        """
        Execute a workflow using agent coordination.

        Args:
            workflow_definition: Workflow definition dictionary
            context: Optional execution context
            workflow_id: Optional workflow ID (generated if None)

        Returns:
            Workflow execution ID
        """
        if workflow_id is None:
            from uuid import uuid4

            workflow_id = str(uuid4())

        # Create coordination context
        coordination_context = WorkflowCoordinationContext(
            workflow_id=workflow_id,
            workflow_definition=workflow_definition,
            execution_status=WorkflowExecutionStatus.PENDING,
            coordination_metadata=context or {},
        )

        self._active_workflows[workflow_id] = coordination_context

        # Begin workflow analysis and agent assignment
        await self._analyze_and_assign_workflow(coordination_context)

        self.logger.info(f"Workflow execution started: {workflow_id}")
        return workflow_id

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel an active workflow.

        Args:
            workflow_id: ID of workflow to cancel

        Returns:
            True if workflow was cancelled, False if not found
        """
        if workflow_id not in self._active_workflows:
            return False

        context = self._active_workflows[workflow_id]
        context.execution_status = WorkflowExecutionStatus.CANCELLED

        # Notify assigned agents to cancel their tasks
        for assignment in context.agent_assignments:
            if assignment.status in ["assigned", "running"]:
                await self._send_cancellation_message(
                    assignment.agent_id, assignment.step_id
                )

        # Remove from active workflows
        del self._active_workflows[workflow_id]

        self.logger.info(f"Workflow cancelled: {workflow_id}")
        return True

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a workflow execution.

        Args:
            workflow_id: ID of workflow

        Returns:
            Status dictionary if found, None otherwise
        """
        if workflow_id not in self._active_workflows:
            return None

        context = self._active_workflows[workflow_id]

        return {
            "workflow_id": workflow_id,
            "status": context.execution_status.value,
            "created_at": context.created_at.isoformat(),
            "started_at": context.started_at.isoformat()
            if context.started_at
            else None,
            "completed_at": context.completed_at.isoformat()
            if context.completed_at
            else None,
            "agent_assignments": [
                {
                    "step_id": assignment.step_id,
                    "agent_id": assignment.agent_id,
                    "status": assignment.status,
                    "capability_match": assignment.capability_match.value,
                    "assigned_at": assignment.assigned_at.isoformat(),
                    "started_at": assignment.started_at.isoformat()
                    if assignment.started_at
                    else None,
                    "completed_at": assignment.completed_at.isoformat()
                    if assignment.completed_at
                    else None,
                    "error": assignment.error,
                }
                for assignment in context.agent_assignments
            ],
            "metadata": context.coordination_metadata,
        }

    def list_active_workflows(self) -> List[str]:
        """
        List all active workflow IDs.

        Returns:
            List of active workflow IDs
        """
        return list(self._active_workflows.keys())

    async def register_step_handler(
        self, step_type: str, handler: Callable[[Dict[str, Any], Dict[str, Any]], Any]
    ) -> None:
        """
        Register a handler for specific workflow step types.

        Args:
            step_type: Type of workflow step
            handler: Handler function for the step type
        """
        self._step_handlers[step_type] = handler
        self.logger.info(f"Step handler registered for type: {step_type}")

    async def _analyze_and_assign_workflow(
        self, context: WorkflowCoordinationContext
    ) -> None:
        """Analyze workflow and assign steps to agents."""
        try:
            context.execution_status = WorkflowExecutionStatus.ASSIGNED
            context.started_at = datetime.now(timezone.utc)

            workflow_def = context.workflow_definition

            # Parse workflow steps
            if "steps" in workflow_def:
                for step in workflow_def["steps"]:
                    await self._assign_step_to_agent(context, step)

            # Begin execution
            context.execution_status = WorkflowExecutionStatus.RUNNING
            await self._execute_assigned_steps(context)

        except Exception as e:
            self.logger.error(
                f"Workflow analysis failed for {context.workflow_id}: {e}"
            )
            context.execution_status = WorkflowExecutionStatus.FAILED

    async def _assign_step_to_agent(
        self, context: WorkflowCoordinationContext, step: Dict[str, Any]
    ) -> None:
        """Assign a workflow step to an appropriate agent."""
        step_id = step.get("id", f"step_{len(context.agent_assignments)}")
        required_capabilities = step.get("requires", [])

        # Find agents with required capabilities
        suitable_agents = []

        for capability in required_capabilities:
            agent_ids = self.agent_registry.find_agents_by_capability(capability)
            for agent_id in agent_ids:
                agent_info = self.agent_registry.get_agent_info(agent_id)
                if agent_info and agent_info.status == RegistrationStatus.ACTIVE:
                    suitable_agents.append((agent_id, AgentCapabilityMatch.EXACT))

        # If no exact matches, look for partial matches
        if not suitable_agents:
            all_active_agents = self.agent_registry.find_agents_by_status(
                RegistrationStatus.ACTIVE
            )
            for agent_id in all_active_agents:
                agent_info = self.agent_registry.get_agent_info(agent_id)
                if agent_info:
                    # Check for partial capability match
                    agent_capabilities = set(agent_info.capabilities)
                    required_capabilities_set = set(required_capabilities)

                    if agent_capabilities.intersection(required_capabilities_set):
                        suitable_agents.append((agent_id, AgentCapabilityMatch.PARTIAL))

        # Assign to best available agent
        if suitable_agents:
            # Sort by match quality and select best
            suitable_agents.sort(key=lambda x: x[1].value)
            agent_id, match_quality = suitable_agents[0]

            assignment = WorkflowAgentAssignment(
                step_id=step_id, agent_id=agent_id, capability_match=match_quality
            )

            context.agent_assignments.append(assignment)

            self.logger.info(
                f"Step {step_id} assigned to agent {agent_id} "
                f"(match: {match_quality.value})"
            )
        else:
            self.logger.warning(f"No suitable agent found for step {step_id}")
            # Create unassigned entry
            assignment = WorkflowAgentAssignment(
                step_id=step_id,
                agent_id="",
                capability_match=AgentCapabilityMatch.NO_MATCH,
                status="unassigned",
                error="No suitable agent found",
            )
            context.agent_assignments.append(assignment)

    async def _execute_assigned_steps(
        self, context: WorkflowCoordinationContext
    ) -> None:
        """Execute workflow steps that have been assigned to agents."""
        # Send task messages to assigned agents
        for assignment in context.agent_assignments:
            if assignment.agent_id and assignment.status == "assigned":
                await self._send_task_message(context, assignment)

    async def _send_task_message(
        self, context: WorkflowCoordinationContext, assignment: WorkflowAgentAssignment
    ) -> None:
        """Send task execution message to an agent."""
        try:
            # Find the step definition
            step_def = None
            for step in context.workflow_definition.get("steps", []):
                if step.get("id") == assignment.step_id:
                    step_def = step
                    break

            if not step_def:
                assignment.error = "Step definition not found"
                assignment.status = "failed"
                return

            # Create task message
            task_message = AgentMessage(
                message_id=f"task_{context.workflow_id}_{assignment.step_id}",
                sender_id="workflow_coordinator",
                recipient_id=assignment.agent_id,
                type=MessageType.TASK_REQUEST,
                content={
                    "workflow_id": context.workflow_id,
                    "step_id": assignment.step_id,
                    "step_definition": step_def,
                    "context": context.coordination_metadata,
                },
                metadata={"workflow_coordination": True, "requires_response": True},
            )

            # Send message
            success = await self.message_bus.send_message(
                task_message, priority=MessagePriority.HIGH
            )

            if success:
                assignment.status = "sent"
                assignment.started_at = datetime.now(timezone.utc)
                self.logger.info(
                    f"Task message sent to {assignment.agent_id} for step {assignment.step_id}"
                )
            else:
                assignment.status = "failed"
                assignment.error = "Failed to send task message"

        except Exception as e:
            assignment.status = "failed"
            assignment.error = f"Task message sending error: {e}"
            self.logger.error(f"Failed to send task message: {e}")

    async def _send_cancellation_message(self, agent_id: str, step_id: str) -> None:
        """Send cancellation message to an agent."""
        cancellation_message = AgentMessage(
            message_id=f"cancel_{step_id}",
            sender_id="workflow_coordinator",
            recipient_id=agent_id,
            type=MessageType.CONTROL,
            content={"action": "cancel_task", "step_id": step_id},
        )

        await self.message_bus.send_message(
            cancellation_message, priority=MessagePriority.CRITICAL
        )

    async def _handle_workflow_message(self, message: AgentMessage) -> None:
        """Handle incoming workflow-related messages."""
        try:
            if message.type == MessageType.TASK_RESPONSE:
                await self._handle_task_response(message)
            elif message.type == MessageType.STATUS_UPDATE:
                await self._handle_status_update(message)

        except Exception as e:
            self.logger.error(f"Error handling workflow message: {e}")

    async def _handle_task_response(self, message: AgentMessage) -> None:
        """Handle task response from an agent."""
        content = message.content
        workflow_id = content.get("workflow_id")
        step_id = content.get("step_id")

        if not workflow_id or workflow_id not in self._active_workflows:
            return

        context = self._active_workflows[workflow_id]

        # Find the assignment
        assignment = None
        for assign in context.agent_assignments:
            if assign.step_id == step_id and assign.agent_id == message.sender_id:
                assignment = assign
                break

        if assignment:
            assignment.completed_at = datetime.now(timezone.utc)
            assignment.result = content.get("result")

            if content.get("success", True):
                assignment.status = "completed"
            else:
                assignment.status = "failed"
                assignment.error = content.get("error", "Task failed")

            # Check if all steps are completed
            await self._check_workflow_completion(context)

    async def _handle_status_update(self, message: AgentMessage) -> None:
        """Handle status update from an agent."""
        # Update assignment status based on agent status
        content = message.content
        workflow_id = content.get("workflow_id")
        step_id = content.get("step_id")
        status = content.get("status")

        if workflow_id and workflow_id in self._active_workflows:
            context = self._active_workflows[workflow_id]

            for assignment in context.agent_assignments:
                if (
                    assignment.step_id == step_id
                    and assignment.agent_id == message.sender_id
                ):
                    assignment.status = status
                    break

    async def _check_workflow_completion(
        self, context: WorkflowCoordinationContext
    ) -> None:
        """Check if workflow is completed and update status."""
        all_completed = True
        any_failed = False

        for assignment in context.agent_assignments:
            if assignment.status in ["assigned", "sent", "running"]:
                all_completed = False
                break
            elif assignment.status == "failed":
                any_failed = True

        if all_completed:
            if any_failed:
                context.execution_status = WorkflowExecutionStatus.FAILED
            else:
                context.execution_status = WorkflowExecutionStatus.COMPLETED

            context.completed_at = datetime.now(timezone.utc)

            self.logger.info(
                f"Workflow {context.workflow_id} completed with status: "
                f"{context.execution_status.value}"
            )

            # Remove from active workflows after a delay to allow status queries
            await asyncio.sleep(60)  # Keep for 1 minute for status queries
            if context.workflow_id in self._active_workflows:
                del self._active_workflows[context.workflow_id]


# Integration convenience functions
async def execute_workflow_with_agents(
    workflow_definition: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to execute a workflow using agent coordination.

    Args:
        workflow_definition: Workflow definition dictionary
        context: Optional execution context

    Returns:
        Workflow execution ID
    """
    coordinator = WorkflowCoordinator()
    await coordinator.start()

    workflow_id = await coordinator.execute_workflow(workflow_definition, context)
    return workflow_id


async def get_workflow_execution_status(workflow_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get workflow execution status.

    Args:
        workflow_id: ID of workflow

    Returns:
        Status dictionary if found, None otherwise
    """
    coordinator = WorkflowCoordinator()
    return await coordinator.get_workflow_status(workflow_id)


# Global coordinator instance
_coordinator_instance: Optional[WorkflowCoordinator] = None


def get_workflow_coordinator() -> WorkflowCoordinator:
    """Get the global workflow coordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = WorkflowCoordinator()
    return _coordinator_instance


async def initialize_workflow_coordination() -> WorkflowCoordinator:
    """Initialize and start the global workflow coordinator."""
    coordinator = get_workflow_coordinator()
    await coordinator.start()
    return coordinator


async def shutdown_workflow_coordination() -> None:
    """Shutdown the global workflow coordinator."""
    global _coordinator_instance
    if _coordinator_instance:
        await _coordinator_instance.stop()
        _coordinator_instance = None
