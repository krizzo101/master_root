"""
O3 Analysis Data Models

Pydantic models and enums for O3 reasoning, analysis, and strategy generation.
Extracted from o3_master_agent.py for better modularity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityAnalysisResult,
    ExecutionStrategy,
)


class ReasoningLevel(str, Enum):
    """Levels of reasoning depth."""

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AnalysisType(str, Enum):
    """Types of analysis performed."""

    COMPLEXITY = "complexity"
    STRATEGY = "strategy"
    PLANNING = "planning"
    OPTIMIZATION = "optimization"


@dataclass
class ReasoningStep:
    """Individual step in reasoning process."""

    step_id: str
    analysis_type: AnalysisType
    reasoning: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)


@dataclass
class AgentStrategy:
    """Strategy for agent deployment and coordination."""

    execution_strategy: ExecutionStrategy
    agent_roles: list[str]
    coordination_pattern: str
    communication_flow: dict[str, list[str]]
    success_criteria: list[str]
    risk_mitigation: list[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Detailed execution plan for the request with explicit dependency tracking."""

    phases: list[dict[str, Any]]
    dependencies: dict[str, list[str]]
    resource_requirements: dict[str, Any]
    timeline_estimates: dict[str, str]
    quality_gates: list[str]
    contingency_plans: list[str] = field(default_factory=list)
    # New dependency tracking fields for parallel vs sequential execution
    parallel_opportunities: list[dict[str, Any]] = field(default_factory=list)
    sequential_requirements: list[dict[str, Any]] = field(default_factory=list)
    integration_points: list[str] = field(default_factory=list)
    consistency_checks: list[str] = field(default_factory=list)


@dataclass
class PipelineDesign:
    """Dynamic pipeline design determined by O3 for each specific request."""

    pipeline_type: str
    stages: list[dict[str, Any]]
    execution_graph: dict[str, Any]
    context_management: dict[str, Any]
    optimization_rationale: str = ""
    estimated_efficiency: str = ""
    alternative_approaches: list[str] = field(default_factory=list)


@dataclass
class O3AnalysisResult:
    """Complete O3-level analysis result."""

    request_analysis: dict[str, Any]
    complexity_assessment: ComplexityAnalysisResult
    agent_strategy: AgentStrategy
    execution_plan: ExecutionPlan
    reasoning_chain: list[ReasoningStep]
    confidence: float
    recommendations: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
