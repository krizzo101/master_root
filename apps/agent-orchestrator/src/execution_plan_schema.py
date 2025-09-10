"""
ExecutionPlan Schema Definition
Comprehensive data classes and enums for the ExecutionPlan system
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TaskType(Enum):
    """All available agent types for ExecutionPlan tasks"""

    # Core specialized agents
    GENERAL_PURPOSE = "general-purpose"
    RESEARCH_GENIUS = "research-genius"
    SOLUTION_ARCHITECT = "solution-architect"
    DEVELOPMENT_SPECIALIST = "development-specialist"
    QA_TESTING_GURU = "qa-testing-guru"
    TECHNICAL_WRITER = "technical-writer"

    # SDLC specialized agents
    SDLC_DISCOVERY = "sdlc-discovery"
    SDLC_DESIGN = "sdlc-design"
    SDLC_PLANNING = "sdlc-planning"
    SDLC_DEVELOPMENT = "sdlc-development"
    SDLC_TESTING = "sdlc-testing"
    SDLC_DEPLOYMENT = "sdlc-deployment"
    SDLC_PRODUCTION = "sdlc-production"
    SDLC_POSTMORTEM = "sdlc-postmortem"

    # Domain specialists
    DATABASE_SPECIALIST = "database-specialist"
    API_INTEGRATION_SPECIALIST = "api-integration-specialist"
    PERFORMANCE_OPTIMIZER = "performance-optimizer"
    SECURITY_ARCHITECT = "security-architect"
    DEVOPS_AUTOMATION = "devops-automation"

    # Analysis and architecture
    REQUIREMENTS_ANALYST = "requirements-analyst"
    BUSINESS_ANALYST = "business-analyst"
    CODE_ANALYZER = "code-analyzer"
    REFACTORING_MASTER = "refactoring-master"

    # Quality and management
    REVIEWER_CRITIC = "reviewer-critic"
    EXCELLENCE_OPTIMIZER = "excellence-optimizer"
    CEO_TEAM_MANAGER = "ceo-team-manager"

    # Specialized generators
    PROMPT_GENERATOR = "prompt-generator"


class ValidationLevel(Enum):
    """Validation strictness levels"""

    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    CRITICAL = "critical"


class ExecutionMode(Enum):
    """ExecutionPlan execution modes"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    MIXED = "mixed"
    AUTO = "auto"


class QualityGateType(Enum):
    """Quality gate validation types"""

    DATABASE = "database"
    HTTP = "http"
    FILE_EXISTS = "file_exists"
    CODE_QUALITY = "code_quality"
    TEST_RESULTS = "test_results"
    CUSTOM = "custom"
    SCHEMA_VALIDATION = "schema_validation"
    DEPENDENCY_CHECK = "dependency_check"
    RESOURCE_VALIDATION = "resource_validation"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """Additional context for task execution"""

    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    files_to_read: List[str] = field(default_factory=list)
    output_directory: Optional[str] = None
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "working_directory": self.working_directory,
            "environment_variables": self.environment_variables,
            "files_to_read": self.files_to_read,
            "output_directory": self.output_directory,
            "custom_properties": self.custom_properties,
        }


@dataclass
class QualityGate:
    """Quality gate definition for validation checkpoints"""

    gate_id: str
    name: str
    description: str
    gate_type: QualityGateType
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    enabled: bool = True
    critical: bool = False

    def __post_init__(self):
        if not self.gate_id.strip():
            raise ValueError("Quality gate ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Quality gate name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "description": self.description,
            "gate_type": self.gate_type.value,
            "config": self.config,
            "dependencies": self.dependencies,
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "critical": self.critical,
        }


@dataclass
class TaskDefinition:
    """Complete task definition for ExecutionPlan"""

    task_id: str
    task_type: TaskType
    prompt: str

    # Dependencies and execution control
    dependencies: List[str] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    phase_id: Optional[str] = None

    # Configuration
    context: Optional[TaskContext] = None
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    priority: TaskPriority = TaskPriority.NORMAL

    # Execution settings
    timeout_seconds: int = 1800  # 30 minutes default
    max_retries: int = 2
    background_execution: bool = False
    monitoring_enabled: bool = True

    # Estimation and planning
    estimated_duration_minutes: Optional[int] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id.strip():
            raise ValueError("Task ID cannot be empty")
        if not self.prompt.strip():
            raise ValueError("Task prompt cannot be empty")

        # Ensure TaskType enum
        if isinstance(self.task_type, str):
            try:
                self.task_type = TaskType(self.task_type)
            except ValueError:
                raise ValueError(f"Invalid task type: {self.task_type}")

        # Ensure ValidationLevel enum
        if isinstance(self.validation_level, str):
            try:
                self.validation_level = ValidationLevel(self.validation_level)
            except ValueError:
                self.validation_level = ValidationLevel.STANDARD

        # Ensure TaskPriority enum
        if isinstance(self.priority, str):
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            self.priority = priority_map.get(self.priority.lower(), TaskPriority.NORMAL)
        elif isinstance(self.priority, int):
            # Convert int to closest enum value
            if self.priority <= 2:
                self.priority = TaskPriority.LOW
            elif self.priority <= 6:
                self.priority = TaskPriority.NORMAL
            elif self.priority <= 9:
                self.priority = TaskPriority.HIGH
            else:
                self.priority = TaskPriority.CRITICAL

        # Initialize context if None
        if self.context is None:
            self.context = TaskContext()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "prompt": self.prompt,
            "dependencies": self.dependencies,
            "quality_gates": self.quality_gates,
            "phase_id": self.phase_id,
            "context": self.context.to_dict() if self.context else None,
            "validation_level": self.validation_level.value,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "background_execution": self.background_execution,
            "monitoring_enabled": self.monitoring_enabled,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "resource_requirements": self.resource_requirements,
        }


@dataclass
class ExecutionPhase:
    """Logical grouping of related tasks"""

    phase_id: str
    name: str
    description: str
    gates: List[str] = field(default_factory=list)
    parallel_execution: bool = True
    max_parallel: int = 3
    timeout_seconds: int = 3600
    depends_on_phases: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.phase_id.strip():
            raise ValueError("Phase ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Phase name cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,
            "gates": self.gates,
            "parallel_execution": self.parallel_execution,
            "max_parallel": self.max_parallel,
            "timeout_seconds": self.timeout_seconds,
            "depends_on_phases": self.depends_on_phases,
        }


@dataclass
class ResourceRequirements:
    """Resource requirements for plan execution"""

    estimated_tokens: int = 5
    peak_parallel: int = 3
    memory_requirements_mb: int = 512
    estimated_duration_minutes: int = 60
    critical_path_duration_minutes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimated_tokens": self.estimated_tokens,
            "peak_parallel": self.peak_parallel,
            "memory_requirements_mb": self.memory_requirements_mb,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "critical_path_duration_minutes": self.critical_path_duration_minutes,
        }


@dataclass
class ExecutionPlan:
    """Complete ExecutionPlan specification"""

    plan_id: str
    name: str
    description: str
    tasks: List[TaskDefinition]

    # Execution configuration
    version: str = "1.0"
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    max_parallel_tasks: int = 5
    enable_quality_gates: bool = True
    enable_monitoring: bool = True
    use_optimizations: bool = True

    # Optional components
    quality_gates: List[QualityGate] = field(default_factory=list)
    phases: List[ExecutionPhase] = field(default_factory=list)

    # Planning and resources
    resource_requirements: Optional[ResourceRequirements] = None
    output_directory: str = "./output"
    estimated_total_duration_minutes: Optional[int] = None

    # Error handling
    fallback_strategy: str = "continue"  # continue, stop, retry
    max_plan_retries: int = 1

    # Metadata
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.plan_id.strip():
            raise ValueError("Plan ID cannot be empty")
        if not self.name.strip():
            raise ValueError("Plan name cannot be empty")
        if not self.tasks:
            raise ValueError("ExecutionPlan must have at least one task")

        # Ensure ExecutionMode enum
        if isinstance(self.execution_mode, str):
            try:
                self.execution_mode = ExecutionMode(self.execution_mode)
            except ValueError:
                self.execution_mode = ExecutionMode.PARALLEL

        # Initialize resource requirements if None
        if self.resource_requirements is None:
            self.resource_requirements = ResourceRequirements()

        # Only do basic validation in __post_init__ - comprehensive validation is optional
        self._validate_basic_structure()

    def _validate_basic_structure(self):
        """Basic structural validation without dependency analysis"""
        # Only validate that tasks have proper structure, not dependencies
        for task in self.tasks:
            if not hasattr(task, "task_id") or not task.task_id:
                raise ValueError("All tasks must have a valid task_id")

    def validate_dependencies(self) -> List[str]:
        """Validate all task dependencies exist and return any issues"""
        # Import validation here to avoid circular imports
        try:
            from .execution_plan_validation import validate_execution_plan_strict
        except ImportError:
            from execution_plan_validation import validate_execution_plan_strict

        # Use the comprehensive validation system
        try:
            validate_execution_plan_strict(self)
            return []  # No issues found
        except Exception as e:
            # Convert validation errors to list format for backward compatibility
            error_message = str(e)
            raise ValueError(f"ExecutionPlan validation failed: {error_message}")

    def validate_comprehensive(self):
        """Comprehensive validation using the advanced validation system"""
        try:
            from .execution_plan_validation import validate_execution_plan
        except ImportError:
            from execution_plan_validation import validate_execution_plan

        return validate_execution_plan(self, strict=True)

    def get_task_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        """Get task by ID"""
        return next((task for task in self.tasks if task.task_id == task_id), None)

    def get_tasks_by_phase(self, phase_id: str) -> List[TaskDefinition]:
        """Get all tasks in a specific phase"""
        return [task for task in self.tasks if task.phase_id == phase_id]

    def get_tasks_by_type(self, task_type: TaskType) -> List[TaskDefinition]:
        """Get all tasks of specific type"""
        return [task for task in self.tasks if task.task_type == task_type]

    def get_quality_gate_by_id(self, gate_id: str) -> Optional[QualityGate]:
        """Get quality gate by ID"""
        return next(
            (gate for gate in self.quality_gates if gate.gate_id == gate_id), None
        )

    def get_execution_order(self) -> List[List[str]]:
        """Calculate execution order based on dependencies"""
        # Topological sort to determine execution batches
        task_deps = {task.task_id: set(task.dependencies) for task in self.tasks}
        # all_tasks = set(task_deps.keys())  # Unused variable removed
        execution_batches = []

        while task_deps:
            # Find tasks with no remaining dependencies
            ready_tasks = [task_id for task_id, deps in task_deps.items() if not deps]

            if not ready_tasks:
                # Check for circular dependencies
                remaining = list(task_deps.keys())
                raise ValueError(
                    f"Circular dependency detected among tasks: {remaining}"
                )

            execution_batches.append(ready_tasks)

            # Remove ready tasks and update dependencies
            for task_id in ready_tasks:
                del task_deps[task_id]

            for deps in task_deps.values():
                deps -= set(ready_tasks)

        return execution_batches

    def estimate_total_duration(self) -> int:
        """Estimate total execution duration in minutes"""
        if self.estimated_total_duration_minutes:
            return self.estimated_total_duration_minutes

        execution_order = self.get_execution_order()
        total_duration = 0

        for batch in execution_order:
            batch_duration = 0
            for task_id in batch:
                task = self.get_task_by_id(task_id)
                if task and task.estimated_duration_minutes:
                    batch_duration = max(
                        batch_duration, task.estimated_duration_minutes
                    )
            total_duration += batch_duration

        return total_duration or 60  # Default 1 hour if no estimates

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "execution_mode": self.execution_mode.value,
            "max_parallel_tasks": self.max_parallel_tasks,
            "enable_quality_gates": self.enable_quality_gates,
            "enable_monitoring": self.enable_monitoring,
            "use_optimizations": self.use_optimizations,
            "tasks": [task.to_dict() for task in self.tasks],
            "quality_gates": [gate.to_dict() for gate in self.quality_gates],
            "phases": [phase.to_dict() for phase in self.phases],
            "resource_requirements": (
                self.resource_requirements.to_dict()
                if self.resource_requirements
                else None
            ),
            "output_directory": self.output_directory,
            "estimated_total_duration_minutes": self.estimate_total_duration(),
            "fallback_strategy": self.fallback_strategy,
            "max_plan_retries": self.max_plan_retries,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionPlan":
        """Create ExecutionPlan from dictionary format

        Args:
            data: Dictionary containing ExecutionPlan data

        Returns:
            ExecutionPlan instance
        """
        # Convert task dicts to TaskDefinition instances
        tasks = []
        for task_data in data.get("tasks", []):
            # Convert task_type string to enum if needed
            if "task_type" in task_data and isinstance(task_data["task_type"], str):
                task_data["task_type"] = TaskType(task_data["task_type"])

            # Convert nested quality gates if present
            if "quality_gates" in task_data:
                task_gates = []
                for gate_data in task_data["quality_gates"]:
                    if isinstance(gate_data, dict):
                        if "gate_type" in gate_data and isinstance(
                            gate_data["gate_type"], str
                        ):
                            gate_data["gate_type"] = QualityGateType(
                                gate_data["gate_type"]
                            )
                        task_gates.append(QualityGate(**gate_data))
                    else:
                        task_gates.append(gate_data)
                task_data["quality_gates"] = task_gates

            tasks.append(TaskDefinition(**task_data))

        # Convert quality gates to QualityGate instances
        quality_gates = []
        for gate_data in data.get("quality_gates", []):
            if isinstance(gate_data, dict):
                if "gate_type" in gate_data and isinstance(gate_data["gate_type"], str):
                    gate_data["gate_type"] = QualityGateType(gate_data["gate_type"])
                quality_gates.append(QualityGate(**gate_data))
            else:
                quality_gates.append(gate_data)

        # Convert phases to ExecutionPhase instances
        phases = []
        for phase_data in data.get("phases", []):
            if isinstance(phase_data, dict):
                phases.append(ExecutionPhase(**phase_data))
            else:
                phases.append(phase_data)

        # Convert resource requirements if present
        resource_requirements = None
        if "resource_requirements" in data and data["resource_requirements"]:
            res_data = data["resource_requirements"]
            if isinstance(res_data, dict):
                resource_requirements = ResourceRequirements(**res_data)
            else:
                resource_requirements = res_data

        # Convert execution_mode string to enum if needed
        execution_mode = data.get("execution_mode", "parallel")
        if isinstance(execution_mode, str):
            execution_mode = ExecutionMode(execution_mode)

        # Build ExecutionPlan with converted components
        return cls(
            plan_id=data["plan_id"],
            name=data["name"],
            description=data["description"],
            tasks=tasks,
            version=data.get("version", "1.0"),
            execution_mode=execution_mode,
            max_parallel_tasks=data.get("max_parallel_tasks", 5),
            enable_quality_gates=data.get("enable_quality_gates", True),
            enable_monitoring=data.get("enable_monitoring", True),
            use_optimizations=data.get("use_optimizations", True),
            quality_gates=quality_gates,
            phases=phases,
            resource_requirements=resource_requirements,
            output_directory=data.get("output_directory", "./output"),
            estimated_total_duration_minutes=data.get(
                "estimated_total_duration_minutes"
            ),
            fallback_strategy=data.get("fallback_strategy", "continue"),
            max_plan_retries=data.get("max_plan_retries", 1),
            created_by=data.get("created_by"),
            created_at=data.get("created_at"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save ExecutionPlan to JSON file"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")


# Helper functions for common patterns
def create_task_definition(
    task_id: str, task_type: Union[TaskType, str], prompt: str, **kwargs
) -> TaskDefinition:
    """Helper to create TaskDefinition with proper type conversion"""
    if isinstance(task_type, str):
        task_type = TaskType(task_type)

    return TaskDefinition(task_id=task_id, task_type=task_type, prompt=prompt, **kwargs)


def create_quality_gate(
    gate_id: str,
    name: str,
    description: str,
    gate_type: Union[QualityGateType, str],
    config: Dict[str, Any] = None,
    **kwargs,
) -> QualityGate:
    """Helper to create QualityGate with proper type conversion"""
    if isinstance(gate_type, str):
        gate_type = QualityGateType(gate_type)

    return QualityGate(
        gate_id=gate_id,
        name=name,
        description=description,
        gate_type=gate_type,
        config=config or {},
        **kwargs,
    )


# Type aliases for convenience
Task = TaskDefinition
Gate = QualityGate
Phase = ExecutionPhase
Plan = ExecutionPlan
