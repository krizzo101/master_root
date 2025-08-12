"""Task Execution Engine - Core bridge between DAG orchestration and Celery execution."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4

from celery.result import AsyncResult

from opsvi_auto_forge.config.models import TaskStatus
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

# Lazy imports to avoid circular dependencies
# from opsvi_auto_forge.application.orchestrator.task_models import TaskExecution, TaskResult, TaskDefinition
# from opsvi_auto_forge.application.orchestrator.task_state_manager import TaskStateManager
# from opsvi_auto_forge.application.orchestrator.result_collector import ResultCollector
# from opsvi_auto_forge.application.orchestrator.task_router import TaskRouter
# from opsvi_auto_forge.application.orchestrator.execution_coordinator import ExecutionCoordinator
from opsvi_auto_forge.infrastructure.workers.agent_tasks import submit_agent_task

logger = logging.getLogger(__name__)


class TaskExecutionEngine(ABC):
    """Abstract base class for task execution engines."""

    @abstractmethod
    async def execute_task(
        self, task_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Any:  # TaskResult
        """Execute a task asynchronously."""
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get current status of a task."""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        pass

    @abstractmethod
    async def get_active_tasks(self) -> Dict[str, Any]:
        """Get all active tasks and their statuses."""
        pass


class CeleryTaskExecutionEngine(TaskExecutionEngine):
    """Celery-based implementation of TaskExecutionEngine.

    This engine provides the missing link between the MetaOrchestrator's DAG
    execution and actual Celery task execution, implementing the critical
    functionality that was identified as missing in the gap analysis.
    """

    def __init__(self, neo4j_client: Neo4jClient, redis_client: Any):
        """Initialize the Task Execution Engine.

        Args:
            neo4j_client: Neo4j client for persistence
            redis_client: Redis client for caching and coordination
        """
        self.neo4j_client = neo4j_client
        self.redis_client = redis_client

        # Initialize sub-components lazily to avoid circular imports
        self._state_manager = None
        self._result_collector = None
        self._task_router = None
        self._execution_coordinator = None

        # Active task tracking
        self.active_tasks: Dict[UUID, AsyncResult] = {}
        self.task_executions: Dict[UUID, Any] = {}  # TaskExecution type

        logger.info("CeleryTaskExecutionEngine initialized successfully")

    @property
    def state_manager(self):
        """Lazy load state manager."""
        if self._state_manager is None:
            from opsvi_auto_forge.application.orchestrator.task_state_manager import (
                TaskStateManager,
            )

            self._state_manager = TaskStateManager(self.neo4j_client, self.redis_client)
        return self._state_manager

    @property
    def result_collector(self):
        """Lazy load result collector."""
        if self._result_collector is None:
            from opsvi_auto_forge.application.orchestrator.result_collector import (
                ResultCollector,
            )

            self._result_collector = ResultCollector(self.neo4j_client)
        return self._result_collector

    @property
    def task_router(self):
        """Lazy load task router."""
        if self._task_router is None:
            from opsvi_auto_forge.application.orchestrator.task_router import TaskRouter

            self._task_router = TaskRouter()
        return self._task_router

    @property
    def execution_coordinator(self):
        """Lazy load execution coordinator."""
        if self._execution_coordinator is None:
            from opsvi_auto_forge.application.orchestrator.execution_coordinator import (
                ExecutionCoordinator,
            )

            self._execution_coordinator = ExecutionCoordinator()
        return self._execution_coordinator

    async def execute_task(
        self, task_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Any:  # TaskResult
        """Execute a task asynchronously.

        Args:
            task_id: Unique task identifier
            task_type: Type of task to execute
            parameters: Task execution parameters

        Returns:
            TaskResult: Structured result of the task execution
        """
        try:
            # Create task execution from parameters
            task_execution = await self._create_task_execution_from_params(
                task_id, task_type, parameters
            )

            # Execute the task
            return await self._execute_task_internal(task_execution)

        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            from opsvi_auto_forge.application.orchestrator.task_models import TaskResult

            return TaskResult(
                task_id=UUID(task_id),
                status=TaskStatus.FAILED,
                score=0.0,
                errors=[str(e)],
                metadata={"error": str(e)},
            )

    async def execute_dag_node(
        self,
        context: Any,  # OrchestrationContext
        dag_node: Any,  # DAGNode
    ) -> Any:  # TaskResult
        """Execute a single DAG node with full lifecycle management.

        This is the core method that bridges DAG orchestration with actual
        task execution, implementing the critical missing functionality.

        Args:
            context: Orchestration context containing project and run info
            dag_node: DAG node to execute

        Returns:
            TaskResult: Structured result of the task execution

        Raises:
            TaskExecutionError: If task execution fails
        """
        task_id = uuid4()

        try:
            logger.info(f"Executing DAG node {dag_node.id} with task ID {task_id}")

            # 1. Create task execution record
            task_execution = await self._create_task_execution(
                context, dag_node, task_id
            )
            self.task_executions[task_id] = task_execution

            # 2. Update state to PENDING
            await self.state_manager.update_state(
                task_id,
                TaskStatus.PENDING,
                dag_node_id=dag_node.id,
                context_id=str(context.run_id),
            )

            # 3. Route task to appropriate queue
            queue_name = self.task_router.route_task(task_execution)
            logger.info(f"Task {task_id} routed to queue: {queue_name}")

            # 4. Submit task to Celery
            celery_task_id = await self._submit_to_celery(task_execution, queue_name)

            # 5. Update state to RUNNING
            await self.state_manager.update_state(
                task_id,
                TaskStatus.RUNNING,
                celery_task_id=celery_task_id,
                started_at=datetime.now(timezone.utc),
            )

            # 6. Wait for completion
            raw_result = await self._wait_for_completion(task_id, celery_task_id)

            # 7. Collect and process result
            processed_result = await self.result_collector.process_result(
                task_id, raw_result
            )

            # 8. Update final state
            await self.state_manager.update_state(
                task_id,
                processed_result.status,
                completed_at=datetime.now(timezone.utc),
                result_id=str(processed_result.task_id),
            )

            # 9. Cleanup
            self._cleanup_task(task_id)

            logger.info(
                f"Task {task_id} completed successfully with status: {processed_result.status}"
            )
            return processed_result

        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")

            # Update state to FAILED
            await self.state_manager.update_state(
                task_id,
                TaskStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )

            # Create error result
            error_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                score=0.0,
                errors=[str(e)],
                warnings=[],
                artifacts=[],
                metadata={"error": str(e)},
            )

            # Cleanup
            self._cleanup_task(task_id)

            return error_result

    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get current status of a task."""
        state = await self.state_manager.get_state(UUID(task_id))
        if state:
            return state.get("status", TaskStatus.PENDING)
        return TaskStatus.PENDING

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task_uuid = UUID(task_id)
        if task_uuid not in self.active_tasks:
            return False

        celery_task = self.active_tasks[task_uuid]
        celery_task.revoke(terminate=True)

        await self.state_manager.update_state(
            task_uuid, TaskStatus.CANCELLED, cancelled_at=datetime.now(timezone.utc)
        )

        self._cleanup_task(task_uuid)
        logger.info(f"Task {task_id} cancelled successfully")
        return True

    async def get_active_tasks(self) -> Dict[str, Any]:
        """Get all active tasks and their statuses."""
        active_tasks = {}
        for task_id in self.active_tasks:
            state = await self.state_manager.get_state(task_id)
            if state:
                active_tasks[str(task_id)] = state
        return active_tasks

    async def _create_task_execution_from_params(
        self, task_id: str, task_type: str, parameters: Dict[str, Any]
    ) -> Any:  # TaskExecution
        """Create a TaskExecution from parameters."""

        from opsvi_auto_forge.application.orchestrator.task_models import (
            TaskDefinition,
            TaskExecution,
        )

        # Create task definition
        task_definition = TaskDefinition(
            name=parameters.get("name", f"task_{task_id}"),
            type=task_type,
            agent_type=parameters.get("agent_type", "default"),
            description=parameters.get("description", ""),
            inputs=parameters.get("inputs", {}),
            outputs=parameters.get("outputs", {}),
            dependencies=parameters.get("dependencies", []),
            timeout_seconds=parameters.get("timeout_seconds", 300),
            retry_attempts=parameters.get("retry_attempts", 3),
            queue=parameters.get("queue", "default"),
        )

        # Create task execution
        task_execution = TaskExecution(
            id=UUID(task_id),
            definition=task_definition,
            project_id=parameters.get("project_id"),
            run_id=parameters.get("run_id"),
            status=TaskStatus.PENDING,
            inputs=parameters.get("inputs", {}),
            metadata={
                "task_id": task_id,
                "task_type": task_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return task_execution

    async def _execute_task_internal(
        self, task_execution: Any
    ) -> Any:  # TaskExecution -> TaskResult
        """Internal task execution logic."""
        try:
            # Route task to appropriate queue
            queue_name = self.task_router.route_task(task_execution)

            # Submit to Celery
            celery_task_id = await self._submit_to_celery(task_execution, queue_name)

            # Wait for completion
            raw_result = await self._wait_for_completion(
                task_execution.id, celery_task_id
            )

            # Process result
            processed_result = await self.result_collector.process_result(
                task_execution.id, raw_result
            )

            # Cleanup
            self._cleanup_task(task_execution.id)

            return processed_result

        except Exception as e:
            logger.error(f"Task {task_execution.id} execution failed: {e}")
            from opsvi_auto_forge.application.orchestrator.task_models import TaskResult

            return TaskResult(
                task_id=task_execution.id,
                status=TaskStatus.FAILED,
                score=0.0,
                errors=[str(e)],
                metadata={"error": str(e)},
            )

    async def _create_task_execution(
        self, context: Any, dag_node: Any, task_id: UUID
    ) -> Any:  # TaskExecution
        """Create a TaskExecution record from DAG node and context."""

        from opsvi_auto_forge.application.orchestrator.task_models import (
            TaskDefinition,
            TaskExecution,
        )

        # Extract agent type from DAG node
        agent_type = dag_node.agent if hasattr(dag_node, "agent") else "default"

        # Create task definition
        task_definition = TaskDefinition(
            name=dag_node.name if hasattr(dag_node, "name") else str(dag_node.id),
            type=self._map_node_type_to_task_type(dag_node),
            agent_type=agent_type,
            description=dag_node.description
            if hasattr(dag_node, "description")
            else "",
            inputs=dag_node.inputs if hasattr(dag_node, "inputs") else {},
            outputs=dag_node.outputs if hasattr(dag_node, "outputs") else {},
            dependencies=dag_node.dependencies
            if hasattr(dag_node, "dependencies")
            else [],
            timeout_seconds=300,  # Default timeout
            retry_attempts=3,  # Default retries
            queue=self.task_router.route_task_by_agent(agent_type),
        )

        # Create task execution
        task_execution = TaskExecution(
            id=task_id,
            definition=task_definition,
            project_id=context.project_id,
            run_id=context.run_id,
            status=TaskStatus.PENDING,
            inputs=dag_node.inputs if hasattr(dag_node, "inputs") else {},
            metadata={
                "dag_node_id": str(dag_node.id),
                "context_id": str(context.run_id),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return task_execution

    async def _submit_to_celery(
        self, task_execution: Any, queue_name: str  # TaskExecution
    ) -> str:
        """Submit task to Celery with proper routing."""

        # Prepare task execution data
        task_execution_data = {
            "task_id": str(task_execution.id),
            "agent_type": task_execution.definition.agent_type,
            "inputs": task_execution.inputs,
            "metadata": task_execution.metadata,
            "timeout_seconds": task_execution.definition.timeout_seconds,
        }

        # Submit to Celery with queue routing
        celery_task = submit_agent_task(
            agent_type=task_execution.definition.agent_type,
            task_execution_data=task_execution_data,
            project_id=str(task_execution.project_id),
            run_id=str(task_execution.run_id),
            node_id=str(task_execution.id),
            queue=queue_name,
        )

        # Store active task reference
        self.active_tasks[task_execution.id] = celery_task

        logger.info(
            f"Task {task_execution.id} submitted to Celery with ID: {celery_task.id}"
        )
        return celery_task.id

    async def _wait_for_completion(
        self, task_id: UUID, celery_task_id: str, timeout: int = 300
    ) -> Dict[str, Any]:
        """Wait for Celery task completion with timeout."""

        celery_task = self.active_tasks.get(task_id)
        if not celery_task:
            raise ValueError(f"Task {task_id} not found in active tasks")

        try:
            logger.info(f"Waiting for task {task_id} completion (timeout: {timeout}s)")

            # Wait for completion with timeout
            result = await asyncio.wait_for(
                self._wait_for_celery_result(celery_task), timeout=timeout
            )

            logger.info(f"Task {task_id} completed successfully")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out after {timeout} seconds")
            raise TimeoutError(f"Task {task_id} timed out")
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            raise

    async def _wait_for_celery_result(self, celery_task: AsyncResult) -> Dict[str, Any]:
        """Convert Celery result to async with proper error handling."""

        while not celery_task.ready():
            await asyncio.sleep(1)

        if celery_task.successful():
            return celery_task.get()
        else:
            error_msg = f"Celery task failed: {celery_task.result}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _map_node_type_to_task_type(self, dag_node: Any) -> str:
        """Map DAG node type to TaskType enum."""
        # Default mapping - can be enhanced based on actual DAG node structure
        node_type = getattr(dag_node, "type", "default")

        type_mapping = {
            "planning": "planning",
            "specification": "specification",
            "architecture": "architecture",
            "coding": "coding",
            "testing": "testing",
            "review": "review",
            "performance": "performance",
            "default": "analysis",
        }

        return type_mapping.get(node_type, "analysis")

    def _cleanup_task(self, task_id: UUID) -> None:
        """Clean up task from active tracking."""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        if task_id in self.task_executions:
            del self.task_executions[task_id]

    async def cleanup_completed_tasks(self) -> int:
        """Clean up completed tasks from memory."""
        completed_count = 0
        completed_tasks = []

        for task_id, celery_task in self.active_tasks.items():
            if celery_task.ready():
                completed_tasks.append(task_id)
                completed_count += 1

        for task_id in completed_tasks:
            self._cleanup_task(task_id)

        if completed_count > 0:
            logger.info(f"Cleaned up {completed_count} completed tasks")

        return completed_count


class TaskExecutionError(Exception):
    """Exception raised for task execution errors."""

    pass
