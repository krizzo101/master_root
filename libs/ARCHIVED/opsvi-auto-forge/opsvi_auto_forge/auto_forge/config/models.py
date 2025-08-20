"""Core data models for the autonomous software factory."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class AgentRole(str, Enum):
    """Agent roles in the autonomous factory."""

    PLANNER = "planner"
    SPECIFIER = "specifier"
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    CRITIC = "critic"
    REPAIR = "repair"
    META = "meta"
    PERF_SMOKE = "perf_smoke"
    PERF_OPT = "perf_opt"


class ArtifactType(str, Enum):
    """Types of artifacts produced by tasks."""

    CODE = "code"
    DOCUMENTATION = "documentation"
    TEST = "test"
    CONFIG = "config"
    BUILD = "build"
    DEPLOY = "deploy"
    ANALYSIS = "analysis"
    REPORT = "report"
    PROJECT_SCAFFOLD = "project_scaffold"
    PROJECT_FINALIZATION = "project_finalization"
    GENERATED_CODE = "generated_code"


class ResultStatus(str, Enum):
    """Result status for task outcomes."""

    OK = "ok"
    FAIL = "fail"


class BaseEntity(BaseModel):
    """Base entity with common fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
        from_attributes=True,
        populate_by_name=True,
    )

    def model_dump(self, **kwargs):
        """Override model_dump to handle UUID and datetime serialization."""
        data = super().model_dump(**kwargs)
        # Ensure all UUIDs and datetimes are serialized as strings
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


class Artifact(BaseEntity):
    """Artifact produced by a task."""

    type: ArtifactType
    path: str
    hash: str = Field(..., description="SHA-256 hash of artifact content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    task_id: Optional[UUID] = Field(
        None, description="ID of the task that produced this artifact"
    )

    @field_validator("hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Validate SHA-256 hash format."""
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("Hash must be a valid SHA-256 hash")
        return v.lower()


class Result(BaseEntity):
    """Result of a task execution."""

    status: ResultStatus
    score: float = Field(..., ge=0.0, le=1.0)
    metrics: Dict[str, Union[float, int, str]] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class Critique(BaseEntity):
    """Critique of a task result by the critic agent."""

    passed: bool
    score: float = Field(..., ge=0.0, le=1.0)
    policy_scores: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
    patch_plan: List[Dict[str, Any]] = Field(default_factory=list)
    agent_id: UUID
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class Decision(BaseEntity):
    """Decision made by an agent."""

    by_agent: AgentRole
    why: str
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class TaskRecord(BaseEntity):
    """Record of a task execution."""

    name: str
    agent: AgentRole
    project_id: UUID
    run_id: UUID
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Artifact] = Field(default_factory=list)
    result: Optional[Result] = None
    critique: Optional[Critique] = None
    decisions: List[Decision] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    queue: str = "default"
    priority: int = 0
    score: float = Field(0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("score", mode="before")
    @classmethod
    def calculate_score(cls, v: Optional[float], info) -> float:
        """Calculate overall score from result and critique."""
        if v is not None:
            return v

        # Calculate from result and critique if available
        if hasattr(info.data, "result") and info.data.result:
            result_score = info.data.result.score
            if hasattr(info.data, "critique") and info.data.critique:
                critique_score = info.data.critique.score
                return (result_score + critique_score) / 2
            return result_score
        return 0.0


class Project(BaseEntity):
    """Project being developed by the autonomous factory."""

    name: str
    description: str
    requirements: List[str] = Field(default_factory=list)
    target_architecture: Optional[str] = None
    target_language: Optional[str] = None
    target_framework: Optional[str] = None
    budget_tokens: Optional[int] = None
    budget_cost: Optional[float] = None
    deadline: Optional[datetime] = None
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Run(BaseEntity):
    """A single run of the autonomous factory pipeline."""

    project_id: UUID
    pipeline_name: str
    status: str = "running"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """Configuration for a pipeline."""

    name: str
    version: str = "1.0.0"
    description: str
    steps: List[Dict[str, Any]]
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 3600
    max_parallel_tasks: int = 4
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelConfig(BaseModel):
    """Configuration for AI model usage."""

    provider: str  # openai, anthropic, etc.
    model: str
    temperature: float = Field(..., ge=0.0, le=2.0)
    max_tokens: int = Field(..., gt=0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    role: AgentRole
    ai_model_config: ModelConfig
    system_prompt: str
    max_iterations: int = 10
    timeout_seconds: int = 300
    retry_attempts: int = 3
    quality_threshold: float = 0.8
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Response models for API
class TaskResponse(BaseModel):
    """Response model for task operations."""

    task_id: UUID
    status: TaskStatus
    message: str
    data: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    """Response model for run operations."""

    run_id: UUID
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
