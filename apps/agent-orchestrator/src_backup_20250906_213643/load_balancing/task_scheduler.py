"""
Advanced Task Scheduler
Intelligent task queuing, prioritization, and scheduling for optimal execution
"""
import asyncio
import heapq
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class SchedulingPolicy(Enum):
    """Task scheduling policies"""

    FIFO = "fifo"  # First In, First Out
    PRIORITY_QUEUE = "priority_queue"
    SHORTEST_JOB_FIRST = "shortest_job_first"
    DEADLINE_AWARE = "deadline_aware"
    FAIR_SHARE = "fair_share"
    ADAPTIVE = "adaptive"


@dataclass
class ScheduledTask:
    """Task with scheduling metadata"""

    task_id: str
    priority: TaskPriority
    estimated_duration: float = 60.0  # seconds
    deadline: Optional[float] = None  # timestamp
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "ScheduledTask") -> bool:
        """Comparison for priority queue (lower priority value = higher priority)"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value

        # Secondary sort by creation time for same priority
        return self.created_at < other.created_at

    @property
    def is_overdue(self) -> bool:
        """Check if task is past its deadline"""
        return self.deadline is not None and time.time() > self.deadline

    @property
    def urgency_score(self) -> float:
        """Calculate urgency score (0-1, higher = more urgent)"""
        current_time = time.time()

        # Base urgency from priority
        priority_urgency = 1.0 / self.priority.value

        # Deadline urgency
        deadline_urgency = 0.0
        if self.deadline:
            time_to_deadline = self.deadline - current_time
            if time_to_deadline > 0:
                # More urgent as deadline approaches
                deadline_urgency = max(
                    0, 1.0 - (time_to_deadline / self.estimated_duration)
                )
            else:
                deadline_urgency = 1.0  # Overdue

        # Age urgency (tasks get more urgent over time)
        age = current_time - self.created_at
        age_urgency = min(0.5, age / 3600)  # Max 0.5 urgency from age (1 hour)

        return min(
            1.0, priority_urgency * 0.5 + deadline_urgency * 0.3 + age_urgency * 0.2
        )

    @property
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries


class TaskScheduler:
    """Advanced task scheduler with multiple policies and intelligent queuing"""

    def __init__(
        self,
        policy: SchedulingPolicy = SchedulingPolicy.ADAPTIVE,
        max_queue_size: int = 1000,
        fair_share_weights: Optional[Dict[str, float]] = None,
    ):
        self.policy = policy
        self.max_queue_size = max_queue_size
        self.fair_share_weights = fair_share_weights or {}

        # Task queues - different data structures for different policies
        self._priority_queue: List[ScheduledTask] = []  # heap
        self._fifo_queue: deque[ScheduledTask] = deque()
        self._deadline_queue: List[ScheduledTask] = []  # heap sorted by deadline

        # Task tracking
        self._all_tasks: Dict[str, ScheduledTask] = {}
        self._pending_tasks: Set[str] = set()
        self._running_tasks: Set[str] = set()
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Set[str] = set()

        # Dependency tracking
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(
            set
        )  # task_id -> dependents
        self._blocked_tasks: Dict[str, Set[str]] = defaultdict(
            set
        )  # task_id -> blocking tasks

        # Fair share tracking
        self._fair_share_usage: Dict[str, float] = defaultdict(
            float
        )  # category -> usage time
        self._fair_share_categories: Dict[str, str] = {}  # task_id -> category

        # Statistics
        self._scheduling_stats = {
            "total_scheduled": 0,
            "total_completed": 0,
            "total_failed": 0,
            "average_wait_time": 0.0,
            "average_execution_time": 0.0,
        }

        logger.info("TaskScheduler initialized with policy: %s", policy.value)

    def schedule_task(
        self, task: ScheduledTask, category: Optional[str] = None
    ) -> bool:
        """Schedule a new task"""
        if len(self._all_tasks) >= self.max_queue_size:
            logger.error("Task queue full, cannot schedule task %s", task.task_id)
            return False

        if task.task_id in self._all_tasks:
            logger.warning("Task %s already scheduled", task.task_id)
            return False

        # Validate dependencies
        for dep_id in task.dependencies:
            if dep_id not in self._all_tasks and dep_id not in self._completed_tasks:
                logger.error(
                    "Task %s has unresolved dependency: %s", task.task_id, dep_id
                )
                return False

        # Add to tracking
        self._all_tasks[task.task_id] = task
        self._pending_tasks.add(task.task_id)
        task.scheduled_at = time.time()

        # Set up dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                self._dependency_graph[dep_id].add(task.task_id)
                if dep_id not in self._completed_tasks:
                    self._blocked_tasks[task.task_id].add(dep_id)

        # Fair share category
        if category:
            self._fair_share_categories[task.task_id] = category

        # Add to appropriate queue
        if not self._blocked_tasks[task.task_id]:  # Not blocked by dependencies
            self._add_to_queue(task)

        self._scheduling_stats["total_scheduled"] += 1

        logger.debug(
            "Scheduled task %s with priority %s", task.task_id, task.priority.value
        )
        return True

    def get_next_task(self) -> Optional[ScheduledTask]:
        """Get the next task to execute based on scheduling policy"""
        if self.policy == SchedulingPolicy.FIFO:
            return self._get_next_fifo()
        elif self.policy == SchedulingPolicy.PRIORITY_QUEUE:
            return self._get_next_priority()
        elif self.policy == SchedulingPolicy.SHORTEST_JOB_FIRST:
            return self._get_next_shortest_job()
        elif self.policy == SchedulingPolicy.DEADLINE_AWARE:
            return self._get_next_deadline_aware()
        elif self.policy == SchedulingPolicy.FAIR_SHARE:
            return self._get_next_fair_share()
        elif self.policy == SchedulingPolicy.ADAPTIVE:
            return self._get_next_adaptive()
        else:
            return self._get_next_priority()  # Default fallback

    def complete_task(
        self, task_id: str, execution_time: float, success: bool = True
    ) -> None:
        """Mark task as completed and update dependencies"""
        if task_id not in self._all_tasks:
            logger.warning("Cannot complete unknown task: %s", task_id)
            return

        task = self._all_tasks[task_id]

        # Update task state
        if success:
            self._running_tasks.discard(task_id)
            self._completed_tasks.add(task_id)

            # Update fair share usage
            category = self._fair_share_categories.get(task_id)
            if category:
                self._fair_share_usage[category] += execution_time

            # Release dependent tasks
            for dependent_id in self._dependency_graph[task_id]:
                if dependent_id in self._blocked_tasks:
                    self._blocked_tasks[dependent_id].discard(task_id)

                    # If no more blocking dependencies, add to queue
                    if (
                        not self._blocked_tasks[dependent_id]
                        and dependent_id in self._pending_tasks
                    ):
                        dependent_task = self._all_tasks[dependent_id]
                        self._add_to_queue(dependent_task)

            self._scheduling_stats["total_completed"] += 1
        else:
            # Task failed
            if task.can_retry:
                # Retry the task
                task.retry_count += 1
                self._running_tasks.discard(task_id)
                self._pending_tasks.add(task_id)
                self._add_to_queue(task)
                logger.info(
                    "Retrying task %s (attempt %d/%d)",
                    task_id,
                    task.retry_count + 1,
                    task.max_retries + 1,
                )
            else:
                # Task permanently failed
                self._running_tasks.discard(task_id)
                self._failed_tasks.add(task_id)
                self._scheduling_stats["total_failed"] += 1
                logger.error(
                    "Task %s failed permanently after %d attempts",
                    task_id,
                    task.retry_count + 1,
                )

        # Update statistics
        if task.started_at:
            wait_time = task.started_at - task.created_at
            self._update_average_stat("average_wait_time", wait_time)
            self._update_average_stat("average_execution_time", execution_time)

    def start_task(self, task_id: str) -> bool:
        """Mark task as started"""
        if task_id not in self._all_tasks:
            return False

        task = self._all_tasks[task_id]
        task.started_at = time.time()

        self._pending_tasks.discard(task_id)
        self._running_tasks.add(task_id)

        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        if task_id not in self._all_tasks:
            return False

        task = self._all_tasks[task_id]

        # Remove from queues
        self._remove_from_queues(task)

        # Update state
        self._pending_tasks.discard(task_id)
        self._running_tasks.discard(task_id)

        # Clean up dependencies
        for dependent_id in self._dependency_graph[task_id]:
            self._blocked_tasks[dependent_id].add("CANCELLED_DEPENDENCY")

        del self._all_tasks[task_id]

        logger.info("Cancelled task %s", task_id)
        return True

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics"""
        return {
            "policy": self.policy.value,
            "queue_sizes": {
                "priority": len(self._priority_queue),
                "fifo": len(self._fifo_queue),
                "deadline": len(self._deadline_queue),
            },
            "task_counts": {
                "total": len(self._all_tasks),
                "pending": len(self._pending_tasks),
                "running": len(self._running_tasks),
                "completed": len(self._completed_tasks),
                "failed": len(self._failed_tasks),
                "blocked": sum(
                    1 for blocked in self._blocked_tasks.values() if blocked
                ),
            },
            "statistics": dict(self._scheduling_stats),
            "fair_share_usage": dict(self._fair_share_usage),
        }

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific task"""
        if task_id not in self._all_tasks:
            return None

        task = self._all_tasks[task_id]

        return {
            "task_id": task.task_id,
            "priority": task.priority.value,
            "estimated_duration": task.estimated_duration,
            "deadline": task.deadline,
            "dependencies": task.dependencies,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "created_at": task.created_at,
            "scheduled_at": task.scheduled_at,
            "started_at": task.started_at,
            "is_overdue": task.is_overdue,
            "urgency_score": task.urgency_score,
            "can_retry": task.can_retry,
            "status": self._get_task_status(task_id),
            "blocking_dependencies": list(self._blocked_tasks.get(task_id, set())),
            "dependent_tasks": list(self._dependency_graph.get(task_id, set())),
            "metadata": task.metadata,
        }

    def _add_to_queue(self, task: ScheduledTask) -> None:
        """Add task to appropriate queue based on policy"""
        if self.policy == SchedulingPolicy.FIFO:
            self._fifo_queue.append(task)
        else:
            # Most policies use priority queue
            heapq.heappush(self._priority_queue, task)

            # Also add to deadline queue if deadline-aware
            if self.policy == SchedulingPolicy.DEADLINE_AWARE and task.deadline:
                # Sort by deadline
                deadline_task = (task.deadline, task)
                heapq.heappush(self._deadline_queue, deadline_task)

    def _remove_from_queues(self, task: ScheduledTask) -> None:
        """Remove task from all queues (expensive operation)"""
        # Remove from FIFO queue
        try:
            self._fifo_queue.remove(task)
        except ValueError:
            pass

        # Remove from priority queue (rebuild heap)
        try:
            self._priority_queue.remove(task)
            heapq.heapify(self._priority_queue)
        except ValueError:
            pass

        # Remove from deadline queue
        self._deadline_queue = [
            (deadline, t)
            for deadline, t in self._deadline_queue
            if t.task_id != task.task_id
        ]
        heapq.heapify(self._deadline_queue)

    def _get_next_fifo(self) -> Optional[ScheduledTask]:
        """Get next task using FIFO policy"""
        return self._fifo_queue.popleft() if self._fifo_queue else None

    def _get_next_priority(self) -> Optional[ScheduledTask]:
        """Get next task using priority queue policy"""
        return heapq.heappop(self._priority_queue) if self._priority_queue else None

    def _get_next_shortest_job(self) -> Optional[ScheduledTask]:
        """Get next task with shortest estimated duration"""
        if not self._priority_queue:
            return None

        # Find task with shortest duration
        min_task = min(self._priority_queue, key=lambda t: t.estimated_duration)
        self._priority_queue.remove(min_task)
        heapq.heapify(self._priority_queue)
        return min_task

    def _get_next_deadline_aware(self) -> Optional[ScheduledTask]:
        """Get next task considering deadlines and urgency"""
        if not self._priority_queue:
            return None

        # Check for overdue tasks first
        overdue_tasks = [t for t in self._priority_queue if t.is_overdue]
        if overdue_tasks:
            # Get highest priority overdue task
            min_task = min(overdue_tasks, key=lambda t: t.priority.value)
            self._priority_queue.remove(min_task)
            heapq.heapify(self._priority_queue)
            return min_task

        # Get task with highest urgency score
        max_urgency_task = max(self._priority_queue, key=lambda t: t.urgency_score)
        self._priority_queue.remove(max_urgency_task)
        heapq.heapify(self._priority_queue)
        return max_urgency_task

    def _get_next_fair_share(self) -> Optional[ScheduledTask]:
        """Get next task using fair share policy"""
        if not self._priority_queue:
            return None

        # Group tasks by category
        task_by_category = defaultdict(list)
        for task in self._priority_queue:
            category = self._fair_share_categories.get(task.task_id, "default")
            task_by_category[category].append(task)

        # Find category with least usage relative to weight
        min_usage_category = None
        min_usage_ratio = float("inf")

        for category, tasks in task_by_category.items():
            weight = self.fair_share_weights.get(category, 1.0)
            usage = self._fair_share_usage[category]
            usage_ratio = usage / weight

            if usage_ratio < min_usage_ratio:
                min_usage_ratio = usage_ratio
                min_usage_category = category

        if min_usage_category:
            # Get highest priority task from selected category
            category_tasks = task_by_category[min_usage_category]
            selected_task = min(category_tasks, key=lambda t: t.priority.value)
            self._priority_queue.remove(selected_task)
            heapq.heapify(self._priority_queue)
            return selected_task

        return None

    def _get_next_adaptive(self) -> Optional[ScheduledTask]:
        """Adaptive scheduling based on current conditions"""
        if not self._priority_queue:
            return None

        # Analyze current conditions
        total_tasks = len(self._all_tasks)
        overdue_count = sum(1 for t in self._priority_queue if t.is_overdue)
        high_priority_count = sum(
            1
            for t in self._priority_queue
            if t.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]
        )

        # Adaptive strategy selection
        if overdue_count > 0:
            # Overdue tasks exist - use deadline aware
            return self._get_next_deadline_aware()
        elif high_priority_count / total_tasks > 0.3:
            # Many high priority tasks - use priority
            return self._get_next_priority()
        elif len(self._fair_share_categories) > 1:
            # Multiple categories - use fair share
            return self._get_next_fair_share()
        else:
            # Default to shortest job first for efficiency
            return self._get_next_shortest_job()

    def _get_task_status(self, task_id: str) -> str:
        """Get current status of a task"""
        if task_id in self._running_tasks:
            return "running"
        elif task_id in self._completed_tasks:
            return "completed"
        elif task_id in self._failed_tasks:
            return "failed"
        elif task_id in self._pending_tasks:
            if self._blocked_tasks.get(task_id):
                return "blocked"
            else:
                return "pending"
        else:
            return "unknown"

    def _update_average_stat(self, stat_name: str, new_value: float) -> None:
        """Update running average statistic"""
        current_avg = self._scheduling_stats.get(stat_name, 0.0)
        total_completed = max(1, self._scheduling_stats["total_completed"])

        # Simple moving average
        updated_avg = (
            (current_avg * (total_completed - 1)) + new_value
        ) / total_completed
        self._scheduling_stats[stat_name] = round(updated_avg, 3)

    def set_policy(self, policy: SchedulingPolicy) -> None:
        """Change scheduling policy"""
        old_policy = self.policy
        self.policy = policy

        # Rebuild queues for new policy
        all_pending_tasks = [
            self._all_tasks[task_id]
            for task_id in self._pending_tasks
            if not self._blocked_tasks.get(task_id)
        ]

        # Clear existing queues
        self._priority_queue.clear()
        self._fifo_queue.clear()
        self._deadline_queue.clear()

        # Re-add tasks to appropriate queues
        for task in all_pending_tasks:
            self._add_to_queue(task)

        logger.info(
            "Scheduling policy changed from %s to %s", old_policy.value, policy.value
        )
