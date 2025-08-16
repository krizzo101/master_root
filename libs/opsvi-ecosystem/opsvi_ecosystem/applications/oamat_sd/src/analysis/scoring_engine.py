"""
Scoring Engine Module

Handles overall scoring algorithms, category determination, and strategy selection.
Extracted from complexity_model.py for better modularity.
"""

import logging
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityCategory,
    ComplexityFactors,
    ExecutionStrategy,
)


class ScoringEngine:
    """Handles overall scoring and strategy determination"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def calculate_overall_score(self, factors: ComplexityFactors) -> float:
        """Calculate weighted overall complexity score (0-100 scale)."""
        # Initialize sums using config defaults - NO HARDCODED VALUES
        weighted_sum = ConfigManager().synthesis.quality.default_weighted_sum
        weight_sum = ConfigManager().synthesis.quality.default_weight_sum

        for factor in factors.get_all_factors():
            weighted_sum += factor.score * factor.weight
            weight_sum += factor.weight

        # Convert from 1-10 scale to 0-100 scale
        if weight_sum > 0:
            avg_score = weighted_sum / weight_sum
            # Use configurable score mapping instead of hardcoded formula
            score_mapping = ConfigManager().complexity.score_mapping
            return (avg_score - score_mapping.min_score) * (score_mapping.scale_factor)
        else:
            return 0.0

    def determine_category(self, overall_score: float) -> ComplexityCategory:
        """Determine complexity category from overall score (0-100 scale)."""

        thresholds = ConfigManager().complexity.scoring_thresholds

        if overall_score <= thresholds["simple"]:
            return ComplexityCategory.LOW
        elif overall_score <= thresholds["moderate"]:
            return ComplexityCategory.MEDIUM
        elif overall_score <= thresholds["complex"]:
            return ComplexityCategory.HIGH
        else:
            return ComplexityCategory.EXTREME

    def determine_execution_strategy(
        self, factors: ComplexityFactors, overall_score: float
    ) -> ExecutionStrategy:
        """Determine optimal execution strategy based on complexity."""

        # Simple strategy conditions - NO HARDCODED THRESHOLDS
        if (
            overall_score
            <= ConfigManager().analysis.complexity.score_thresholds["simple_strategy"]
            and factors.scope.score
            <= ConfigManager().analysis.complexity.score_thresholds["scope_limit"]
            and factors.dependencies.score
            <= ConfigManager().analysis.complexity.score_thresholds[
                "dependencies_limit"
            ]
        ):
            return ExecutionStrategy.SIMPLE

        # Orchestrated strategy conditions
        if (
            overall_score
            >= ConfigManager().analysis.complexity.score_thresholds[
                "orchestrated_strategy"
            ]
            or factors.scope.score
            >= ConfigManager().analysis.complexity.score_thresholds[
                "scope_orchestrated"
            ]
            or factors.dependencies.score >= 7
            or factors.technical_depth.score >= 8
        ):
            return ExecutionStrategy.ORCHESTRATED

        # Default to multi-agent
        return ExecutionStrategy.MULTI_AGENT

    def generate_agent_requirements(
        self, factors: ComplexityFactors, strategy: ExecutionStrategy
    ) -> dict[str, Any]:
        """Generate agent requirements based on complexity analysis."""
        requirements = {
            "agent_count": ConfigManager().agent_factory.counts.single_agent,
            "specializations": [],
            "coordination_level": "none",
            "tools_required": [],
            "monitoring_level": "basic",
        }

        if strategy == ExecutionStrategy.SIMPLE:
            requirements.update(
                {
                    "agent_count": ConfigManager().agent_factory.counts.single_agent,
                    "specializations": ["generalist"],
                    "coordination_level": "none",
                }
            )

        elif strategy == ExecutionStrategy.MULTI_AGENT:
            specializations = []

            if factors.technical_depth.score >= 6:
                specializations.append("technical_specialist")
            if factors.domain_knowledge.score >= 6:
                specializations.append("domain_expert")
            if factors.scope.score >= 6:
                specializations.append("architect")

            requirements.update(
                {
                    "agent_count": len(specializations) or 2,
                    "specializations": specializations or ["researcher", "implementer"],
                    "coordination_level": "moderate",
                }
            )

        elif strategy == ExecutionStrategy.ORCHESTRATED:
            requirements.update(
                {
                    "agent_count": 4,
                    "specializations": [
                        "architect",
                        "researcher",
                        "implementer",
                        "validator",
                    ],
                    "coordination_level": "high",
                    "monitoring_level": "detailed",
                }
            )

        # Add tools based on complexity
        if factors.dependencies.score >= 5:
            requirements["tools_required"].append("integration_tools")
        if factors.risk.score >= 6:
            requirements["tools_required"].append("security_tools")
        if factors.technical_depth.score >= 7:
            requirements["tools_required"].append("advanced_analysis_tools")

        return requirements

    def estimate_effort(
        self, factors: ComplexityFactors, strategy: ExecutionStrategy
    ) -> str:
        """Estimate effort level based on complexity."""
        avg_score = sum(f.score for f in factors.get_all_factors()) / 6

        if avg_score <= 3:
            return "Low (Hours)"
        elif avg_score <= 5:
            return "Medium (Days)"
        elif avg_score <= 7:
            return "High (Weeks)"
        else:
            return "Very High (Months)"

    def calculate_confidence(self, factors: ComplexityFactors) -> float:
        """Calculate confidence in the complexity analysis."""

        # Base confidence

        confidence = ConfigManager().reasoning.default_confidence_score

        # Adjust based on factor consistency
        scores = [f.score for f in factors.get_all_factors()]
        variance = sum(
            (score - sum(scores) / len(scores)) ** 2 for score in scores
        ) / len(scores)

        # Lower confidence for high variance (inconsistent factors) - NO HARDCODED VALUES

        if (
            variance
            > ConfigManager().analysis.complexity.variance_analysis[
                "variance_threshold_high"
            ]
        ):
            confidence -= ConfigManager().analysis.confidence["variance_high"]
        elif (
            variance
            > ConfigManager().analysis.complexity.variance_analysis[
                "variance_threshold_medium"
            ]
        ):
            confidence -= ConfigManager().analysis.confidence["variance_medium"]

        # Adjust based on extreme scores
        extreme_scores = sum(1 for score in scores if score <= 2 or score >= 9)
        if (
            extreme_scores
            > ConfigManager().analysis.complexity.variance_analysis[
                "extreme_score_count_threshold"
            ]
        ):
            confidence -= ConfigManager().analysis.confidence["extreme_score"]

        # Ensure bounds
        return max(0.1, min(ConfigManager().analysis.confidence.max_confidence))
