"""Pydantic models for task orchestration and tracking."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Types of tasks in the pipeline."""

    PLAN = "plan"
    SPEC = "spec"
    ARCHITECTURE = "architecture"
    CODE = "code"
    TEST = "test"
    VALIDATE = "validate"
    DOCUMENT = "document"
    RESEARCH = "research"
    CRITIC = "critic"


class Metrics(BaseModel):
    """Task execution metrics."""

    tokens_used: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    mocked: bool = False
    retry_count: int = 0


class TaskRecord(BaseModel):
    """Record of a task execution."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # Execution context
    project_id: UUID
    run_id: UUID
    parent_task_id: UUID | None = None

    # Input/Output
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None
    error_message: str | None = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Metrics
    metrics: Metrics = Field(default_factory=Metrics)

    # Dependencies and flow control
    depends_on: list[UUID] = Field(default_factory=list)
    gate_policies: list[str] = Field(default_factory=list)
    max_loops: int = 1
    current_loop: int = 0
    fallback_task: str | None = None

    # Agent information
    agent_path: str
    agent_config: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """Artifact produced by a task."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    artifact_type: str  # "code", "docs", "tests", "config", etc.
    file_path: str
    content_hash: str
    size_bytes: int
    mime_type: str

    # Metadata
    task_id: UUID
    project_id: UUID
    run_id: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Content (for small artifacts)
    content: str | None = None

    # Derived from
    derived_from: list[UUID] = Field(default_factory=list)


class Result(BaseModel):
    """Result of a task execution."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)

    # Metrics
    metrics: Metrics = Field(default_factory=Metrics)

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: int = 0


class Critique(BaseModel):
    """Critique/Evaluation of a task or artifact."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    artifact_id: UUID | None = None

    # Evaluation scores
    overall_score: float = Field(ge=0.0, le=1.0)
    policy_scores: dict[str, float] = Field(default_factory=dict)

    # Results
    pass_threshold: bool = False
    reasons: list[str] = Field(default_factory=list)

    # Patch plan for failures
    patch_plan: list[dict[str, Any]] = Field(default_factory=list)

    # Metadata
    critic_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    """Project being processed."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    request: str

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)

    # Status
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Run(BaseModel):
    """A single execution run of a project."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    pipeline_name: str

    # Status
    status: str = "running"
    current_task: str | None = None

    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)

    # Results
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
