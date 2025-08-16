"""Task models for the orchestrator."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from opsvi_auto_forge.config.models import AgentRole, TaskStatus


class TaskType(str, Enum):
    """Types of tasks in the pipeline."""

    PLANNING = "planning"
    SPECIFICATION = "specification"
    ARCHITECTURE = "architecture"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    PERFORMANCE = "performance"


class TaskPriority(int, Enum):
    """Task priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskDefinition(BaseModel):
    """Definition of a task type."""

    name: str
    type: TaskType
    agent_type: str
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_attempts: int = 3
    priority: TaskPriority = TaskPriority.NORMAL
    queue: str = "default"
    required: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class TaskExecution(BaseModel):
    """Execution instance of a task."""

    id: UUID
    definition: TaskDefinition
    project_id: UUID
    run_id: UUID
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    result_id: Optional[UUID] = None
    critique_id: Optional[UUID] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
    )

    @field_validator("execution_time_seconds")
    @classmethod
    def validate_execution_time(cls, v: Optional[float]) -> Optional[float]:
        """Validate execution time is positive."""
        if v is not None and v < 0:
            raise ValueError("Execution time must be positive")
        return v

    @field_validator("memory_usage_mb")
    @classmethod
    def validate_memory_usage(cls, v: Optional[float]) -> Optional[float]:
        """Validate memory usage is positive."""
        if v is not None and v < 0:
            raise ValueError("Memory usage must be positive")
        return v

    @field_validator("cpu_usage_percent")
    @classmethod
    def validate_cpu_usage(cls, v: Optional[float]) -> Optional[float]:
        """Validate CPU usage is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("CPU usage must be between 0 and 100")
        return v


class TaskDependency(BaseModel):
    """Dependency relationship between tasks."""

    task_id: UUID
    depends_on: UUID
    type: str = "completion"  # completion, artifact, result
    condition: Optional[str] = None  # Optional condition for dependency
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class TaskSchedule(BaseModel):
    """Schedule for task execution."""

    task_id: UUID
    run_id: UUID
    scheduled_at: datetime
    priority: TaskPriority = TaskPriority.NORMAL
    queue: str = "default"
    retry_delay_seconds: int = 60
    max_retries: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
    )


class TaskResult(BaseModel):
    """Result of task execution."""

    task_id: UUID
    status: TaskStatus
    score: float = Field(..., ge=0.0, le=1.0)
    metrics: Dict[str, Union[float, int, str]] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    execution_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            UUID: lambda v: str(v),
        },
    )

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Validate score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0 and 1")
        return v


class TaskRegistry(BaseModel):
    """Registry of available task definitions."""

    tasks: Dict[str, TaskDefinition] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def register_task(self, task: TaskDefinition) -> None:
        """Register a task definition."""
        self.tasks[task.name] = task

    def get_task(self, name: str) -> Optional[TaskDefinition]:
        """Get a task definition by name."""
        return self.tasks.get(name)

    def list_tasks(self) -> List[str]:
        """List all registered task names."""
        return list(self.tasks.keys())

    def remove_task(self, name: str) -> bool:
        """Remove a task definition."""
        if name in self.tasks:
            del self.tasks[name]
            return True
        return False


class TaskExecutionPlan(BaseModel):
    """Plan for task execution with dependencies and ordering."""

    task_id: UUID
    task_name: str
    stage_name: str
    agent: AgentRole
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[UUID] = Field(default_factory=list)
    dependents: List[UUID] = Field(default_factory=list)
    execution_phase: int = 0  # Phase number for parallel execution
    estimated_duration: Optional[float] = None
    timeout_seconds: int = 300
    retry_attempts: int = 3
    queue: str = "default"
    required: bool = True
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            UUID: lambda v: str(v),
        },
    )

    @field_validator("execution_phase")
    @classmethod
    def validate_execution_phase(cls, v: int) -> int:
        """Validate execution phase is non-negative."""
        if v < 0:
            raise ValueError("Execution phase must be non-negative")
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("retry_attempts")
    @classmethod
    def validate_retry_attempts(cls, v: int) -> int:
        """Validate retry attempts is non-negative."""
        if v < 0:
            raise ValueError("Retry attempts must be non-negative")
        return v
