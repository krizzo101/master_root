"""
Complexity Analysis Data Models

Enums and dataclasses for complexity analysis system.
Extracted from complexity_model.py for better modularity.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _get_complexity_config():
    """Helper to get complexity configuration for dataclass defaults"""
    try:
        from src.applications.oamat_sd.src.config.config_manager import ConfigManager

        return ConfigManager().analysis.complexity
    except ImportError:
        # Fallback for testing
        from types import SimpleNamespace

        return SimpleNamespace(defaults={"factor_weight": 1.0})


class ExecutionStrategy(str, Enum):
    """Execution strategies based on complexity analysis."""

    SIMPLE = "simple"  # Single agent, direct execution
    MULTI_AGENT = "multi_agent"  # Multiple specialized agents
    ORCHESTRATED = "orchestrated"  # Complex orchestration with DAG


class ComplexityCategory(str, Enum):
    """Overall complexity categories."""

    LOW = "low"  # Score 1-3
    MEDIUM = "medium"  # Score 4-6
    HIGH = "high"  # Score 7-8
    EXTREME = "extreme"  # Score 9-10


@dataclass
class ComplexityFactor:
    """Individual complexity factor analysis."""

    name: str
    score: int  # 1-10 scale
    reasoning: str
    weight: float = field(
        default_factory=lambda: _get_complexity_config().defaults["factor_weight"]
    )
    indicators: list[str] = field(default_factory=list)


@dataclass
class ComplexityFactors:
    """Six core complexity factors."""

    scope: ComplexityFactor
    technical_depth: ComplexityFactor
    domain_knowledge: ComplexityFactor
    dependencies: ComplexityFactor
    timeline: ComplexityFactor
    risk: ComplexityFactor

    def get_all_factors(self) -> list[ComplexityFactor]:
        """Get all factors as a list."""
        return [
            self.scope,
            self.technical_depth,
            self.domain_knowledge,
            self.dependencies,
            self.timeline,
            self.risk,
        ]

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary of scores."""
        return {
            "scope": self.scope.score,
            "technical_depth": self.technical_depth.score,
            "domain_knowledge": self.domain_knowledge.score,
            "dependencies": self.dependencies.score,
            "timeline": self.timeline.score,
            "risk": self.risk.score,
        }


@dataclass
class ComplexityAnalysisResult:
    """Complete complexity analysis result."""

    factors: ComplexityFactors
    overall_score: float
    category: ComplexityCategory
    execution_strategy: ExecutionStrategy
    reasoning: str
    agent_requirements: dict[str, Any]
    estimated_effort: str
    confidence: float
