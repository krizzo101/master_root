"""
Dependency-Injected Orchestrator Implementation

Refactored orchestrator that uses dependency injection for all external dependencies,
eliminating singleton patterns and improving testability.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .factory.orchestrator_factory import OrchestratorConfig
from .interfaces import IFileHandler, IMessageBus, ITokenProvider
from .interfaces.message_bus import Message, Priority

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents a task for an agent"""

    task_id: str
    agent_id: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None
    token: Optional[str] = None


class DependencyInjectedOrchestrator:
    """
    Orchestrator implementation with full dependency injection.

    This orchestrator:
    - Uses injected providers for all external dependencies
    - Eliminates singleton patterns
    - Provides clean separation of concerns
    - Enables easy testing with mock implementations
    """

    def __init__(
        self,
        token_provider: ITokenProvider,
        file_handler: IFileHandler,
        message_bus: IMessageBus,
        config: Optional[OrchestratorConfig] = None,
    ):
        """
        Initialize orchestrator with injected dependencies.

        Args:
            token_provider: Token provider implementation
            file_handler: File handler implementation
            message_bus: Message bus implementation
            config: Orchestrator configuration
        """
        self.token_provider = token_provider
        self.file_handler = file_handler
        self.message_bus = message_bus
        self.config = config or OrchestratorConfig()

        # Internal state
        self.session_id: Optional[str] = None
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.running = False
        self._background_tasks: List[asyncio.Task] = []

        # Configure logging
        logging.basicConfig(level=self.config.log_level)

    async def initialize(self, session_id: str) -> None:
        """
        Initialize the orchestrator for a session.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        logger.info(f"Initializing orchestrator for session {session_id}")

        # Connect to message bus
        await self.message_bus.connect()

        # Subscribe to orchestrator topics
        await self._setup_message_handlers()

        # Ensure session directory exists
        session_dir = self.config.session_dir / session_id
        await self.file_handler.ensure_dir(session_dir)

        # Start background tasks if configured
        if self.config.enable_monitoring:
            self._background_tasks.append(asyncio.create_task(self._monitor_health()))

        if self.config.enable_checkpointing:
            self._background_tasks.append(asyncio.create_task(self._checkpoint_loop()))

        self.running = True
        logger.info("Orchestrator initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the orchestrator gracefully"""
        logger.info("Shutting down orchestrator")
        self.running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Release any held tokens
        for task in self.active_tasks.values():
            if task.token:
                await self.token_provider.release_token(task.token, task.task_id)

        # Disconnect from message bus
        await self.message_bus.disconnect()

        # Save final state
        await self._save_state()

        logger.info("Orchestrator shutdown complete")

    async def execute_task(
        self,
        agent_id: str,
        task_payload: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> AgentTask:
        """
        Execute a task with an agent.

        Args:
            agent_id: ID of the agent to execute the task
            task_payload: Task payload for the agent
            task_id: Optional task ID (generated if not provided)

        Returns:
            AgentTask object tracking the execution
        """
        import uuid

        task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"

        task = AgentTask(
            task_id=task_id,
            agent_id=agent_id,
            payload=task_payload,
        )

        self.active_tasks[task_id] = task

        try:
            # Acquire token for the task
            task.token = await self.token_provider.acquire_token(
                task_id=task_id,
                timeout=self.config.token_reservation_timeout,
            )

            # Update task status
            task.status = "running"

            # Send task to agent via message bus
            await self.message_bus.send_direct(
                recipient=agent_id,
                payload={
                    "task_id": task_id,
                    "action": "execute",
                    "payload": task_payload,
                    "token": task.token,
                },
                priority=Priority.NORMAL,
            )

            # Save task state
            await self._save_task_state(task)

            logger.info(f"Task {task_id} sent to agent {agent_id}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

            if task.token:
                await self.token_provider.release_token(task.token, task_id)

            logger.error(f"Failed to execute task {task_id}: {e}")
            raise

        return task

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
    ) -> List[AgentTask]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of task definitions (each with agent_id and payload)
            batch_id: Optional batch identifier

        Returns:
            List of AgentTask objects
        """
        import uuid

        batch_id = batch_id or f"batch_{uuid.uuid4().hex[:8]}"
        logger.info(f"Executing batch {batch_id} with {len(tasks)} tasks")

        # Acquire tokens for the batch
        tokens = await self.token_provider.acquire_batch(
            count=min(len(tasks), self.config.max_parallel_agents),
            batch_id=batch_id,
            timeout=self.config.token_reservation_timeout,
        )

        # Create task objects
        agent_tasks = []
        token_idx = 0

        for task_def in tasks:
            task_id = f"{batch_id}_{len(agent_tasks)}"

            task = AgentTask(
                task_id=task_id,
                agent_id=task_def["agent_id"],
                payload=task_def["payload"],
            )

            # Assign token if available
            if token_idx < len(tokens):
                task.token = tokens[token_idx]
                token_idx += 1
                task.status = "running"
            else:
                task.status = "queued"

            agent_tasks.append(task)
            self.active_tasks[task_id] = task

        # Execute tasks with tokens
        execution_tasks = []
        for task in agent_tasks:
            if task.status == "running":
                execution_tasks.append(self._execute_single_task(task))

        # Wait for execution
        await asyncio.gather(*execution_tasks, return_exceptions=True)

        return agent_tasks

    async def _execute_single_task(self, task: AgentTask) -> None:
        """Execute a single task"""
        try:
            await self.message_bus.send_direct(
                recipient=task.agent_id,
                payload={
                    "task_id": task.task_id,
                    "action": "execute",
                    "payload": task.payload,
                    "token": task.token,
                },
                priority=Priority.NORMAL,
            )

            await self._save_task_state(task)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")

    async def _setup_message_handlers(self) -> None:
        """Setup message handlers for orchestrator"""

        async def handle_status_update(message: Message):
            """Handle status updates from agents"""
            task_id = message.payload.get("task_id")
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.status = message.payload.get("status", task.status)

                if task.status == "completed":
                    task.result = message.payload.get("result")
                    await self._complete_task(task)
                elif task.status == "failed":
                    task.error = message.payload.get("error")
                    await self._complete_task(task)

        async def handle_coordination(message: Message):
            """Handle coordination messages"""
            action = message.payload.get("action")

            if action == "request_token":
                # Agent requesting additional token
                agent_id = message.sender
                try:
                    token = await self.token_provider.acquire_token()
                    await self.message_bus.send_direct(
                        recipient=agent_id,
                        payload={"action": "token_granted", "token": token},
                        priority=Priority.HIGH,
                    )
                except Exception as e:
                    await self.message_bus.send_direct(
                        recipient=agent_id,
                        payload={"action": "token_denied", "reason": str(e)},
                        priority=Priority.HIGH,
                    )

        # Subscribe to relevant topics
        await self.message_bus.subscribe(
            topics=["status", "status_update"],
            handler=handle_status_update,
            subscriber_id=f"orchestrator_{self.session_id}",
        )

        await self.message_bus.subscribe(
            topics=["coordination"],
            handler=handle_coordination,
            subscriber_id=f"orchestrator_{self.session_id}",
        )

    async def _complete_task(self, task: AgentTask) -> None:
        """Complete a task and clean up resources"""
        # Release token
        if task.token:
            await self.token_provider.release_token(task.token, task.task_id)

        # Move to completed
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
            self.completed_tasks.append(task)

        # Save state
        await self._save_task_state(task)

        logger.info(f"Task {task.task_id} completed with status {task.status}")

    async def _save_task_state(self, task: AgentTask) -> None:
        """Save task state to file"""
        if not self.session_id:
            return

        task_file = (
            self.config.session_dir / self.session_id / "tasks" / f"{task.task_id}.json"
        )
        await self.file_handler.ensure_dir(task_file.parent)

        await self.file_handler.write_json(
            task_file,
            {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "status": task.status,
                "payload": task.payload,
                "result": task.result,
                "error": task.error,
            },
        )

    async def _save_state(self) -> None:
        """Save orchestrator state"""
        if not self.session_id:
            return

        state_file = (
            self.config.session_dir / self.session_id / "orchestrator_state.json"
        )

        state = {
            "session_id": self.session_id,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "config": {
                "max_parallel_agents": self.config.max_parallel_agents,
                "enable_monitoring": self.config.enable_monitoring,
                "enable_collaboration": self.config.enable_collaboration,
            },
        }

        await self.file_handler.write_json(state_file, state)

    async def _checkpoint_loop(self) -> None:
        """Background task for periodic checkpointing"""
        while self.running:
            try:
                await asyncio.sleep(self.config.checkpoint_interval)
                await self._save_state()
                logger.debug("Checkpoint saved")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Checkpoint failed: {e}")

    async def _monitor_health(self) -> None:
        """Background task for health monitoring"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Check provider health
                token_health = await self.token_provider.health_check()
                bus_health = await self.message_bus.health_check()

                if not token_health or not bus_health:
                    logger.warning(
                        f"Health check warning - Token: {token_health}, Bus: {bus_health}"
                    )

                # Collect metrics
                metrics = {
                    "token_metrics": await self.token_provider.get_metrics(),
                    "file_metrics": await self.file_handler.get_metrics(),
                    "bus_metrics": await self.message_bus.get_metrics(),
                    "active_tasks": len(self.active_tasks),
                    "completed_tasks": len(self.completed_tasks),
                }

                # Save metrics
                if self.session_id:
                    metrics_file = (
                        self.config.session_dir
                        / self.session_id
                        / "metrics"
                        / f"metrics_{asyncio.get_event_loop().time()}.json"
                    )
                    await self.file_handler.ensure_dir(metrics_file.parent)
                    await self.file_handler.write_json(metrics_file, metrics)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring failed: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "session_id": self.session_id,
            "running": self.running,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "token_availability": self.token_provider.get_available_count(),
            "total_tokens": self.token_provider.get_total_count(),
        }
