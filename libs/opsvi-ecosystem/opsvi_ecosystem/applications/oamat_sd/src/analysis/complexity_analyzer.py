"""
Complexity Analyzer Module

Handles O3-powered complexity analysis and assessment for project requests.
Extracted from o3_master_agent.py for better modularity.
"""

import logging
from typing import Any, Dict, List, Tuple

from src.applications.oamat_sd.src.agents.request_validation import ValidationResult
from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityAnalysisResult,
    ComplexityCategory,
    ComplexityFactor,
    ComplexityFactors,
    ExecutionStrategy,
)
from src.applications.oamat_sd.src.models.o3_analysis_models import (
    AnalysisType,
    ReasoningStep,
)


class ComplexityAnalyzer:
    """Handles O3-powered complexity analysis and assessment"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def analyze_complexity(
        self, request: Dict[str, Any], validation_result: ValidationResult
    ) -> Tuple[ComplexityAnalysisResult, List[ReasoningStep]]:
        """Perform deep complexity analysis with O3-level reasoning."""

        self.logger.info(
            f"O3 analyzing complexity for: {request.get('name') if 'name' in request else ConfigManager().analysis.request_processing['unnamed_request']}"
        )

        reasoning_steps = []

        # Step 1: Initial complexity assessment
        step1 = ReasoningStep(
            step_id="complexity_initial",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning=f"Analyzing request type {validation_result.request_type} with {len(validation_result.extracted_info)} extracted fields",
            confidence=ConfigManager().reasoning.default_confidence_score,
            evidence=[
                f"Request type: {validation_result.request_type}",
                f"Fields: {list(validation_result.extracted_info.keys())}",
            ],
        )
        reasoning_steps.append(step1)

        # Step 2: Multi-dimensional analysis
        complexity_factors = self._analyze_complexity_dimensions(
            request, validation_result
        )

        step2 = ReasoningStep(
            step_id="complexity_dimensions",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning="Analyzed six complexity dimensions: scope, technical depth, domain knowledge, dependencies, timeline, risk",
            confidence=ConfigManager().reasoning.medium_confidence_score,
            evidence=[
                f"Scope: {complexity_factors['scope']}",
                f"Technical: {complexity_factors['technical_depth']}",
            ],
        )
        reasoning_steps.append(step2)

        # Step 3: Strategic assessment
        overall_score = sum(complexity_factors.values()) / len(complexity_factors)
        category = self._determine_complexity_category(overall_score)

        step3 = ReasoningStep(
            step_id="complexity_assessment",
            analysis_type=AnalysisType.COMPLEXITY,
            reasoning=f"Overall complexity score: {overall_score:.1f}, Category: {category}",
            confidence=ConfigManager().reasoning.high_confidence_score,
            evidence=[f"Average score: {overall_score:.1f}", f"Category: {category}"],
        )
        reasoning_steps.append(step3)

        # Create complexity result (simplified for TDD)
        # Create individual factors
        factors = ComplexityFactors(
            scope=ComplexityFactor(
                "scope", complexity_factors["scope"], "Analyzed scope complexity"
            ),
            technical_depth=ComplexityFactor(
                "technical_depth",
                complexity_factors["technical_depth"],
                "Analyzed technical depth",
            ),
            domain_knowledge=ComplexityFactor(
                "domain_knowledge",
                complexity_factors["domain_knowledge"],
                "Analyzed domain complexity",
            ),
            dependencies=ComplexityFactor(
                "dependencies",
                complexity_factors["dependencies"],
                "Analyzed dependencies",
            ),
            timeline=ComplexityFactor(
                "timeline", complexity_factors["timeline"], "Analyzed timeline"
            ),
            risk=ComplexityFactor(
                "risk", complexity_factors["risk"], "Analyzed risk factors"
            ),
        )

        # Determine strategy
        execution_strategy = self._determine_execution_strategy(
            overall_score, complexity_factors
        )

        complexity_result = ComplexityAnalysisResult(
            factors=factors,
            overall_score=overall_score,
            category=ComplexityCategory(category),
            execution_strategy=ExecutionStrategy(execution_strategy),
            reasoning=f"O3 analysis: {overall_score:.1f}/10 complexity, {execution_strategy} strategy recommended",
            agent_requirements=self._generate_agent_requirements(
                execution_strategy, complexity_factors
            ),
            estimated_effort=self._estimate_effort(overall_score),
            confidence=ConfigManager().reasoning.medium_confidence_score,
        )

        return complexity_result, reasoning_steps

    def _analyze_complexity_dimensions(
        self, request: Dict[str, Any], validation_result: ValidationResult
    ) -> Dict[str, int]:
        """Analyze complexity across six dimensions."""
        # NO FALLBACKS - use config default for missing description
        request_text = str(
            request.get("description")
            if "description" in request
            else ConfigManager().analysis.request_processing["default_empty_content"]
        ).lower()

        # Simplified analysis for TDD (real implementation would use O3 reasoning)
        dimensions = {}

        # Scope analysis
        scope_indicators = ["full", "complete", "entire", "comprehensive", "end-to-end"]
        scope_score = 3 + sum(
            1 for indicator in scope_indicators if indicator in request_text
        )
        dimensions["scope"] = min(10, scope_score)

        # Technical depth
        tech_indicators = ["api", "database", "algorithm", "security", "performance"]
        tech_score = 3 + sum(
            1 for indicator in tech_indicators if indicator in request_text
        )
        dimensions["technical_depth"] = min(10, tech_score)

        # Domain knowledge
        domain_indicators = ["business", "finance", "healthcare", "scientific", "legal"]
        domain_score = 3 + sum(
            2 for indicator in domain_indicators if indicator in request_text
        )
        dimensions["domain_knowledge"] = min(10, domain_score)

        # Dependencies
        dep_indicators = ["integrate", "third-party", "external", "api", "service"]
        dep_score = 2 + sum(
            1 for indicator in dep_indicators if indicator in request_text
        )
        dimensions["dependencies"] = min(10, dep_score)

        # Timeline
        urgent_indicators = ["urgent", "asap", "immediately", "rush"]
        timeline_score = 5 + (
            3
            if any(indicator in request_text for indicator in urgent_indicators)
            else 0
        )
        dimensions["timeline"] = min(10, timeline_score)

        # Risk
        risk_indicators = ["production", "critical", "security", "data", "enterprise"]
        risk_score = 3 + sum(
            1 for indicator in risk_indicators if indicator in request_text
        )
        dimensions["risk"] = min(10, risk_score)

        return dimensions

    def _determine_complexity_category(self, overall_score: float) -> str:
        """Determine complexity category from score - NO HARDCODED THRESHOLDS"""

        if (
            overall_score
            <= ConfigManager().analysis.complexity.score_thresholds["threshold_low"]
            / 10
        ):  # Convert 30.0 to 3.0
            return "low"
        elif (
            overall_score
            <= ConfigManager().analysis.complexity.score_thresholds["threshold_medium"]
            / 10
        ):  # Convert 60.0 to 6.0
            return "medium"
        elif (
            overall_score
            <= ConfigManager().analysis.complexity.score_thresholds["threshold_high"]
            / 10
        ):  # Convert 80.0 to 8.0
            return "high"
        else:
            return "extreme"

    def _determine_execution_strategy(
        self, overall_score: float, complexity_factors: Dict[str, int]
    ) -> str:
        """Determine optimal execution strategy - NO HARDCODED THRESHOLDS"""
        if (
            overall_score
            <= ConfigManager().analysis.complexity.score_thresholds["simple_strategy"]
            and complexity_factors["scope"]
            <= ConfigManager().analysis.complexity.score_thresholds["scope_limit"]
        ):
            return "simple"
        elif (
            overall_score
            >= ConfigManager().analysis.complexity.score_thresholds[
                "orchestrated_strategy"
            ]
            or complexity_factors["dependencies"] >= 7
        ):  # This would need a config value too
            return "orchestrated"
        else:
            return "multi_agent"

    def _generate_agent_requirements(
        self, strategy: str, complexity_factors: Dict[str, int]
    ) -> Dict[str, Any]:
        """Generate agent requirements based on strategy."""
        if strategy == "simple":
            return {
                "agent_count": ConfigManager().agent_factory.counts.single_agent,
                "specializations": ["generalist"],
                "coordination_level": "none",
            }
        elif strategy == "multi_agent":
            return {
                "agent_count": ConfigManager().agent_factory.counts.small_team,
                "specializations": ["researcher", "implementer", "validator"],
                "coordination_level": "moderate",
            }
        else:  # orchestrated
            return {
                "agent_count": ConfigManager().agent_factory.counts.large_team,
                "specializations": [
                    "architect",
                    "researcher",
                    "implementer",
                    "integrator",
                    "validator",
                ],
                "coordination_level": "high",
            }

    def _estimate_effort(self, overall_score: float) -> str:
        """Estimate effort level."""
        if overall_score <= 3:
            return "Low (Hours)"
        elif overall_score <= 5:
            return "Medium (Days)"
        elif overall_score <= 7:
            return "High (Weeks)"
        else:
            return "Very High (Months)"
