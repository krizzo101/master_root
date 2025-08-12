"""
OAMAT Agent Models

Contains all Pydantic models, enums, and data structures for the OAMAT system.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionCategory(str, Enum):
    """Categories for clarification questions to guide specification refinement."""

    GENERAL = "general"
    SCOPE = "scope"
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    CONSTRAINTS = "constraints"
    INFRASTRUCTURE = "infrastructure"


# Enums for Workflow Classification
class TaskComplexity(str, Enum):
    """Task complexity classification for intelligent resource allocation"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class WorkflowStrategy(str, Enum):
    """Workflow execution strategies for optimal orchestration"""

    LINEAR = "linear"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    ITERATIVE = "iterative"
    HYBRID = "hybrid"
    SDLC = "sdlc"


# Supporting Models for Enhanced Planning
class NodeResourceRequirements(BaseModel):
    """Resource requirements for individual workflow nodes"""

    model_config = ConfigDict(extra="forbid")
    estimated_duration_minutes: int | None = None
    cpu_intensity: str = Field(default="medium", description="low, medium, high")
    memory_requirements: str = Field(
        default="standard", description="minimal, standard, high"
    )
    network_usage: str = Field(
        default="moderate", description="minimal, moderate, intensive"
    )
    storage_needs: str = Field(
        default="temporary", description="none, temporary, persistent"
    )
    dependencies: list[str] = Field(default_factory=list)


class NodeMetadata(BaseModel):
    """Metadata for enhanced workflow node tracking"""

    model_config = ConfigDict(extra="forbid")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    estimated_duration: int | None = None
    priority: str = Field(default="normal", description="low, normal, high, critical")
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int | None = None
    tags: list[str] = Field(default_factory=list)


class PlanResourceRequirements(BaseModel):
    """Overall resource requirements for workflow plans"""

    model_config = ConfigDict(extra="forbid")
    total_estimated_duration: int | None = None
    peak_agents_required: int = Field(default=1)
    required_tools: list[str] = Field(default_factory=list)
    external_dependencies: list[str] = Field(default_factory=list)
    computational_complexity: str = Field(default="medium")


class PlanMetadata(BaseModel):
    """Metadata for comprehensive workflow plan tracking"""

    model_config = ConfigDict(extra="forbid")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = Field(default="1.0")
    created_by: str = Field(default="enhanced_manager")
    plan_type: str = Field(default="standard")
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    risk_level: str = Field(default="medium", description="low, medium, high, critical")


# Core Analysis Models
class EnhancedRequestAnalysis(BaseModel):
    """Comprehensive analysis of user requests with sophisticated intelligence"""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}")

    # Intent and Context Analysis
    primary_intent: str = Field(
        default="", description="Main intent of the user request"
    )
    secondary_intents: list[str] = Field(default_factory=list)
    domain_category: str = Field(
        default="general", description="Technical domain category"
    )
    context_understanding: dict[str, Any] = Field(default_factory=dict)

    # Complexity and Requirements Analysis
    complexity: TaskComplexity = Field(default=TaskComplexity.MODERATE)
    estimated_effort_hours: float | None = None
    required_expertise: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    estimated_phases: int | None = None

    # Agent and Tool Recommendations
    recommended_agents: list[str] = Field(default_factory=list)
    suggested_workflow_pattern: str = Field(
        default="research_and_analyze", description="Suggested workflow pattern"
    )
    alternative_approaches: list[str] = Field(default_factory=list)

    # Quality and Success Criteria
    success_criteria: list[str] = Field(default_factory=list)
    quality_requirements: list[str] = Field(default_factory=list)
    deliverable_expectations: list[str] = Field(default_factory=list)

    # Risk and Constraint Analysis
    identified_risks: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    uncertainty_factors: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)

    # Strategic Recommendations
    workflow_strategy: WorkflowStrategy = Field(default=WorkflowStrategy.ADAPTIVE)
    optimization_opportunities: list[str] = Field(default_factory=list)
    escalation_conditions: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)

    # Confidence and Validation
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    success_probability: float | None = None
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    validation_notes: list[str] = Field(default_factory=list)


# Enhanced Workflow Node Model
class EnhancedWorkflowNode(BaseModel):
    """Sophisticated workflow node with comprehensive orchestration capabilities"""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")

    # Core Node Configuration
    agent_role: str = Field(
        default="", description="Role of the agent handling this node"
    )
    task_type: str = Field(default="", description="Type of task to be performed")
    description: str = Field(default="", description="Description of the task")

    # CRITICAL TASK MARKING - NEW FEATURE
    critical: bool = Field(
        default=False, description="If True, workflow stops if this task fails"
    )
    critical_reason: str | None = Field(
        default=None, description="Why this task is critical"
    )

    # Input and Output Management
    parameters: str = Field(default="{}", description="JSON string of parameters")
    expected_outputs: list[str] = Field(default_factory=list)

    # Orchestration and Flow Control
    next_nodes: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(
        default_factory=list,
        description="Node IDs that must complete before this node can execute",
    )
    parallel_eligible: bool = Field(default=True)

    # Quality and Success Management
    success_criteria: list[str] = Field(default_factory=list)
    quality_gates: list[str] = Field(default_factory=list)

    # Integration and Tool Management
    tools_required: list[str] = Field(default_factory=list)

    # INTELLIGENT SUBDIVISION - Manager-Driven (NEW)
    requires_subdivision: bool = Field(
        default=False,
        description="If True, this node should be automatically subdivided by WorkflowManager",
    )
    subdivision_reasoning: str | None = Field(
        default=None, description="Why this node was marked for subdivision"
    )
    estimated_sub_nodes: int = Field(
        default=0, description="Estimated number of sub-nodes this will create"
    )
    suggested_sub_roles: list[str] = Field(
        default_factory=list, description="Suggested agent roles for subdivision"
    )
    complexity_score: float = Field(
        default=0.5,
        description="Complexity score from 0.0 (simple) to 1.0 (very complex)",
    )
    parallelization_potential: float = Field(
        default=0.5, description="How much this task can be parallelized (0.0-1.0)"
    )


# Comprehensive Workflow Plan Model
class EnhancedWorkflowPlan(BaseModel):
    """Comprehensive workflow plan with sophisticated orchestration"""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")

    # Plan Identification and Description
    title: str = Field(default="", description="Title of the workflow plan")
    description: str = Field(default="", description="Description of the workflow plan")

    # Strategic Configuration
    strategy: WorkflowStrategy = Field(default=WorkflowStrategy.ADAPTIVE)
    complexity: TaskComplexity = Field(default=TaskComplexity.MODERATE)

    # Node and Flow Management
    nodes: list[EnhancedWorkflowNode] = Field(default_factory=list)

    # Output and Deliverable Management
    expected_outputs: list[str] = Field(default_factory=list)

    # Quality and Success Management
    success_criteria: list[str] = Field(default_factory=list)
    quality_requirements: list[str] = Field(default_factory=list)

    # Risk and Resilience Management
    escalation_triggers: list[str] = Field(default_factory=list)

    # Resource and Performance Management
    estimated_duration_minutes: int | None = None


# Request Processing Models
class ProcessingRequest(BaseModel):
    """Input model for request processing"""

    model_config = ConfigDict(extra="forbid")
    user_request: str = Field(default="", description="The user's request")
    context: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)


class ProcessingResponse(BaseModel):
    """Output model for request processing"""

    model_config = ConfigDict(extra="forbid")
    success: bool = Field(
        default=False, description="Whether the request was processed successfully"
    )
    analysis: EnhancedRequestAnalysis | None = None
    workflow: EnhancedWorkflowPlan | None = None
    error: str | None = None
    fallback_analysis: EnhancedRequestAnalysis | None = None
    fallback_workflow: EnhancedWorkflowPlan | None = None
    agent: str = "workflow_manager"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class ClarificationQuestion(BaseModel):
    """Individual clarification question for user input"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default="", description="Unique identifier for the question")
    question: str = Field(default="", description="The question to ask the user")
    question_type: Literal["text", "choice", "yes_no", "optional"] = Field(
        default="text", description="Type of question"
    )
    options: list[str] | None = Field(
        default=None, description="Available options for choice questions"
    )
    default_value: str | None = Field(
        default=None, description="Default/recommended value"
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium", description="Question priority"
    )
    category: QuestionCategory = Field(
        default=QuestionCategory.GENERAL,
        description="Question category to guide specification refinement.",
    )
    explanation: str | None = Field(
        default=None, description="Why this question is important"
    )
    skip_if_obvious: bool = Field(
        default=False, description="Skip if answer can be inferred from context"
    )


class ExpandedPrompt(BaseModel):
    """Expanded and clarified version of the original user request"""

    model_config = ConfigDict(extra="forbid")

    # Original request tracking
    original_request: str | None = Field(
        default="", description="The original user request"
    )

    # Expanded specification
    objective: str | None = Field(
        default="", description="Clear, comprehensive objective statement"
    )
    scope_and_deliverables: list[str] | None = Field(
        default_factory=list, description="Detailed scope and expected deliverables"
    )
    technical_architecture: dict[str, str] | None = Field(
        default_factory=dict, description="Inferred technical components and approaches"
    )
    execution_approach: list[str] | None = Field(
        default_factory=list, description="High-level execution steps"
    )
    success_criteria: list[str] | None = Field(
        default_factory=list, description="Measurable success criteria"
    )

    # Inferred assumptions
    inferred_assumptions: list[str] | None = Field(
        default_factory=list, description="Assumptions made during expansion"
    )
    domain_category: str | None = Field(
        default="general",
        description="Project domain (e.g., 'web_development', 'data_analysis')",
    )

    # Clarification needs
    clarification_questions: list[ClarificationQuestion] | None = Field(
        default_factory=list, description="Questions to ask user"
    )
    high_priority_questions: list[str] | None = Field(
        default_factory=list,
        description="Most critical questions that must be answered",
    )

    # Risk and complexity assessment
    complexity_factors: list[str] | None = Field(
        default_factory=list, description="Factors that add complexity"
    )
    potential_risks: list[str] | None = Field(
        default_factory=list, description="Identified risks and challenges"
    )

    # Recommendations
    recommended_approaches: dict[str, str] | None = Field(
        default_factory=dict,
        description="Recommended technical approaches with rationale",
    )


class QuestionAnswer(BaseModel):
    """A single question and its corresponding answer"""

    model_config = ConfigDict(extra="forbid")
    question_id: str = Field(description="The ID of the question being answered")
    answer: str = Field(description="The user's answer to the question")


class UserClarificationResponse(BaseModel):
    """User responses to clarification questions"""

    model_config = ConfigDict(extra="forbid")

    responses: list[QuestionAnswer] = Field(
        description="A list of question IDs and their corresponding answers"
    )
    additional_context: str | None = Field(
        default=None, description="Additional context provided by user"
    )
    skip_remaining: bool = Field(
        default=False, description="User wants to skip remaining questions"
    )


class RefinedSpecification(BaseModel):
    """Final refined specification after user clarification"""

    model_config = ConfigDict(extra="forbid")

    # Core specification
    refined_objective: str | None = Field(
        default="", description="Refined objective incorporating user feedback"
    )
    detailed_requirements: list[str] | None = Field(
        default_factory=list, description="Detailed functional requirements"
    )
    technical_specifications: dict[str, str] | None = Field(
        default_factory=dict, description="Specific technical choices"
    )

    # Implementation details
    implementation_phases: list[str] | None = Field(
        default_factory=list, description="Detailed implementation phases"
    )
    critical_path_items: list[str] | None = Field(
        default_factory=list, description="Items that must succeed for project success"
    )

    # Quality and success
    acceptance_criteria: list[str] | None = Field(
        default_factory=list, description="Specific acceptance criteria"
    )
    testing_strategy: list[str] | None = Field(
        default_factory=list, description="Testing approach and coverage"
    )

    # Constraints and considerations
    constraints: list[str] | None = Field(
        default_factory=list, description="Project constraints and limitations"
    )
    assumptions: list[str] | None = Field(
        default_factory=list, description="Final assumptions being made"
    )

    # Metadata
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in the spec's completeness (0.0-1.0)",
    )
    estimated_complexity: TaskComplexity | None = Field(
        default=TaskComplexity.MODERATE, description="Estimated project complexity"
    )
    recommended_timeline: str | None = Field(
        default=None, description="Recommended timeline"
    )


class RefinedSpecUpdate(BaseModel):
    """Schema for returning an updated RefinedSpecification from an LLM call."""

    model_config = ConfigDict(extra="forbid")
    updated_spec: RefinedSpecification = Field(
        description="The new, updated specification based on the latest user answer."
    )
    reasoning: str = Field(
        description="Explanation of what was changed in the spec and why."
    )


class DynamicQuestionUpdate(BaseModel):
    """Schema for dynamically updating the list of clarification questions."""

    model_config = ConfigDict(extra="forbid")
    updated_questions: list[ClarificationQuestion] = Field(
        description="The new, updated list of questions to ask."
    )
    reasoning: str = Field(description="Explanation of why the questions were updated.")
