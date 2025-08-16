"""Task Router - Intelligent task routing to appropriate Celery queues."""

import logging
from typing import Dict, Optional, Any
from opsvi_auto_forge.application.orchestrator.task_models import (
    TaskExecution,
    TaskPriority,
    TaskType,
)

logger = logging.getLogger(__name__)


class TaskRouter:
    """Intelligent task routing to appropriate Celery queues.

    This component provides the missing intelligent task routing functionality
    identified in the gap analysis, ensuring tasks are routed to appropriate
    queues based on multiple factors.
    """

    def __init__(self):
        """Initialize the Task Router with queue mappings and priorities."""

        # Agent type to queue mapping
        self.queue_mapping = {
            "planner": "default",
            "specifier": "default",
            "architect": "heavy",
            "coder": "heavy",
            "tester": "test",
            "critic": "default",
            "perf_smoke": "test",
            "perf_opt": "heavy",
            "security_validator": "test",
            "syntax_fixer": "default",
            "assurance_orchestrator": "heavy",
            "base_repair": "default",
        }

        # Queue priority levels (higher number = higher priority)
        self.queue_priorities = {"default": 1, "heavy": 2, "test": 3, "io": 4}

        # Task type to queue mapping
        self.task_type_mapping = {
            TaskType.PLANNING: "default",
            TaskType.SPECIFICATION: "default",
            TaskType.ARCHITECTURE: "heavy",
            TaskType.CODING: "heavy",
            TaskType.TESTING: "test",
            TaskType.REVIEW: "default",
            TaskType.DEPLOYMENT: "heavy",
            TaskType.ANALYSIS: "default",
            TaskType.PERFORMANCE: "heavy",
        }

        # Queue capacity limits
        self.queue_capacity = {"default": 50, "heavy": 20, "test": 30, "io": 100}

        logger.info("TaskRouter initialized successfully")

    def route_task(self, task_execution: TaskExecution) -> str:
        """Route task to appropriate queue based on multiple factors.

        Args:
            task_execution: Task execution to route

        Returns:
            Queue name to route the task to
        """
        try:
            logger.debug(f"Routing task {task_execution.id}")

            # 1. Check agent type mapping
            agent_type = task_execution.definition.agent_type
            if agent_type in self.queue_mapping:
                base_queue = self.queue_mapping[agent_type]
            else:
                base_queue = "default"

            # 2. Apply priority adjustments
            if task_execution.definition.priority == TaskPriority.CRITICAL:
                logger.debug(
                    f"Task {task_execution.id} is critical, routing to heavy queue"
                )
                return "heavy"  # Critical tasks go to heavy queue

            # 3. Check task type requirements
            task_type = task_execution.definition.type
            if task_type in self.task_type_mapping:
                type_queue = self.task_type_mapping[task_type]
                if (
                    self.queue_priorities[type_queue]
                    > self.queue_priorities[base_queue]
                ):
                    base_queue = type_queue

            # 4. Check estimated duration
            if task_execution.definition.timeout_seconds > 600:  # 10 minutes
                logger.debug(
                    f"Task {task_execution.id} has long timeout, routing to heavy queue"
                )
                return "heavy"

            # 5. Check queue capacity (if available)
            if hasattr(self, "_queue_loads"):
                queue_loads = self._queue_loads
                if base_queue in queue_loads:
                    current_load = queue_loads[base_queue]
                    capacity = self.queue_capacity.get(base_queue, 50)

                    if current_load >= capacity * 0.9:  # 90% capacity
                        # Try to find alternative queue
                        alternative = self._find_alternative_queue(
                            base_queue, queue_loads
                        )
                        if alternative:
                            logger.debug(
                                f"Queue {base_queue} at capacity, routing to {alternative}"
                            )
                            return alternative

            logger.debug(f"Task {task_execution.id} routed to queue: {base_queue}")
            return base_queue

        except Exception as e:
            logger.error(f"Failed to route task {task_execution.id}: {e}")
            return "default"  # Fallback to default queue

    def route_task_by_agent(self, agent_type: str) -> str:
        """Route task based on agent type only.

        Args:
            agent_type: Type of agent

        Returns:
            Queue name
        """
        return self.queue_mapping.get(agent_type, "default")

    def route_task_by_type(self, task_type: TaskType) -> str:
        """Route task based on task type only.

        Args:
            task_type: Type of task

        Returns:
            Queue name
        """
        return self.task_type_mapping.get(task_type, "default")

    def get_queue_priority(self, queue_name: str) -> int:
        """Get priority level for a queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Priority level (higher number = higher priority)
        """
        return self.queue_priorities.get(queue_name, 1)

    def get_queue_capacity(self, queue_name: str) -> int:
        """Get capacity limit for a queue.

        Args:
            queue_name: Name of the queue

        Returns:
            Capacity limit
        """
        return self.queue_capacity.get(queue_name, 50)

    def set_queue_loads(self, queue_loads: Dict[str, int]) -> None:
        """Set current queue loads for capacity-aware routing.

        Args:
            queue_loads: Dictionary mapping queue names to current load
        """
        self._queue_loads = queue_loads

    def _find_alternative_queue(
        self, preferred_queue: str, queue_loads: Dict[str, int]
    ) -> Optional[str]:
        """Find alternative queue when preferred queue is at capacity.

        Args:
            preferred_queue: Preferred queue name
            queue_loads: Current queue loads

        Returns:
            Alternative queue name or None if none available
        """
        preferred_priority = self.queue_priorities.get(preferred_queue, 1)

        # Find queues with similar or higher priority that have capacity
        alternatives = []
        for queue_name, load in queue_loads.items():
            if queue_name == preferred_queue:
                continue

            priority = self.queue_priorities.get(queue_name, 1)
            capacity = self.queue_capacity.get(queue_name, 50)

            # Prefer queues with similar or higher priority and available capacity
            if priority >= preferred_priority and load < capacity * 0.8:
                alternatives.append((queue_name, priority, load))

        if alternatives:
            # Sort by priority (descending) then by load (ascending)
            alternatives.sort(key=lambda x: (-x[1], x[2]))
            return alternatives[0][0]

        return None

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics and configuration.

        Returns:
            Dictionary with routing statistics
        """
        return {
            "queue_mapping": self.queue_mapping,
            "queue_priorities": self.queue_priorities,
            "task_type_mapping": {
                k.value: v for k, v in self.task_type_mapping.items()
            },
            "queue_capacity": self.queue_capacity,
            "queue_loads": getattr(self, "_queue_loads", {}),
        }

    def update_queue_mapping(self, agent_type: str, queue_name: str) -> None:
        """Update queue mapping for an agent type.

        Args:
            agent_type: Agent type to update
            queue_name: New queue name
        """
        if queue_name in self.queue_priorities:
            self.queue_mapping[agent_type] = queue_name
            logger.info(f"Updated queue mapping for {agent_type}: {queue_name}")
        else:
            logger.warning(f"Invalid queue name: {queue_name}")

    def update_queue_capacity(self, queue_name: str, capacity: int) -> None:
        """Update capacity for a queue.

        Args:
            queue_name: Queue name to update
            capacity: New capacity limit
        """
        if capacity > 0:
            self.queue_capacity[queue_name] = capacity
            logger.info(f"Updated capacity for {queue_name}: {capacity}")
        else:
            logger.warning(f"Invalid capacity: {capacity}")


class TaskRoutingError(Exception):
    """Exception raised for task routing errors."""

    pass
