"""
Pydantic schemas for the Auto-Forge Factory API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class JobStatus(str, Enum):
    """Status of a development job."""

    PENDING = "pending"
    PLANNING = "planning"
    SPECIFYING = "specifying"
    ARCHITECTING = "architecting"
    CODING = "coding"
    TESTING = "testing"
    OPTIMIZING = "optimizing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents in the factory."""

    PLANNER = "planner"
    SPECIFIER = "specifier"
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    PERFORMANCE_OPTIMIZER = "performance_optimizer"
    SECURITY_VALIDATOR = "security_validator"
    SYNTAX_FIXER = "syntax_fixer"
    CRITIC = "critic"
    META_ORCHESTRATOR = "meta_orchestrator"


class Language(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    C_SHARP = "csharp"
    CPP = "cpp"
    PHP = "php"
    RUBY = "ruby"


class Framework(str, Enum):
    """Supported frameworks."""

    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    EXPRESS = "express"
    GIN = "gin"
    ECHO = "echo"
    ACTIX = "actix"
    ROCKET = "rocket"
    SPRING = "spring"
    ASPNET = "aspnet"
    LARAVEL = "laravel"
    RAILS = "rails"


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    DIGITALOCEAN = "digitalocean"
    HEROKU = "heroku"
    VERCEL = "vercel"
    NETLIFY = "netlify"


class BaseEntity(BaseModel):
    """Base entity with common fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
        from_attributes=True,
        populate_by_name=True,
    )


class DevelopmentRequest(BaseModel):
    """Request to develop software."""

    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Project description")
    requirements: List[str] = Field(..., description="List of requirements")
    target_language: Optional[Language] = Field(
        None, description="Target programming language"
    )
    target_framework: Optional[Framework] = Field(None, description="Target framework")
    target_architecture: Optional[str] = Field(
        None, description="Target architecture (microservices, monolith, etc.)"
    )
    cloud_provider: Optional[CloudProvider] = Field(
        None, description="Target cloud provider"
    )
    budget_tokens: Optional[int] = Field(
        None, description="Token budget for development"
    )
    budget_cost: Optional[float] = Field(
        None, description="Cost budget for development"
    )
    deadline: Optional[datetime] = Field(None, description="Project deadline")
    priority: int = Field(1, ge=1, le=10, description="Priority level (1-10)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AgentProgress(BaseModel):
    """Progress of an individual agent."""

    agent_type: AgentType
    status: JobStatus
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    current_task: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    artifacts_generated: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class JobProgress(BaseModel):
    """Overall progress of a development job."""

    job_id: UUID
    status: JobStatus
    overall_progress_percent: float = Field(0.0, ge=0.0, le=100.0)
    current_phase: str
    agent_progress: List[AgentProgress] = Field(default_factory=list)
    total_artifacts: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    estimated_completion: Optional[datetime] = None
    started_at: datetime
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Artifact(BaseModel):
    """Artifact produced during development."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str  # code, test, config, doc, etc.
    path: str
    content: Optional[str] = None
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DevelopmentResponse(BaseModel):
    """Response from development request."""

    job_id: UUID
    status: JobStatus
    message: str
    progress_url: Optional[str] = None
    websocket_url: Optional[str] = None


class JobResult(BaseModel):
    """Final result of a development job."""

    job_id: UUID
    status: JobStatus
    artifacts: List[Artifact] = Field(default_factory=list)
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    quality_score: float = Field(0.0, ge=0.0, le=1.0)
    security_score: float = Field(0.0, ge=0.0, le=1.0)
    performance_score: float = Field(0.0, ge=0.0, le=1.0)
    total_tokens_used: int = 0
    total_cost: float = 0.0
    execution_time_seconds: float = 0.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    deployment_instructions: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class WebSocketMessage(BaseModel):
    """WebSocket message for real-time updates."""

    type: str  # progress, artifact, error, completion
    job_id: UUID
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]
    agents: Dict[str, str]
    queue_size: int
    active_jobs: int


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    agent_type: AgentType
    model: str = "gpt-4"
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(4000, gt=0)
    timeout_seconds: int = Field(300, gt=0)
    retry_attempts: int = Field(3, ge=0)
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FactoryConfig(BaseModel):
    """Configuration for the Auto-Forge factory."""

    max_concurrent_jobs: int = Field(10, gt=0)
    max_agents_per_job: int = Field(8, gt=0)
    default_timeout_seconds: int = Field(3600, gt=0)
    agent_configs: Dict[AgentType, AgentConfig] = Field(default_factory=dict)
    supported_languages: List[Language] = Field(default_factory=list)
    supported_frameworks: List[Framework] = Field(default_factory=list)
    supported_cloud_providers: List[CloudProvider] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
