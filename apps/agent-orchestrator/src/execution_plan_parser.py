"""
ExecutionPlan Parser
Converts ExecutionPlan format to working GenericOrchestrator AgentTask format
Built on proven working orchestrator foundation
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from generic_orchestrator import AgentTask

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """ExecutionPlan execution modes"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"
    AUTO = "auto"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExecutionPlanTask:
    """ExecutionPlan task that maps cleanly to working orchestrator AgentTask"""

    id: str
    type: str
    prompt: str
    depends: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 600  # seconds
    retries: int = 0
    quality_gates: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task after initialization"""
        if not self.id or self.id.strip() == "":
            raise ValueError("Task ID cannot be empty")
        if not self.type or self.type.strip() == "":
            raise ValueError("Task type cannot be empty")
        if not self.prompt or self.prompt.strip() == "":
            raise ValueError("Task prompt cannot be empty")

        # Ensure priority is TaskPriority enum
        if isinstance(self.priority, str):
            try:
                self.priority = TaskPriority(self.priority)
            except ValueError:
                logger.warning(
                    f"Invalid priority '{self.priority}', defaulting to NORMAL"
                )
                self.priority = TaskPriority.NORMAL

    def to_agent_task(self) -> AgentTask:
        """Convert to working orchestrator AgentTask format"""
        # Build context with all additional information
        context = self.metadata.copy()
        context.update(
            {
                "priority": self.priority.value,
                "timeout": self.timeout,
                "retries": self.retries,
                "quality_gates": self.quality_gates,
                "original_execution_plan_task": True,
            }
        )

        return AgentTask(
            task_id=self.id,
            task_type=self.type,
            prompt=self.prompt,
            dependencies=self.depends,
            context=context,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return asdict(self)


@dataclass
class ExecutionPlan:
    """ExecutionPlan that integrates seamlessly with working GenericOrchestrator"""

    id: str
    name: str
    description: str
    tasks: List[ExecutionPlanTask]
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    max_parallel: int = 5
    timeout: int = 3600  # seconds
    enable_quality_gates: bool = True
    enable_monitoring: bool = True
    use_optimizations: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate execution plan after initialization"""
        if not self.id or self.id.strip() == "":
            raise ValueError("ExecutionPlan ID cannot be empty")
        if not self.name or self.name.strip() == "":
            raise ValueError("ExecutionPlan name cannot be empty")
        if not self.tasks:
            raise ValueError("ExecutionPlan must have at least one task")

        # Ensure execution_mode is ExecutionMode enum
        if isinstance(self.execution_mode, str):
            try:
                self.execution_mode = ExecutionMode(self.execution_mode)
            except ValueError:
                logger.warning(
                    f"Invalid execution mode '{self.execution_mode}', defaulting to PARALLEL"
                )
                self.execution_mode = ExecutionMode.PARALLEL

        # Validate task dependencies exist
        task_ids = {task.id for task in self.tasks}
        for task in self.tasks:
            for dep in task.depends:
                if dep not in task_ids:
                    raise ValueError(
                        f"Task '{task.id}' depends on non-existent task '{dep}'"
                    )

    def to_agent_tasks(self) -> List[AgentTask]:
        """Convert all tasks to working orchestrator AgentTask format"""
        return [task.to_agent_task() for task in self.tasks]

    def get_task_by_id(self, task_id: str) -> Optional[ExecutionPlanTask]:
        """Get task by ID"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[ExecutionPlanTask]:
        """Get all tasks with specific priority"""
        return [task for task in self.tasks if task.priority == priority]

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get dependency graph for visualization/analysis"""
        graph = {}
        for task in self.tasks:
            graph[task.id] = task.depends.copy()
        return graph

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": [task.to_dict() for task in self.tasks],
            "execution_mode": self.execution_mode.value,
            "max_parallel": self.max_parallel,
            "timeout": self.timeout,
            "enable_quality_gates": self.enable_quality_gates,
            "enable_monitoring": self.enable_monitoring,
            "use_optimizations": self.use_optimizations,
            "metadata": self.metadata,
        }


class ExecutionPlanParser:
    """Parser that converts various formats to ExecutionPlan"""

    @staticmethod
    def from_json_file(file_path: Union[str, Path]) -> ExecutionPlan:
        """Load ExecutionPlan from JSON file"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"ExecutionPlan file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ExecutionPlanParser.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in ExecutionPlan file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading ExecutionPlan from {file_path}: {e}")

    @staticmethod
    def from_json_string(json_string: str) -> ExecutionPlan:
        """Load ExecutionPlan from JSON string"""
        try:
            data = json.loads(json_string)
            return ExecutionPlanParser.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ExecutionPlan:
        """Load ExecutionPlan from dictionary"""
        # Parse tasks
        tasks = []
        for task_data in data.get("tasks", []):
            task = ExecutionPlanTask(
                id=task_data["id"],
                type=task_data["type"],
                prompt=task_data["prompt"],
                depends=task_data.get("depends", []),
                priority=task_data.get("priority", "normal"),
                timeout=task_data.get("timeout", 600),
                retries=task_data.get("retries", 0),
                quality_gates=task_data.get("quality_gates", []),
                metadata=task_data.get("metadata", {}),
            )
            tasks.append(task)

        # Create ExecutionPlan
        return ExecutionPlan(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            tasks=tasks,
            execution_mode=data.get("execution_mode", "parallel"),
            max_parallel=data.get("max_parallel", 5),
            timeout=data.get("timeout", 3600),
            enable_quality_gates=data.get("enable_quality_gates", True),
            enable_monitoring=data.get("enable_monitoring", True),
            use_optimizations=data.get("use_optimizations", True),
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def to_json_file(execution_plan: ExecutionPlan, file_path: Union[str, Path]):
        """Save ExecutionPlan to JSON file"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(execution_plan.to_dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def validate_execution_plan(execution_plan: ExecutionPlan) -> List[str]:
        """Validate ExecutionPlan and return list of issues"""
        issues = []

        # Check for circular dependencies
        def has_circular_dependency(
            task_id: str, visited: set, recursion_stack: set
        ) -> bool:
            visited.add(task_id)
            recursion_stack.add(task_id)

            task = execution_plan.get_task_by_id(task_id)
            if task:
                for dep in task.depends:
                    if dep in recursion_stack:
                        return True
                    if dep not in visited:
                        if has_circular_dependency(dep, visited, recursion_stack):
                            return True

            recursion_stack.remove(task_id)
            return False

        visited = set()
        for task in execution_plan.tasks:
            if task.id not in visited:
                if has_circular_dependency(task.id, visited, set()):
                    issues.append(
                        f"Circular dependency detected involving task '{task.id}'"
                    )

        # Check for orphaned dependencies
        task_ids = {task.id for task in execution_plan.tasks}
        for task in execution_plan.tasks:
            for dep in task.depends:
                if dep not in task_ids:
                    issues.append(
                        f"Task '{task.id}' depends on non-existent task '{dep}'"
                    )

        # Check for duplicate task IDs
        task_id_counts = {}
        for task in execution_plan.tasks:
            task_id_counts[task.id] = task_id_counts.get(task.id, 0) + 1

        for task_id, count in task_id_counts.items():
            if count > 1:
                issues.append(f"Duplicate task ID '{task_id}' found {count} times")

        return issues


class ExecutionPlanAdapter:
    """Adapter for integrating ExecutionPlan with GenericOrchestrator"""

    def __init__(self, working_orchestrator=None):
        self.working_orchestrator = working_orchestrator

    def adapt_for_orchestrator(self, execution_plan: ExecutionPlan) -> List[AgentTask]:
        """Adapt ExecutionPlan for use with working GenericOrchestrator"""
        agent_tasks = execution_plan.to_agent_tasks()

        # Add execution plan context to all tasks
        for task in agent_tasks:
            task.context.update(
                {
                    "execution_plan_id": execution_plan.id,
                    "execution_plan_name": execution_plan.name,
                    "execution_mode": execution_plan.execution_mode.value,
                    "quality_gates_enabled": execution_plan.enable_quality_gates,
                    "monitoring_enabled": execution_plan.enable_monitoring,
                }
            )

        return agent_tasks

    def create_execution_summary(
        self, execution_plan: ExecutionPlan, results: List[Dict]
    ) -> Dict[str, Any]:
        """Create execution summary combining ExecutionPlan info with results"""
        task_results = {result.get("task_id", ""): result for result in results}

        summary = {
            "execution_plan": {
                "id": execution_plan.id,
                "name": execution_plan.name,
                "description": execution_plan.description,
                "execution_mode": execution_plan.execution_mode.value,
                "total_tasks": len(execution_plan.tasks),
            },
            "execution_results": {
                "completed": sum(1 for r in results if r.get("status") == "completed"),
                "failed": sum(1 for r in results if r.get("status") == "failed"),
                "total": len(results),
            },
            "task_details": [],
        }

        # Add details for each task
        for task in execution_plan.tasks:
            result = task_results.get(task.id, {})
            summary["task_details"].append(
                {
                    "task_id": task.id,
                    "task_type": task.type,
                    "priority": task.priority.value,
                    "dependencies": task.depends,
                    "status": result.get("status", "unknown"),
                    "error": result.get("error"),
                    "start_time": result.get("start_time"),
                    "end_time": result.get("end_time"),
                }
            )

        return summary


# Convenience functions for common use cases
def create_execution_plan_from_json(file_path: str) -> ExecutionPlan:
    """Convenience function to create ExecutionPlan from JSON file"""
    return ExecutionPlanParser.from_json_file(file_path)


def create_simple_execution_plan(
    name: str, task_definitions: List[Dict[str, Any]]
) -> ExecutionPlan:
    """Create simple ExecutionPlan from task definitions"""
    tasks = []
    for i, task_def in enumerate(task_definitions):
        task = ExecutionPlanTask(
            id=task_def.get("id", f"task_{i+1}"),
            type=task_def["type"],
            prompt=task_def["prompt"],
            depends=task_def.get("depends", []),
            priority=task_def.get("priority", "normal"),
        )
        tasks.append(task)

    return ExecutionPlan(
        id=f"plan_{name.lower().replace(' ', '_')}",
        name=name,
        description=f"ExecutionPlan: {name}",
        tasks=tasks,
    )


# Testing function
def test_execution_plan_parser():
    """Test ExecutionPlan parser with sample data"""
    print("Testing ExecutionPlan parser...")

    # Create test execution plan
    test_data = {
        "id": "test_plan",
        "name": "Test ExecutionPlan",
        "description": "Testing ExecutionPlan parser functionality",
        "tasks": [
            {
                "id": "research_task",
                "type": "research",
                "prompt": "Research best practices for async programming",
                "priority": "high",
                "quality_gates": ["structure", "prompt"],
            },
            {
                "id": "design_task",
                "type": "design",
                "prompt": "Design system architecture based on research",
                "depends": ["research_task"],
                "priority": "normal",
            },
            {
                "id": "implement_task",
                "type": "code",
                "prompt": "Implement the designed system",
                "depends": ["design_task"],
                "priority": "high",
                "timeout": 900,
            },
        ],
        "execution_mode": "parallel",
        "enable_quality_gates": True,
        "enable_monitoring": True,
    }

    # Test parsing
    try:
        execution_plan = ExecutionPlanParser.from_dict(test_data)
        print(f"✓ Successfully parsed ExecutionPlan: {execution_plan.name}")
        print(f"  Tasks: {len(execution_plan.tasks)}")
        print(f"  Mode: {execution_plan.execution_mode.value}")

        # Test validation
        issues = ExecutionPlanParser.validate_execution_plan(execution_plan)
        if issues:
            print(f"✗ Validation issues: {issues}")
        else:
            print("✓ Validation passed")

        # Test conversion to AgentTasks
        agent_tasks = execution_plan.to_agent_tasks()
        print(f"✓ Converted to {len(agent_tasks)} AgentTask objects")

        # Test adapter
        adapter = ExecutionPlanAdapter()
        adapted_tasks = adapter.adapt_for_orchestrator(execution_plan)
        print(f"✓ Adapted {len(adapted_tasks)} tasks for orchestrator")

        return execution_plan

    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        return None


if __name__ == "__main__":
    test_execution_plan_parser()
