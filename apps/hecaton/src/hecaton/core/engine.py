"""Execution engine for HECATON orchestration"""

import asyncio
import logging

from ..utils.enhanced_logging import (
    get_logger,
    log_execution_time,
    log_state_transition,
)

logger = get_logger(__name__)
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agents.agent_registry import AgentRegistry
from ..agents.meta_agent import MetaAgent
from ..messaging.message_broker import MessageBroker
from ..safety.checkpoint_manager import CheckpointManager
from ..safety.error_boundaries import ErrorBoundary
from ..swarm.swarm_decomposer import SwarmTaskDecomposer

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for task execution"""

    task_id: str
    agent_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    error_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionEngine:
    """Core execution engine for HECATON tasks"""

    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        message_broker: Optional[MessageBroker] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        error_boundary: Optional[ErrorBoundary] = None,
        meta_agent: Optional[MetaAgent] = None,
        swarm_decomposer: Optional[SwarmTaskDecomposer] = None,
    ):
        """
        Initialize execution engine with core components.

        Args:
            agent_registry: Registry for managing agents
            message_broker: Broker for inter-agent communication
            checkpoint_manager: Manager for state checkpointing
            error_boundary: Error isolation and recovery
            meta_agent: Intelligent task delegation
            swarm_decomposer: Task decomposition for parallel execution
        """
        self.agent_registry = agent_registry or AgentRegistry()
        self.message_broker = message_broker or MessageBroker()
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.error_boundary = error_boundary or ErrorBoundary()
        self.meta_agent = meta_agent or MetaAgent()
        self.swarm_decomposer = swarm_decomposer or SwarmTaskDecomposer()

        self.execution_contexts: Dict[str, ExecutionContext] = {}
        self.is_running = False

    async def start(self):
        """Start the execution engine and its components"""
        if self.is_running:
            logger.warning("Execution engine already running")
            return

        logger.info("Starting execution engine")

        # Start components
        await self.message_broker.start()

        self.is_running = True
        logger.info("Execution engine started successfully")

    async def stop(self):
        """Stop the execution engine and cleanup"""
        if not self.is_running:
            logger.warning("Execution engine not running")
            return

        logger.info("Stopping execution engine")

        # Stop components
        await self.message_broker.stop()

        # Clear contexts
        self.execution_contexts.clear()

        self.is_running = False
        logger.info("Execution engine stopped")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with full safety and coordination.

        Args:
            task: Task definition with type, description, and requirements

        Returns:
            Dict with execution results and metadata
        """
        if not self.is_running:
            await self.start()

        task_id = task.get("id", f"task_{datetime.now().timestamp()}")
        context = ExecutionContext(task_id=task_id)
        self.execution_contexts[task_id] = context

        try:
            # Create initial checkpoint
            checkpoint_id = await self.checkpoint_manager.create_checkpoint(
                {"task": task, "status": "started", "context": context.__dict__}
            )
            context.checkpoint_id = checkpoint_id

            # Decompose task if complex
            if self._is_complex_task(task):
                result = await self._execute_complex_task(task, context)
            else:
                result = await self._execute_simple_task(task, context)

            # Create completion checkpoint
            await self.checkpoint_manager.create_checkpoint(
                {
                    "task": task,
                    "status": "completed",
                    "result": result,
                    "context": context.__dict__,
                }
            )

            return {
                "task_id": task_id,
                "status": "success",
                "result": result,
                "execution_time": (datetime.now() - context.start_time).total_seconds(),
                "metadata": context.metadata,
            }

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            context.error_count += 1

            # Try to recover from checkpoint
            if context.checkpoint_id:
                try:
                    state = await self.checkpoint_manager.rollback_to_checkpoint(
                        context.checkpoint_id
                    )
                    logger.info(f"Recovered task {task_id} from checkpoint")
                    # Could retry here with recovered state
                except Exception as recovery_error:
                    logger.error(f"Failed to recover task {task_id}: {recovery_error}")

            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "error_count": context.error_count,
                "execution_time": (datetime.now() - context.start_time).total_seconds(),
            }

        finally:
            # Cleanup context after some delay
            if task_id in self.execution_contexts:
                # In production, would schedule cleanup after delay
                pass

    async def _execute_simple_task(
        self, task: Dict[str, Any], context: ExecutionContext
    ) -> Any:
        """Execute a simple task with single agent"""

        # Delegate to appropriate agent
        decision = await self.meta_agent.decide_delegation(task)
        context.agent_id = decision.agent_id

        # Execute with error boundary
        async def agent_execution():
            agent = await self.agent_registry.get_agent(decision.agent_id)
            if not agent:
                raise ValueError(f"Agent {decision.agent_id} not found")

            # In real implementation, would execute via agent's interface
            # For now, simulate execution
            await asyncio.sleep(0.1)  # Simulate work
            return {
                "agent": decision.agent_id,
                "confidence": decision.confidence,
                "output": f"Task completed by {decision.agent_id}",
            }

        result = await self.error_boundary.execute_with_boundary(
            agent_execution,
            context={"task_id": context.task_id, "agent_id": context.agent_id},
        )

        return result

    async def _execute_complex_task(
        self, task: Dict[str, Any], context: ExecutionContext
    ) -> Any:
        """Execute a complex task with multiple agents and parallelization"""

        # Decompose into execution groups
        execution_groups = await self.swarm_decomposer.decompose_task(task)

        results = []
        for group in execution_groups:
            if group.can_parallelize and len(group.tasks) > 1:
                # Execute tasks in parallel
                group_tasks = [
                    self._execute_simple_task(
                        {"type": t.task_type, "description": t.description},
                        ExecutionContext(task_id=t.task_id),
                    )
                    for t in group.tasks
                ]
                group_results = await asyncio.gather(
                    *group_tasks, return_exceptions=True
                )
                results.extend(group_results)
            else:
                # Execute sequentially
                for task_node in group.tasks:
                    result = await self._execute_simple_task(
                        {
                            "type": task_node.task_type,
                            "description": task_node.description,
                        },
                        ExecutionContext(task_id=task_node.task_id),
                    )
                    results.append(result)

        return {
            "execution_groups": len(execution_groups),
            "total_tasks": sum(len(g.tasks) for g in execution_groups),
            "results": results,
        }

    def _is_complex_task(self, task: Dict[str, Any]) -> bool:
        """Determine if a task is complex and needs decomposition"""
        # Complex if has subtasks or multiple requirements
        if "subtasks" in task:
            return True
        if "requirements" in task and len(task.get("requirements", [])) > 2:
            return True
        if task.get("complexity") in ["high", "complex"]:
            return True
        return False

    async def get_status(self) -> Dict[str, Any]:
        """Get current engine status and metrics"""
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.execution_contexts),
            "registered_agents": len(self.agent_registry.agents),
            "checkpoints": len(await self.checkpoint_manager.list_checkpoints()),
            "contexts": [
                {
                    "task_id": ctx.task_id,
                    "agent_id": ctx.agent_id,
                    "error_count": ctx.error_count,
                    "duration": (datetime.now() - ctx.start_time).total_seconds(),
                }
                for ctx in self.execution_contexts.values()
            ],
        }
