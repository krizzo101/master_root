#!/usr/bin/env python3
"""
Orchestrator Execution Plan Schema

Defines the schema and data structures for execution plans that agents can generate
when working with the agent orchestrator system. These plans control how the
orchestrator will execute tasks with dependencies, quality gates, and monitoring.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ExecutionMode(Enum):
    """Execution mode for the orchestrator"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"  # Some tasks parallel, others sequential based on dependencies


class TaskType(Enum):
    """Common task types for agent orchestration"""

    # Core agent types
    GENERAL_PURPOSE = "general-purpose"
    DEVELOPMENT_SPECIALIST = "development-specialist"
    API_INTEGRATION_SPECIALIST = "api-integration-specialist"
    QA_TESTING_GURU = "qa-testing-guru"
    TECHNICAL_WRITER = "technical-writer"

    # Specialized agents
    DATABASE_SPECIALIST = "database-specialist"
    SECURITY_ARCHITECT = "security-architect"
    PERFORMANCE_OPTIMIZER = "performance-optimizer"
    SOLUTION_ARCHITECT = "solution-architect"
    REQUIREMENTS_ANALYST = "requirements-analyst"

    # SDLC agents
    SDLC_DISCOVERY = "sdlc-discovery"
    SDLC_DESIGN = "sdlc-design"
    SDLC_DEVELOPMENT = "sdlc-development"
    SDLC_TESTING = "sdlc-testing"
    SDLC_DEPLOYMENT = "sdlc-deployment"
    SDLC_PRODUCTION = "sdlc-production"


class QualityGateType(Enum):
    """Types of quality gates"""

    DATABASE = "database"
    HTTP = "http"
    FILE_EXISTS = "file_exists"
    CODE_QUALITY = "code_quality"
    TEST_RESULTS = "test_results"
    CUSTOM = "custom"


class ValidationLevel(Enum):
    """Validation levels for tasks and deliverables"""

    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


@dataclass
class QualityGate:
    """Quality gate definition for execution plans"""

    gate_id: str
    name: str
    description: str
    gate_type: QualityGateType
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_interval: int = 30
    max_retries: int = 10
    enabled: bool = True


@dataclass
class ExecutionPhase:
    """Execution phase grouping related tasks"""

    phase_id: str
    name: str
    description: str
    gates: List[str] = field(default_factory=list)  # Quality gates for this phase
    parallel_execution: bool = True
    max_parallel: Optional[int] = None
    timeout_seconds: Optional[int] = None


@dataclass
class TaskDefinition:
    """Task definition for execution plans"""

    task_id: str
    task_type: Union[TaskType, str]  # Allow custom task types
    prompt: str

    # Dependencies and execution control
    dependencies: List[str] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    phase_id: Optional[str] = None

    # Context and configuration
    context: Dict[str, Any] = field(default_factory=dict)
    working_directory: Optional[str] = None
    output_files: List[str] = field(default_factory=list)

    # Validation and monitoring
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    monitoring_enabled: bool = True
    background_execution: bool = False

    # Agent identification (for log tracking)
    agent_uuid: Optional[str] = None
    team_id: Optional[str] = None

    # Retry and timeout configuration
    max_retries: int = 0
    retry_delay: int = 30
    timeout_seconds: Optional[int] = None

    # Priority and resource allocation
    priority: int = 0  # Higher numbers = higher priority
    estimated_duration_minutes: Optional[int] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """Complete execution plan for the orchestrator"""

    # Plan metadata
    plan_id: str
    name: str
    description: str
    version: str = "1.0"
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    # Execution configuration
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    max_parallel_tasks: int = 10
    enable_quality_gates: bool = True
    enable_monitoring: bool = True
    use_optimizations: bool = True

    # Tasks and structure
    tasks: List[TaskDefinition] = field(default_factory=list)
    phases: List[ExecutionPhase] = field(default_factory=list)
    quality_gates: List[QualityGate] = field(default_factory=list)

    # Resource management
    token_requirements: int = 1  # Number of Claude tokens needed
    estimated_total_duration_minutes: Optional[int] = None

    # Output and results
    output_directory: Optional[str] = None
    result_processing: Optional[Dict[str, Any]] = None

    # Monitoring and notifications
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    notification_config: Dict[str, Any] = field(default_factory=dict)

    # Fallback and error handling
    fallback_strategy: str = "fail_fast"  # fail_fast, continue, retry_failed
    error_handling: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""

        def convert_value(value):
            if isinstance(value, Enum):
                return value.value
            elif hasattr(value, "__dict__"):
                return {k: convert_value(v) for k, v in value.__dict__.items()}
            elif isinstance(value, list):
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return value

        return convert_value(self.__dict__)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        """Create ExecutionPlan from dictionary"""
        # Convert string enums back to enum objects
        if "execution_mode" in data and isinstance(data["execution_mode"], str):
            data["execution_mode"] = ExecutionMode(data["execution_mode"])

        # Convert tasks
        if "tasks" in data:
            tasks = []
            for task_data in data["tasks"]:
                if "task_type" in task_data and isinstance(task_data["task_type"], str):
                    try:
                        task_data["task_type"] = TaskType(task_data["task_type"])
                    except ValueError:
                        # Allow custom task types as strings
                        pass

                if "validation_level" in task_data and isinstance(
                    task_data["validation_level"], str
                ):
                    task_data["validation_level"] = ValidationLevel(
                        task_data["validation_level"]
                    )

                tasks.append(TaskDefinition(**task_data))
            data["tasks"] = tasks

        # Convert phases
        if "phases" in data:
            phases = [ExecutionPhase(**phase_data) for phase_data in data["phases"]]
            data["phases"] = phases

        # Convert quality gates
        if "quality_gates" in data:
            gates = []
            for gate_data in data["quality_gates"]:
                if "gate_type" in gate_data and isinstance(gate_data["gate_type"], str):
                    gate_data["gate_type"] = QualityGateType(gate_data["gate_type"])
                gates.append(QualityGate(**gate_data))
            data["quality_gates"] = gates

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        """Create ExecutionPlan from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> List[str]:
        """Validate the execution plan and return list of errors"""
        errors = []

        # Check required fields
        if not self.plan_id:
            errors.append("plan_id is required")
        if not self.name:
            errors.append("name is required")
        if not self.tasks:
            errors.append("At least one task is required")

        # Validate task IDs are unique
        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("Task IDs must be unique")

        # Validate dependencies reference existing tasks
        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"Task {task.task_id} has unknown dependency: {dep}")

        # Validate quality gates referenced by tasks exist
        gate_ids = [gate.gate_id for gate in self.quality_gates]
        for task in self.tasks:
            for gate_id in task.quality_gates:
                if gate_id not in gate_ids:
                    errors.append(
                        f"Task {task.task_id} references unknown quality gate: {gate_id}"
                    )

        # Validate phases reference existing gates
        for phase in self.phases:
            for gate_id in phase.gates:
                if gate_id not in gate_ids:
                    errors.append(
                        f"Phase {phase.phase_id} references unknown quality gate: {gate_id}"
                    )

        # Check for circular dependencies
        def has_circular_dependency(task_id: str, visited: set, path: set) -> bool:
            if task_id in path:
                return True
            if task_id in visited:
                return False

            visited.add(task_id)
            path.add(task_id)

            task = next((t for t in self.tasks if t.task_id == task_id), None)
            if task:
                for dep in task.dependencies:
                    if has_circular_dependency(dep, visited, path):
                        return True

            path.remove(task_id)
            return False

        visited = set()
        for task in self.tasks:
            if task.task_id not in visited:
                if has_circular_dependency(task.task_id, visited, set()):
                    errors.append(
                        f"Circular dependency detected involving task {task.task_id}"
                    )

        return errors

    def get_execution_order(self) -> List[List[str]]:
        """Get execution order respecting dependencies (returns batches that can run in parallel)"""
        remaining_tasks = {task.task_id: task for task in self.tasks}
        completed_tasks = set()
        execution_batches = []

        while remaining_tasks:
            # Find tasks that can run now (dependencies satisfied)
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                if all(dep in completed_tasks for dep in task.dependencies):
                    ready_tasks.append(task_id)

            if not ready_tasks:
                # No tasks can run - must be circular dependency
                raise ValueError(
                    f"Circular dependency or invalid dependencies. Remaining tasks: {list(remaining_tasks.keys())}"
                )

            # Add batch and mark as completed
            execution_batches.append(ready_tasks)
            for task_id in ready_tasks:
                completed_tasks.add(task_id)
                del remaining_tasks[task_id]

        return execution_batches
