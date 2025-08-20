"""PlannerAgent - Creates and manages execution plans."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    DEFERRED = 5


@dataclass
class Task:
    """Individual task in an execution plan."""

    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # seconds
    assigned_agent: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """Complete execution plan with tasks and dependencies."""

    id: str
    goal: str
    tasks: List[Task]
    total_estimated_duration: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_met = all(
                self.get_task(dep_id)
                and self.get_task(dep_id).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )

            if deps_met:
                ready.append(task)

        return sorted(ready, key=lambda t: t.priority.value)

    def is_complete(self) -> bool:
        """Check if plan execution is complete."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
            for task in self.tasks
        )

    def has_failures(self) -> bool:
        """Check if any tasks have failed."""
        return any(task.status == TaskStatus.FAILED for task in self.tasks)

    def get_completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if not self.tasks:
            return 0.0

        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100


class PlannerAgent(BaseAgent):
    """Creates and manages execution plans for complex goals."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize planner agent."""
        super().__init__(
            config
            or AgentConfig(
                name="PlannerAgent",
                description="Creates and manages execution plans",
                capabilities=[
                    "planning",
                    "decomposition",
                    "scheduling",
                    "optimization",
                ],
                max_retries=3,
                timeout=60,
            )
        )
        self.plans: Dict[str, ExecutionPlan] = {}
        self._plan_counter = 0

    def initialize(self) -> bool:
        """Initialize the planner agent."""
        logger.info("planner_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning task."""
        action = task.get("action", "plan")

        if action == "plan":
            return self._create_plan(task)
        elif action == "update":
            return self._update_plan(task)
        elif action == "optimize":
            return self._optimize_plan(task)
        elif action == "get_ready":
            return self._get_ready_tasks(task)
        elif action == "status":
            return self._get_plan_status(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def plan(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """Create execution plan for a goal."""
        result = self.execute(
            {"action": "plan", "goal": goal, "context": context or {}}
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["plan"]

    def _create_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create new execution plan."""
        goal = task.get("goal", "")
        context = task.get("context", {})

        if not goal:
            return {"error": "Goal is required"}

        # Generate plan ID
        self._plan_counter += 1
        plan_id = f"plan_{self._plan_counter}"

        # Decompose goal into tasks
        tasks = self._decompose_goal(goal, context)

        # Build dependency graph
        tasks = self._build_dependencies(tasks, context)

        # Estimate durations
        total_duration = self._estimate_duration(tasks)

        # Create plan
        plan = ExecutionPlan(
            id=plan_id,
            goal=goal,
            tasks=tasks,
            total_estimated_duration=total_duration,
            metadata=context,
        )

        # Store plan
        self.plans[plan_id] = plan

        logger.info(
            "plan_created",
            plan_id=plan_id,
            goal=goal,
            task_count=len(tasks),
            estimated_duration=total_duration,
        )

        return {
            "plan": plan,
            "plan_id": plan_id,
            "task_count": len(tasks),
            "estimated_duration": total_duration,
        }

    def _decompose_goal(self, goal: str, context: Dict[str, Any]) -> List[Task]:
        """Decompose goal into atomic tasks."""
        tasks = []

        # Analyze goal complexity
        complexity = self._analyze_complexity(goal)

        if complexity == "simple":
            # Single task for simple goals
            tasks.append(
                Task(
                    id="task_1",
                    name="Execute Goal",
                    description=goal,
                    priority=TaskPriority.MEDIUM,
                )
            )
        elif complexity == "moderate":
            # Break into 3-5 tasks
            tasks.extend(
                [
                    Task(
                        id="task_1",
                        name="Analyze Requirements",
                        description=f"Analyze requirements for: {goal}",
                        priority=TaskPriority.HIGH,
                    ),
                    Task(
                        id="task_2",
                        name="Design Solution",
                        description=f"Design solution approach",
                        priority=TaskPriority.HIGH,
                    ),
                    Task(
                        id="task_3",
                        name="Implement Solution",
                        description=f"Implement the designed solution",
                        priority=TaskPriority.MEDIUM,
                    ),
                    Task(
                        id="task_4",
                        name="Validate Results",
                        description=f"Validate implementation meets requirements",
                        priority=TaskPriority.MEDIUM,
                    ),
                ]
            )
        else:  # complex
            # Break into multiple phases
            tasks.extend(
                [
                    Task(
                        id="task_1",
                        name="Discovery Phase",
                        description="Gather information and analyze requirements",
                        priority=TaskPriority.CRITICAL,
                    ),
                    Task(
                        id="task_2",
                        name="Planning Phase",
                        description="Create detailed implementation plan",
                        priority=TaskPriority.CRITICAL,
                    ),
                    Task(
                        id="task_3",
                        name="Design Phase",
                        description="Design system architecture and components",
                        priority=TaskPriority.HIGH,
                    ),
                    Task(
                        id="task_4",
                        name="Development Phase",
                        description="Implement core functionality",
                        priority=TaskPriority.HIGH,
                    ),
                    Task(
                        id="task_5",
                        name="Integration Phase",
                        description="Integrate components and systems",
                        priority=TaskPriority.MEDIUM,
                    ),
                    Task(
                        id="task_6",
                        name="Testing Phase",
                        description="Comprehensive testing and validation",
                        priority=TaskPriority.MEDIUM,
                    ),
                    Task(
                        id="task_7",
                        name="Deployment Phase",
                        description="Deploy and monitor solution",
                        priority=TaskPriority.LOW,
                    ),
                ]
            )

        # Add required capabilities based on goal keywords
        for task in tasks:
            task.required_capabilities = self._infer_capabilities(task.description)

        return tasks

    def _build_dependencies(
        self, tasks: List[Task], context: Dict[str, Any]
    ) -> List[Task]:
        """Build task dependency graph."""
        if len(tasks) <= 1:
            return tasks

        # Simple linear dependencies for now
        # Can be enhanced with parallel task detection
        for i in range(1, len(tasks)):
            tasks[i].dependencies = [tasks[i - 1].id]

        # Detect parallelizable tasks
        parallel_keywords = ["test", "document", "monitor"]
        for i, task in enumerate(tasks):
            if any(keyword in task.name.lower() for keyword in parallel_keywords):
                # These can run in parallel with previous task
                if i > 0 and tasks[i - 1].id in task.dependencies:
                    task.dependencies.remove(tasks[i - 1].id)
                    if i > 1:
                        task.dependencies.append(tasks[i - 2].id)

        return tasks

    def _estimate_duration(self, tasks: List[Task]) -> int:
        """Estimate total plan duration in seconds."""
        # Simple estimation based on task count and complexity
        base_duration = 30  # Base time per task

        total = 0
        for task in tasks:
            # Estimate based on priority (higher priority = more complex)
            multiplier = 6 - task.priority.value  # 5 for CRITICAL, 1 for DEFERRED
            task.estimated_duration = base_duration * multiplier

            # Add to total if not parallelizable
            if not task.dependencies or len(task.dependencies) == len(tasks) - 1:
                total += task.estimated_duration

        return total

    def _analyze_complexity(self, goal: str) -> str:
        """Analyze goal complexity."""
        # Simple heuristic based on goal length and keywords
        complex_keywords = [
            "system",
            "architecture",
            "integrate",
            "optimize",
            "refactor",
        ]
        moderate_keywords = ["implement", "create", "build", "develop", "design"]

        goal_lower = goal.lower()

        if any(keyword in goal_lower for keyword in complex_keywords):
            return "complex"
        elif any(keyword in goal_lower for keyword in moderate_keywords):
            return "moderate"
        elif len(goal.split()) > 10:
            return "moderate"
        else:
            return "simple"

    def _infer_capabilities(self, description: str) -> List[str]:
        """Infer required capabilities from task description."""
        capabilities = []
        desc_lower = description.lower()

        capability_keywords = {
            "analyze": ["analysis", "research"],
            "design": ["design", "architecture"],
            "implement": ["execution", "development"],
            "test": ["testing", "validation"],
            "deploy": ["deployment", "operations"],
            "document": ["documentation", "reporting"],
            "optimize": ["optimization", "performance"],
            "integrate": ["integration", "orchestration"],
        }

        for keyword, caps in capability_keywords.items():
            if keyword in desc_lower:
                capabilities.extend(caps)

        return capabilities or ["execution"]

    def _update_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing plan."""
        plan_id = task.get("plan_id")
        task_id = task.get("task_id")
        status = task.get("status")
        result = task.get("result")
        error = task.get("error")

        if not plan_id or plan_id not in self.plans:
            return {"error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]

        if task_id:
            task_obj = plan.get_task(task_id)
            if not task_obj:
                return {"error": f"Task {task_id} not found in plan {plan_id}"}

            if status:
                task_obj.status = TaskStatus[status.upper()]
            if result is not None:
                task_obj.result = result
            if error:
                task_obj.error = error
                task_obj.retry_count += 1

        return {"plan": plan, "updated": True}

    def _optimize_plan(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize execution plan."""
        plan_id = task.get("plan_id")

        if not plan_id or plan_id not in self.plans:
            return {"error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]

        # Identify optimization opportunities
        optimizations = []

        # Find parallelizable tasks
        for task_obj in plan.tasks:
            if len(task_obj.dependencies) > 1:
                # Check if dependencies can be reduced
                deps_completed = all(
                    plan.get_task(dep).status == TaskStatus.COMPLETED
                    for dep in task_obj.dependencies[:-1]
                )
                if deps_completed:
                    task_obj.dependencies = [task_obj.dependencies[-1]]
                    optimizations.append(f"Reduced dependencies for {task_obj.name}")

        # Reorder by priority
        pending_tasks = [t for t in plan.tasks if t.status == TaskStatus.PENDING]
        if pending_tasks:
            pending_tasks.sort(key=lambda t: t.priority.value)
            optimizations.append("Reordered tasks by priority")

        return {"plan": plan, "optimizations": optimizations}

    def _get_ready_tasks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get tasks ready for execution."""
        plan_id = task.get("plan_id")

        if not plan_id or plan_id not in self.plans:
            return {"error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]
        ready_tasks = plan.get_ready_tasks()

        return {
            "plan_id": plan_id,
            "ready_tasks": ready_tasks,
            "count": len(ready_tasks),
        }

    def _get_plan_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get plan execution status."""
        plan_id = task.get("plan_id")

        if not plan_id or plan_id not in self.plans:
            return {"error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]

        return {
            "plan_id": plan_id,
            "is_complete": plan.is_complete(),
            "has_failures": plan.has_failures(),
            "completion_percentage": plan.get_completion_percentage(),
            "total_tasks": len(plan.tasks),
            "completed_tasks": sum(
                1 for t in plan.tasks if t.status == TaskStatus.COMPLETED
            ),
            "failed_tasks": sum(1 for t in plan.tasks if t.status == TaskStatus.FAILED),
            "pending_tasks": sum(
                1 for t in plan.tasks if t.status == TaskStatus.PENDING
            ),
            "ready_tasks": len(plan.get_ready_tasks()),
        }

    def shutdown(self) -> bool:
        """Shutdown the planner agent."""
        logger.info("planner_agent_shutdown", plans_count=len(self.plans))
        self.plans.clear()
        return True
