"""
O3 Analysis Data Models

Pydantic models and enums for O3 reasoning, analysis, and strategy generation.
Extracted from o3_master_agent.py for better modularity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

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
    evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)


@dataclass
class AgentStrategy:
    """Strategy for agent deployment and coordination."""

    execution_strategy: ExecutionStrategy
    agent_roles: List[str]
    coordination_pattern: str
    communication_flow: Dict[str, List[str]]
    success_criteria: List[str]
    risk_mitigation: List[str] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    """Detailed execution plan for the request with explicit dependency tracking."""

    phases: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    resource_requirements: Dict[str, Any]
    timeline_estimates: Dict[str, str]
    quality_gates: List[str]
    contingency_plans: List[str] = field(default_factory=list)
    # New dependency tracking fields for parallel vs sequential execution
    parallel_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    sequential_requirements: List[Dict[str, Any]] = field(default_factory=list)
    integration_points: List[str] = field(default_factory=list)
    consistency_checks: List[str] = field(default_factory=list)


@dataclass
class PipelineDesign:
    """Dynamic pipeline design determined by O3 for each specific request."""

    pipeline_type: str
    stages: List[Dict[str, Any]]
    execution_graph: Dict[str, Any]
    context_management: Dict[str, Any]
    optimization_rationale: str = ""
    estimated_efficiency: str = ""
    alternative_approaches: List[str] = field(default_factory=list)


@dataclass
class O3AnalysisResult:
    """Complete O3-level analysis result."""

    request_analysis: Dict[str, Any]
    complexity_assessment: ComplexityAnalysisResult
    agent_strategy: AgentStrategy
    execution_plan: ExecutionPlan
    reasoning_chain: List[ReasoningStep]
    confidence: float
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
