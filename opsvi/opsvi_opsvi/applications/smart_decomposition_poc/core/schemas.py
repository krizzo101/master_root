"""
Smart Decomposition Meta-Intelligence System - Response Schemas
Pydantic models for structured OpenAI responses with validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ComplexityLevel(str, Enum):
    """Task complexity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementsResponse(BaseModel):
    """Structured response schema for requirements expansion agents"""

    expanded_requirements: str = Field(
        description="Comprehensive technical requirements analysis", min_length=50
    )
    technical_specifications: List[str] = Field(
        description="Detailed technical specifications list", min_items=1
    )
    dependencies: List[str] = Field(
        description="External dependencies and integrations required",
        default_factory=list,
    )
    complexity_assessment: ComplexityLevel = Field(
        description="Overall project complexity level"
    )
    estimated_effort: int = Field(
        description="Estimated effort in hours", ge=1, le=1000
    )
    validation_criteria: List[str] = Field(
        description="Success validation criteria", min_items=1
    )
    architecture_considerations: Optional[str] = Field(
        description="High-level architecture notes", default=None
    )
    risk_factors: List[str] = Field(
        description="Potential risks and mitigation strategies", default_factory=list
    )

    @validator("technical_specifications")
    def validate_specs(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one technical specification required")
        return v


class WorkDecompositionTask(BaseModel):
    """Individual task in work decomposition"""

    task_id: str = Field(description="Unique task identifier")
    title: str = Field(description="Task title", min_length=5)
    description: str = Field(description="Detailed task description", min_length=10)
    agent_role: str = Field(description="Required agent role for execution")
    dependencies: List[str] = Field(
        description="Task dependencies", default_factory=list
    )
    estimated_duration: int = Field(
        description="Estimated duration in minutes", ge=5, le=480
    )
    priority: Priority = Field(description="Task priority level")
    complexity: ComplexityLevel = Field(description="Task complexity")
    deliverables: List[str] = Field(description="Expected deliverables", min_items=1)


class CoordinationResponse(BaseModel):
    """Structured response schema for coordination and planning agents"""

    task_assignments: Dict[str, str] = Field(description="Agent role to task mapping")
    execution_order: List[str] = Field(
        description="Recommended task execution sequence", min_items=1
    )
    dependencies_mapped: Dict[str, List[str]] = Field(
        description="Task dependency relationships"
    )
    parallel_opportunities: List[List[str]] = Field(
        description="Groups of tasks that can execute in parallel", default_factory=list
    )
    risk_assessment: str = Field(
        description="Risk analysis and mitigation strategies", min_length=20
    )
    estimated_total_time: int = Field(
        description="Total estimated execution time in minutes", ge=10
    )
    critical_path: List[str] = Field(
        description="Critical path through task dependencies"
    )
    work_decomposition: List[WorkDecompositionTask] = Field(
        description="Detailed work breakdown structure", min_items=1
    )
    success: bool = Field(description="Coordination planning success status")


class CodeFile(BaseModel):
    """Individual code file specification"""

    filename: str = Field(description="File name with extension")
    content: str = Field(description="Complete file content", min_length=10)
    language: str = Field(description="Programming language")
    purpose: str = Field(description="File purpose and role")


class ImplementationResponse(BaseModel):
    """Structured response schema for implementation agents"""

    code_files: List[CodeFile] = Field(description="Generated code files", min_items=1)
    documentation: str = Field(
        description="Implementation documentation", min_length=50
    )
    tests: str = Field(description="Test code and test cases", min_length=20)
    deployment_config: str = Field(
        description="Deployment configuration files", min_length=10
    )
    implementation_notes: List[str] = Field(
        description="Important implementation details", default_factory=list
    )
    dependencies_installed: List[str] = Field(
        description="Required dependencies to install", default_factory=list
    )
    setup_instructions: str = Field(
        description="Setup and installation instructions", min_length=20
    )
    success: bool = Field(description="Implementation success status")

    @validator("code_files")
    def validate_code_files(cls, v):
        if not v:
            raise ValueError("At least one code file required")
        return v


class ValidationResponse(BaseModel):
    """Structured response schema for validation agents"""

    validation_results: Dict[str, bool] = Field(description="Validation test results")
    issues_found: List[str] = Field(
        description="Issues identified during validation", default_factory=list
    )
    recommendations: List[str] = Field(
        description="Improvement recommendations", default_factory=list
    )
    quality_score: float = Field(
        description="Overall quality score (0-1)", ge=0.0, le=1.0
    )
    performance_metrics: Dict[str, Any] = Field(
        description="Performance measurement results", default_factory=dict
    )
    compliance_status: bool = Field(description="Requirements compliance status")
    success: bool = Field(description="Validation success status")


class SystemResponse(BaseModel):
    """Generic system response wrapper"""

    success: bool = Field(description="Operation success status")
    result: Dict[str, Any] = Field(description="Operation result data")
    agent_id: str = Field(description="Executing agent identifier")
    role: str = Field(description="Agent role")
    model: str = Field(description="OpenAI model used")
    execution_time: float = Field(description="Execution time in seconds", ge=0)
    timestamp: datetime = Field(
        description="Response timestamp", default_factory=datetime.utcnow
    )
    metadata: Dict[str, Any] = Field(
        description="Additional metadata", default_factory=dict
    )


class ErrorResponse(BaseModel):
    """Structured error response"""

    success: bool = Field(default=False, description="Always false for errors")
    error_type: str = Field(description="Error type classification")
    error_message: str = Field(description="Human-readable error message")
    error_details: Dict[str, Any] = Field(
        description="Detailed error information", default_factory=dict
    )
    agent_id: Optional[str] = Field(description="Agent that encountered error")
    timestamp: datetime = Field(
        description="Error timestamp", default_factory=datetime.utcnow
    )
    recovery_suggestions: List[str] = Field(
        description="Suggested recovery actions", default_factory=list
    )


class PerformanceMetrics(BaseModel):
    """Performance tracking metrics"""

    execution_time: float = Field(description="Total execution time in seconds")
    parallel_efficiency: float = Field(
        description="Parallel execution efficiency ratio"
    )
    task_count: int = Field(description="Number of tasks executed")
    success_rate: float = Field(description="Success rate (0-1)", ge=0, le=1)
    memory_usage: float = Field(description="Peak memory usage in MB")
    model_usage: Dict[str, int] = Field(
        description="Token usage per model", default_factory=dict
    )


# Schema registry for agent roles
AGENT_RESPONSE_SCHEMAS = {
    "manager": CoordinationResponse,
    "requirements_expander": RequirementsResponse,
    "work_decomposer": CoordinationResponse,
    "architect": RequirementsResponse,
    "developer": ImplementationResponse,
    "tester": ValidationResponse,
    "coordinator": CoordinationResponse,
    "validator": ValidationResponse,
    "integrator": ImplementationResponse,
    "optimizer": ValidationResponse,
}


def get_schema_for_role(role: str) -> BaseModel:
    """Get appropriate Pydantic schema for agent role"""
    return AGENT_RESPONSE_SCHEMAS.get(role, SystemResponse)


def validate_response(role: str, response_data: Dict[str, Any]) -> BaseModel:
    """Validate response data against role-specific schema"""
    schema_class = get_schema_for_role(role)
    return schema_class(**response_data)
