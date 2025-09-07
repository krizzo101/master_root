"""
Integration scaffolding for ExecutionPlan functionality
Connects new features to the working GenericOrchestrator foundation
"""
import json
import sys
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# Import working orchestrator components
sys.path.append(str(Path(__file__).parent.parent / "src"))
from generic_orchestrator import AgentTask, GenericOrchestrator


@dataclass
class ExecutionPlanTask:
    """ExecutionPlan task that maps to working orchestrator AgentTask"""

    id: str
    type: str
    prompt: str
    depends: List[str] = None
    quality_gates: List[str] = None
    meta: Dict[str, Any] = None

    def to_agent_task(self) -> AgentTask:
        """Convert to working orchestrator AgentTask format"""
        return AgentTask(
            task_id=self.id,
            task_type=self.type,
            prompt=self.prompt,
            dependencies=self.depends or [],
            context=self.meta or {},
        )


@dataclass
class ExecutionPlan:
    """ExecutionPlan that integrates with working orchestrator"""

    id: str
    name: str
    description: str
    tasks: List[ExecutionPlanTask]
    execution_mode: str = "parallel"
    enable_quality_gates: bool = False
    enable_monitoring: bool = False
    use_optimizations: bool = True

    def to_agent_tasks(self) -> List[AgentTask]:
        """Convert ExecutionPlan to working orchestrator tasks"""
        return [task.to_agent_task() for task in self.tasks]


class QualityGate(ABC):
    """Abstract quality gate that can validate tasks"""

    @abstractmethod
    async def validate(self, task: AgentTask) -> Dict[str, Any]:
        """Validate task before/after execution"""
        pass


class BasicQualityGate(QualityGate):
    """Basic quality gate implementation"""

    async def validate(self, task: AgentTask) -> Dict[str, Any]:
        """Basic validation - ensure task has required fields"""
        issues = []

        if not task.task_id:
            issues.append("Missing task_id")
        if not task.prompt:
            issues.append("Missing prompt")
        if not task.task_type:
            issues.append("Missing task_type")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "gate_type": "basic_validation",
        }


class BasicMonitor:
    """Basic monitoring that works with current orchestrator"""

    def __init__(self):
        self.metrics = {
            "tasks_started": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "execution_time": 0,
        }

    async def log_task_start(self, task_id: str):
        """Log task start"""
        self.metrics["tasks_started"] += 1
        print(f"[MONITOR] Task started: {task_id}")

    async def log_task_completion(self, task_id: str, status: str, duration: float):
        """Log task completion"""
        if status == "completed":
            self.metrics["tasks_completed"] += 1
        else:
            self.metrics["tasks_failed"] += 1

        self.metrics["execution_time"] += duration
        print(f"[MONITOR] Task {status}: {task_id} ({duration:.2f}s)")

    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        return self.metrics.copy()


class ExecutionPlanOrchestrator:
    """Enhanced orchestrator that adds ExecutionPlan support to working GenericOrchestrator"""

    def __init__(self, output_dir: Path, max_parallel: int = 5):
        self.generic_orchestrator = GenericOrchestrator(
            output_dir=output_dir, max_parallel=max_parallel, use_optimizations=True
        )
        self.quality_gates = [BasicQualityGate()]
        self.monitor = BasicMonitor()

    async def execute_plan(self, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute ExecutionPlan using working orchestrator foundation"""
        print(f"Executing ExecutionPlan: {execution_plan.name}")
        print(
            f"Tasks: {len(execution_plan.tasks)}, Mode: {execution_plan.execution_mode}"
        )

        # Convert ExecutionPlan to working orchestrator format
        agent_tasks = execution_plan.to_agent_tasks()

        # Add quality gate validation if enabled
        if execution_plan.enable_quality_gates:
            validated_tasks = []
            for task in agent_tasks:
                for gate in self.quality_gates:
                    validation_result = await gate.validate(task)
                    if not validation_result["passed"]:
                        print(
                            f"Quality gate failed for {task.task_id}: {validation_result['issues']}"
                        )
                        task.status = "failed"
                        task.error = (
                            f"Quality gate validation failed: "
                            f"{validation_result['issues']}"
                        )
                    else:
                        print(f"Quality gate passed for {task.task_id}")
                validated_tasks.append(task)
            agent_tasks = validated_tasks

        # Execute using working orchestrator
        results = await self.generic_orchestrator.execute_batch(agent_tasks)

        # Add monitoring metrics if enabled
        execution_result = {
            "execution_mode": execution_plan.execution_mode,
            "results": results,
            "quality_gates_enabled": execution_plan.enable_quality_gates,
            "monitoring_enabled": execution_plan.enable_monitoring,
        }

        if execution_plan.enable_monitoring:
            execution_result["monitoring_metrics"] = self.monitor.get_metrics()

        return execution_result


def create_execution_plan_from_json(file_path: str) -> ExecutionPlan:
    """Load ExecutionPlan from JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)

    tasks = []
    for task_data in data.get("tasks", []):
        task = ExecutionPlanTask(
            id=task_data["id"],
            type=task_data["type"],
            prompt=task_data["prompt"],
            depends=task_data.get("depends", []),
            quality_gates=task_data.get("quality_gates", []),
            meta=task_data.get("meta", {}),
        )
        tasks.append(task)

    return ExecutionPlan(
        id=data["id"],
        name=data["name"],
        description=data["description"],
        tasks=tasks,
        execution_mode=data.get("execution_mode", "parallel"),
        enable_quality_gates=data.get("enable_quality_gates", False),
        enable_monitoring=data.get("enable_monitoring", False),
        use_optimizations=data.get("use_optimizations", True),
    )


# Test integration with current working orchestrator
async def test_integration():
    """Test that ExecutionPlan integrates with working orchestrator"""
    from pathlib import Path

    # Create test ExecutionPlan
    test_plan = ExecutionPlan(
        id="test_plan",
        name="Integration Test Plan",
        description="Test ExecutionPlan integration with working orchestrator",
        tasks=[
            ExecutionPlanTask(
                id="test_task_1",
                type="research",
                prompt="Test research task for integration",
            ),
            ExecutionPlanTask(
                id="test_task_2",
                type="code",
                prompt="Test code task that depends on research",
                depends=["test_task_1"],
            ),
        ],
        enable_quality_gates=True,
        enable_monitoring=True,
    )

    # Test orchestrator
    orchestrator = ExecutionPlanOrchestrator(
        output_dir=Path(tempfile.mkdtemp(prefix="execution_plan_test_")), max_parallel=2
    )

    print("Testing ExecutionPlan integration...")
    result = await orchestrator.execute_plan(test_plan)

    print(f"Integration test result: {result['execution_mode']}")
    print(f"Quality gates enabled: {result['quality_gates_enabled']}")
    print(f"Monitoring enabled: {result['monitoring_enabled']}")

    return result


if __name__ == "__main__":
    # Run integration test
    import asyncio

    asyncio.run(test_integration())
