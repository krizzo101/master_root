"""
Smart Decomposition Data Models Implementation

Implements all Pydantic models from DATA_MODELS_SPECIFICATION.md
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RequestType(str, Enum):
    """Supported request types for schema validation"""

    WEB_APPLICATION = "web_application"
    MICROSERVICE = "microservice"
    SCRIPT = "script"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


class Priority(str, Enum):
    """Gap analysis priority levels"""

    CRITICAL = "critical"  # Blocks execution
    HIGH = "high"  # Significantly impacts quality
    MEDIUM = "medium"  # Moderate impact
    LOW = "low"  # Optional enhancement


class GapType(str, Enum):
    """Type/category of information gap for agentic gap analysis."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    INFERABLE = "inferable"
    RESEARCHABLE = "researchable"
    USER_INPUT = "user_input"


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestInput(BaseModel):
    """Initial user request input"""

    content: str = Field(
        ..., min_length=10, max_length=10000, description="Raw user request content"
    )
    request_type: RequestType | None = Field(
        None, description="Detected or specified request type"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context information"
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences and constraints"
    )
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request correlation ID",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Request submission timestamp"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or v.isspace():
            raise ValueError("Content cannot be empty or whitespace only")
        return v.strip()


class ValidationResult(BaseModel):
    """Request validation outcome"""

    is_valid: bool = Field(..., description="Overall validation status")
    detected_type: RequestType | None = Field(
        None, description="Auto-detected request type"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence (0-1)"
    )
    extracted_info: dict[str, Any] = Field(
        default_factory=dict, description="Extracted structured information"
    )
    validation_errors: list[str] = Field(
        default_factory=list, description="Validation error messages"
    )
    schema_matches: list[str] = Field(
        default_factory=list, description="Matching schema identifiers"
    )


class InformationGap(BaseModel):
    """Individual information gap"""

    field_name: str = Field(..., description="Missing field identifier")
    description: str = Field(..., description="Human-readable gap description")
    priority: Priority = Field(..., description="Gap priority level")
    required_for_execution: bool = Field(..., description="Blocks execution if missing")
    suggested_default: Any | None = Field(None, description="Suggested default value")
    research_strategy: str | None = Field(None, description="How to research this gap")


class GapAnalysisResult(BaseModel):
    """Complete gap analysis outcome"""

    total_gaps: int = Field(..., ge=0, description="Total number of gaps identified")
    critical_gaps: list[InformationGap] = Field(
        default_factory=list, description="Critical gaps requiring user input"
    )
    auto_fillable_gaps: list[InformationGap] = Field(
        default_factory=list, description="Gaps that can be auto-completed"
    )
    completion_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Request completeness percentage"
    )
    blocking_execution: bool = Field(..., description="Whether gaps block execution")
    estimated_completion_time: int = Field(
        ..., ge=0, description="Estimated time to complete gaps (seconds)"
    )


class CompletionAction(BaseModel):
    """Individual completion action"""

    gap_field: str = Field(..., description="Field being completed")
    action_type: str = Field(..., description="Type of completion action")
    data_source: str = Field(..., description="Source of completion data")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Completion confidence")
    assumptions_made: list[str] = Field(
        default_factory=list, description="Assumptions made during completion"
    )


class InformationCompletionResult(BaseModel):
    """Result of information completion process"""

    completion_actions: list[CompletionAction] = Field(
        default_factory=list, description="Actions taken to complete information"
    )
    filled_data: dict[str, Any] = Field(
        default_factory=dict, description="Data that was filled in"
    )
    remaining_gaps: list[InformationGap] = Field(
        default_factory=list, description="Gaps that could not be filled"
    )
    completion_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall completion confidence"
    )
    escalation_required: bool = Field(..., description="Whether user input is needed")


class ComplexityFactor(BaseModel):
    """Individual complexity factor analysis"""

    name: str = Field(..., description="Factor name")
    score: int = Field(..., ge=1, le=10, description="Complexity score (1-10)")
    reasoning: str = Field(..., description="Explanation for the score")
    indicators: list[str] = Field(
        default_factory=list,
        description="Specific indicators that influenced the score",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this factor assessment"
    )


class ComplexityAnalysis(BaseModel):
    """Complete complexity analysis result"""

    factors: dict[str, ComplexityFactor] = Field(
        ..., description="Six complexity factors"
    )
    overall_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall complexity score"
    )
    execution_strategy: str = Field(..., description="Recommended execution strategy")
    agent_requirements: dict[str, Any] = Field(
        default_factory=dict, description="Required agent capabilities"
    )
    estimated_effort: str = Field(..., description="Effort estimation")
    reasoning_chain: list[str] = Field(
        default_factory=list, description="Step-by-step reasoning"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall analysis confidence"
    )

    @field_validator("factors")
    @classmethod
    def validate_six_factors(cls, v):
        required_factors = {
            "scope",
            "technical_depth",
            "domain_knowledge",
            "dependencies",
            "timeline",
            "risk",
        }
        if set(v.keys()) != required_factors:
            raise ValueError(f"Must include exactly these factors: {required_factors}")
        return v


class AgentCommand(BaseModel):
    """Command for agent execution"""

    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: str = Field(..., description="Target agent role")
    action: str = Field(..., description="Action to perform")
    parameters: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)
    timeout: int = Field(default=300, description="Timeout in seconds")


class AgentResult(BaseModel):
    """Result from agent execution"""

    command_id: str = Field(..., description="Source command ID")
    agent_role: str = Field(..., description="Agent that produced result")
    success: bool = Field(..., description="Whether execution succeeded")
    result_data: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = Field(None)
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    """State management for agent orchestration"""

    state_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    current_phase: str = Field(..., description="Current execution phase")
    active_agents: list[str] = Field(default_factory=list)
    completed_commands: list[str] = Field(default_factory=list)
    pending_commands: list[AgentCommand] = Field(default_factory=list)
    state_data: dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SystemError(BaseModel):
    """System error information"""

    error_code: str = Field(..., description="Structured error code")
    error_message: str = Field(..., description="Human-readable error message")
    component: str = Field(..., description="Component that generated the error")
    severity: str = Field(..., description="Error severity level")
    context: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recovery_suggested: bool = Field(default=False)


class ExecutionResult(BaseModel):
    """Final execution result"""

    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = Field(..., description="Final execution status")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = Field(None)
    final_output: dict[str, Any] = Field(default_factory=dict)
    agent_contributions: dict[str, AgentResult] = Field(default_factory=dict)
    errors: list[SystemError] = Field(default_factory=list)
    performance_metrics: dict[str, float] = Field(default_factory=dict)
    success: bool = Field(..., description="Overall success indicator")

    @field_validator("end_time")
    @classmethod
    def end_time_after_start(cls, v):
        # Note: For cross-field validation in Pydantic v2, use model_validator instead
        # For now, we'll just validate the field exists
        return v


class GapAnalysisInput(BaseModel):
    """Input model for gap analysis requests."""

    request_id: str = Field(
        ..., description="Unique identifier for the gap analysis request"
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict, description="Input data for gap analysis"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time of request creation"
    )


class InformationCompletionInput(BaseModel):
    """Input model for information completion requests."""

    request_id: str = Field(
        ..., description="Unique identifier for the information completion request"
    )
    input_data: dict[str, Any] = Field(
        default_factory=dict, description="Input data for information completion"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Time of request creation"
    )
