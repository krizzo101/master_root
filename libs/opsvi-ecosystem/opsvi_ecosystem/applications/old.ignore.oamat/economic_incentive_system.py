"""
OAMAT Economic Incentive System for Fractal Workflow Control

This system implements progressive reward reduction to naturally control recursive
subdivision while maintaining capability for genuinely complex problems.

Core Principle: Market forces balance subdivision desire vs complexity management.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IncentiveDomain(Enum):
    """Different domains may have different subdivision characteristics"""

    SOFTWARE_DEVELOPMENT = "software_dev"
    RESEARCH = "research"
    CONTENT_CREATION = "content"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"


@dataclass
class RewardParameters:
    """Configuration for economic incentive calculations"""

    base_decay_rate: float = 0.8  # Reward reduction per level (0.8^n)
    minimum_reward: float = 0.1  # Floor to prevent zero rewards
    escape_complexity_threshold: float = (
        9.0  # Override reward reduction if complexity extremely high
    )
    motivation_amplifier: float = 1.2  # How much reward affects effective complexity
    domain_modifiers: Dict[IncentiveDomain, float] = field(
        default_factory=lambda: {
            IncentiveDomain.RESEARCH: 0.9,  # Slightly more conservative for research
            IncentiveDomain.SOFTWARE_DEVELOPMENT: 1.0,  # Baseline
            IncentiveDomain.CONTENT_CREATION: 1.1,  # Slightly more aggressive
            IncentiveDomain.DATA_ANALYSIS: 0.85,  # More conservative
            IncentiveDomain.GENERAL: 1.0,
        }
    )


class SubdivisionDecision(BaseModel):
    """Result of subdivision decision analysis"""

    should_subdivide: bool
    base_complexity: float
    level_reward: float
    effective_complexity: float
    effective_threshold: float
    justification: str
    confidence: float = Field(ge=0.0, le=1.0)
    escape_hatch_triggered: bool = False


class EconomicIncentiveCalculator:
    """
    Calculates subdivision incentives using progressive reward reduction.

    Creates natural market forces:
    - High rewards at top levels encourage broad decomposition
    - Reduced rewards at deeper levels require stronger justification
    - Escape hatch allows genuine complexity to drive deep subdivision
    """

    def __init__(self, parameters: Optional[RewardParameters] = None):
        self.params = parameters or RewardParameters()
        self._subdivision_history: list[SubdivisionDecision] = []

    def calculate_subdivision_reward(
        self, hierarchy_level: int, domain: IncentiveDomain = IncentiveDomain.GENERAL
    ) -> float:
        """Calculate reward factor for subdivision at given level"""
        if hierarchy_level < 0:
            raise ValueError("Hierarchy level cannot be negative")

        # Base exponential decay
        base_reward = self.params.base_decay_rate**hierarchy_level

        # Apply domain modifier
        domain_modifier = self.params.domain_modifiers.get(domain, 1.0)
        adjusted_reward = base_reward * domain_modifier

        # Apply minimum floor
        final_reward = max(adjusted_reward, self.params.minimum_reward)

        logger.debug(
            f"Level {hierarchy_level} reward: {final_reward:.3f} "
            f"(base: {base_reward:.3f}, domain: {domain_modifier})"
        )

        return final_reward

    def calculate_effective_complexity(
        self, base_complexity: float, level_reward: float
    ) -> float:
        """
        Calculate reward-adjusted effective complexity.
        Higher rewards make borderline cases more likely to subdivide.
        """
        if not (0 <= base_complexity <= 10):
            raise ValueError("Base complexity must be between 0 and 10")

        # Reward amplifies perceived complexity (high reward = more eager to subdivide)
        motivation_boost = (
            level_reward - self.params.minimum_reward
        ) * self.params.motivation_amplifier
        effective_complexity = base_complexity + motivation_boost

        return min(effective_complexity, 10.0)  # Cap at maximum complexity

    def get_effective_threshold(
        self, base_threshold: float, hierarchy_level: int
    ) -> float:
        """
        Calculate level-adjusted subdivision threshold.
        Deeper levels require higher complexity to justify subdivision.
        """
        # Threshold increases slightly with depth to compensate for reduced reward
        level_adjustment = hierarchy_level * 0.3  # +0.3 per level
        return min(
            base_threshold + level_adjustment, 9.5
        )  # Cap to allow some subdivision

    def should_subdivide(
        self,
        base_complexity: float,
        hierarchy_level: int,
        base_threshold: float = 4.0,
        domain: IncentiveDomain = IncentiveDomain.GENERAL,
        context: Optional[Dict[str, Any]] = None,
    ) -> SubdivisionDecision:
        """
        Make subdivision decision using economic incentive model.

        Returns comprehensive decision with reasoning and metrics.
        """
        # Calculate reward factors
        level_reward = self.calculate_subdivision_reward(hierarchy_level, domain)
        effective_complexity = self.calculate_effective_complexity(
            base_complexity, level_reward
        )
        effective_threshold = self.get_effective_threshold(
            base_threshold, hierarchy_level
        )

        # Check escape hatch for extremely complex problems
        escape_hatch = base_complexity >= self.params.escape_complexity_threshold

        # Make subdivision decision
        should_subdivide = (effective_complexity > effective_threshold) or escape_hatch

        # Note: In production, this should integrate with ContextAlignmentValidator
        # to ensure subdivision preserves macro intent alignment

        # Generate justification
        if escape_hatch:
            justification = f"Escape hatch triggered - complexity {base_complexity:.1f} exceeds threshold {self.params.escape_complexity_threshold}"
        elif should_subdivide:
            justification = f"Effective complexity {effective_complexity:.1f} > threshold {effective_threshold:.1f} (reward: {level_reward:.2f})"
        else:
            justification = f"Effective complexity {effective_complexity:.1f} ≤ threshold {effective_threshold:.1f} (insufficient reward at level {hierarchy_level})"

        # Calculate confidence based on margin
        margin = abs(effective_complexity - effective_threshold)
        confidence = min(margin / 2.0, 1.0)  # Normalize to 0-1

        decision = SubdivisionDecision(
            should_subdivide=should_subdivide,
            base_complexity=base_complexity,
            level_reward=level_reward,
            effective_complexity=effective_complexity,
            effective_threshold=effective_threshold,
            justification=justification,
            confidence=confidence,
            escape_hatch_triggered=escape_hatch,
        )

        # Track decision for analytics
        self._subdivision_history.append(decision)

        logger.info(
            f"Subdivision decision at level {hierarchy_level}: "
            f"{'SUBDIVIDE' if should_subdivide else 'NO SUBDIVISION'} - {justification}"
        )

        return decision

    def get_subdivision_analytics(self) -> Dict[str, Any]:
        """Generate analytics on subdivision patterns and effectiveness"""
        if not self._subdivision_history:
            return {"message": "No subdivision decisions recorded"}

        total_decisions = len(self._subdivision_history)
        subdivisions = sum(1 for d in self._subdivision_history if d.should_subdivide)
        escape_hatch_uses = sum(
            1 for d in self._subdivision_history if d.escape_hatch_triggered
        )

        # Group by level for depth analysis
        level_stats = {}
        for decision in self._subdivision_history:
            level = len(
                [d for d in self._subdivision_history if d is decision]
            )  # Approximate level
            if level not in level_stats:
                level_stats[level] = {
                    "total": 0,
                    "subdivisions": 0,
                    "avg_complexity": 0,
                }

            level_stats[level]["total"] += 1
            if decision.should_subdivide:
                level_stats[level]["subdivisions"] += 1
            level_stats[level]["avg_complexity"] += decision.base_complexity

        # Calculate averages
        for level_data in level_stats.values():
            level_data["avg_complexity"] /= level_data["total"]
            level_data["subdivision_rate"] = (
                level_data["subdivisions"] / level_data["total"]
            )

        return {
            "total_decisions": total_decisions,
            "subdivision_rate": subdivisions / total_decisions,
            "escape_hatch_usage": escape_hatch_uses / total_decisions,
            "level_statistics": level_stats,
            "recent_decisions": [
                {
                    "complexity": d.base_complexity,
                    "effective_complexity": d.effective_complexity,
                    "reward": d.level_reward,
                    "subdivided": d.should_subdivide,
                    "confidence": d.confidence,
                }
                for d in self._subdivision_history[-10:]  # Last 10 decisions
            ],
        }


class WorkflowEconomicIntegration:
    """
    Integration layer between economic incentive system and OAMAT workflow management.

    Bridges the gap between economic calculations and practical workflow decisions.
    """

    def __init__(self, calculator: Optional[EconomicIncentiveCalculator] = None):
        self.calculator = calculator or EconomicIncentiveCalculator()

    def evaluate_node_subdivision(
        self,
        node_spec: Dict[str, Any],
        hierarchy_level: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate whether a workflow node should be subdivided.

        Returns: (should_subdivide, decision_metadata)
        """
        # Extract complexity from node specification
        base_complexity = node_spec.get("complexity_score", 5.0)

        # Determine domain from context
        domain_name = context.get("domain", "general") if context else "general"
        domain = (
            IncentiveDomain(domain_name)
            if domain_name in [d.value for d in IncentiveDomain]
            else IncentiveDomain.GENERAL
        )

        # Make economic decision
        decision = self.calculator.should_subdivide(
            base_complexity=base_complexity,
            hierarchy_level=hierarchy_level,
            domain=domain,
            context=context,
        )

        # Package decision metadata
        metadata = {
            "economic_decision": decision.dict(),
            "hierarchy_level": hierarchy_level,
            "domain": domain.value,
            "subdivision_analytics": self.calculator.get_subdivision_analytics(),
        }

        return decision.should_subdivide, metadata

    def recommend_subdivision_parameters(
        self, historical_performance: Dict[str, Any]
    ) -> RewardParameters:
        """
        Recommend economic parameters based on historical performance.

        Uses machine learning-like approach to optimize parameters.
        """
        # This would analyze historical data to recommend optimal parameters
        # For now, return defaults with basic adjustments

        current_params = self.calculator.params

        # Example adaptive logic (would be more sophisticated in practice)
        if historical_performance.get("over_subdivision_rate", 0) > 0.3:
            # Too much subdivision - increase decay rate
            current_params.base_decay_rate *= 0.9
        elif historical_performance.get("under_subdivision_rate", 0) > 0.3:
            # Too little subdivision - decrease decay rate
            current_params.base_decay_rate *= 1.1

        return current_params


# Example usage and testing scenarios
if __name__ == "__main__":
    # Initialize system
    calculator = EconomicIncentiveCalculator()
    integration = WorkflowEconomicIntegration(calculator)

    # Test scenarios
    scenarios = [
        {"name": "Simple Landing Page", "complexity": 3, "expected_depth": 1},
        {"name": "E-commerce Platform", "complexity": 8, "expected_depth": 3},
        {"name": "AI/ML Research Platform", "complexity": 9, "expected_depth": 5},
        {"name": "Blog Website", "complexity": 4, "expected_depth": 2},
    ]

    print("OAMAT Economic Incentive System Test Results")
    print("=" * 60)

    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']} (Complexity: {scenario['complexity']})")
        print("-" * 40)

        # Simulate subdivision decisions at multiple levels
        level = 0
        while level < 6:  # Max 6 levels
            decision = calculator.should_subdivide(
                base_complexity=scenario["complexity"],
                hierarchy_level=level,
                domain=IncentiveDomain.SOFTWARE_DEVELOPMENT,
            )

            print(
                f"Level {level}: {'SUBDIVIDE' if decision.should_subdivide else 'STOP'} "
                f"(Effective: {decision.effective_complexity:.1f}, "
                f"Reward: {decision.level_reward:.2f})"
            )

            if not decision.should_subdivide:
                break

            level += 1
            # Reduce complexity slightly for child nodes
            scenario["complexity"] = max(scenario["complexity"] - 0.5, 2.0)

    # Display analytics
    print("\nSystem Analytics:")
    print("-" * 40)
    analytics = calculator.get_subdivision_analytics()
    print(f"Total Decisions: {analytics.get('total_decisions', 0)}")
    print(f"Subdivision Rate: {analytics.get('subdivision_rate', 0):.2%}")
    print(f"Escape Hatch Usage: {analytics.get('escape_hatch_usage', 0):.2%}")
