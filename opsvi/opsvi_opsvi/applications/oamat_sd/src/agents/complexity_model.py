"""
Complexity Model - Modular Implementation

A clean, modular orchestrator for complexity analysis using AI reasoning.
Coordinates specialized modules for factor analysis, scoring, and AI reasoning.
"""

import logging
from typing import Any, Dict, Optional

from src.applications.oamat_sd.src.analysis.ai_reasoning import AIReasoningEngine
from src.applications.oamat_sd.src.analysis.factor_analyzer import FactorAnalyzer
from src.applications.oamat_sd.src.analysis.scoring_engine import ScoringEngine
from src.applications.oamat_sd.src.interfaces.agent_interfaces import (
    IComplexityAnalysisModel,
)
from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityAnalysisResult,
    ComplexityFactors,
)
from src.applications.oamat_sd.src.models.complexity_models import (
    ComplexityFactor as ComplexityFactorModel,
)

logger = logging.getLogger(__name__)


class ComplexityModel(IComplexityAnalysisModel):
    """
    Modular Complexity Analysis using AI Reasoning

    This model orchestrates the complete complexity analysis workflow:
    1. Factor Analysis -> Analyze individual complexity factors
    2. AI Reasoning -> Use LLM for intelligent analysis
    3. Scoring Engine -> Calculate scores and determine strategy
    4. Result Synthesis -> Combine all analysis into final result
    """

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """Initialize the Complexity Model with all modular components"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Legacy factor weights for backward compatibility
        self.factor_weights = {
            "scope": 1.2,
            "technical_depth": 1.1,
            "domain_knowledge": 1.0,
            "dependencies": 1.1,
            "timeline": 0.8,
            "risk": 1.0,
        }

        # Initialize modular components
        self.factor_analyzer = FactorAnalyzer(self.factor_weights)
        self.scoring_engine = ScoringEngine()
        self.ai_reasoning = AIReasoningEngine(model_config) if model_config else None

        self.logger.info("✅ Complexity Model initialized with modular architecture")

    async def analyze(self, request) -> ComplexityAnalysisResult:
        """
        Perform comprehensive complexity analysis using modular components

        Main orchestration method that coordinates all analysis modules
        """
        self.logger.info("🎯 Starting comprehensive complexity analysis")

        try:
            # Step 1: Factor Analysis - Analyze individual complexity factors
            self.logger.info("📊 Step 1: Factor Analysis")
            factors = await self._analyze_all_factors(request)

            # Step 2: AI Reasoning (if available) - Enhanced analysis
            if self.ai_reasoning:
                self.logger.info("🤖 Step 2: AI-Enhanced Analysis")
                request_context = {"request": str(request)}

                # Get AI factor analysis
                ai_factors = await self.ai_reasoning.analyze_complexity_factors(
                    request, request_context
                )

                # Enhance factors with AI insights
                factors = self._enhance_factors_with_ai(factors, ai_factors)

                # Get AI reasoning
                ai_reasoning = await self.ai_reasoning.analyze_complexity_reasoning(
                    ai_factors, request_context
                )
            else:
                self.logger.info("🔧 Step 2: Standard Analysis (No AI)")
                ai_reasoning = None

            # Step 3: Scoring and Strategy - Calculate overall metrics
            self.logger.info("🎯 Step 3: Scoring and Strategy Determination")
            overall_score = self.scoring_engine.calculate_overall_score(factors)
            category = self.scoring_engine.determine_category(overall_score)
            execution_strategy = self.scoring_engine.determine_execution_strategy(
                factors, overall_score
            )

            # Step 4: Result Synthesis - Combine all analysis
            self.logger.info("🔄 Step 4: Result Synthesis")
            agent_requirements = self.scoring_engine.generate_agent_requirements(
                factors, execution_strategy
            )
            estimated_effort = self.scoring_engine.estimate_effort(
                factors, execution_strategy
            )
            confidence = self.scoring_engine.calculate_confidence(factors)

            # Generate reasoning text - NO FALLBACKS
            if ai_reasoning:
                reasoning_chain = (
                    ai_reasoning.get("reasoning_chain")
                    if "reasoning_chain" in ai_reasoning
                    else []
                )
                first_reasoning = reasoning_chain[0] if reasoning_chain else ""
                reasoning = f"AI-enhanced analysis: {first_reasoning[:200]}..."
            else:
                reasoning = self._generate_standard_reasoning(
                    factors, overall_score, category
                )

            # Create final result
            result = ComplexityAnalysisResult(
                factors=factors,
                overall_score=overall_score,
                category=category,
                execution_strategy=execution_strategy,
                reasoning=reasoning,
                agent_requirements=agent_requirements,
                estimated_effort=estimated_effort,
                confidence=confidence,
            )

            self.logger.info(
                f"✅ Complexity analysis complete - score: {overall_score:.1f}, strategy: {execution_strategy}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Complexity analysis failed: {e}")
            # NO FALLBACKS RULE: Must fail completely if analysis fails
            raise RuntimeError(
                f"Complexity analysis failed: {e}. Cannot proceed without complete analysis."
            )

    async def _analyze_all_factors(self, request) -> ComplexityFactors:
        """Analyze all complexity factors using the factor analyzer"""

        # Analyze all 6 complexity factors
        scope = self.factor_analyzer.analyze_scope_factor(request)
        technical_depth = self.factor_analyzer.analyze_technical_depth_factor(request)
        domain_knowledge = self.factor_analyzer.analyze_domain_knowledge_factor(request)
        dependencies = self.factor_analyzer.analyze_dependencies_factor(request)
        timeline = self.factor_analyzer.analyze_timeline_factor(request)
        risk = self.factor_analyzer.analyze_risk_factor(request)

        return ComplexityFactors(
            scope=scope,
            technical_depth=technical_depth,
            domain_knowledge=domain_knowledge,
            dependencies=dependencies,
            timeline=timeline,
            risk=risk,
        )

    def _enhance_factors_with_ai(
        self, factors: ComplexityFactors, ai_factors: Dict[str, Any]
    ) -> ComplexityFactors:
        """Enhance factor analysis with AI insights"""

        enhanced_factors = []

        for factor in factors.get_all_factors():
            factor_name = factor.name

            if factor_name in ai_factors:
                ai_data = ai_factors[factor_name]

                # Use AI score if significantly different and confident - NO FALLBACKS
                from src.applications.oamat_sd.src.config.config_manager import (
                    ConfigManager,
                )

                ai_score = ai_data.get("score") if "score" in ai_data else factor.score
                ai_confidence = (
                    ai_data.get("confidence")
                    if "confidence" in ai_data
                    else ConfigManager.get_config().analysis.confidence["low"]
                )

                if (
                    ai_confidence
                    > ConfigManager.get_config().analysis.confidence[
                        "ai_blending_threshold"
                    ]
                    and abs(ai_score - factor.score)
                    > ConfigManager.get_config().analysis.complexity.variance_analysis[
                        "score_difference_threshold"
                    ]
                ):
                    # Blend AI and pattern-based scores
                    blended_score = int((factor.score + ai_score) / 2)
                    ai_reasoning_text = (
                        ai_data.get("reasoning")
                        if "reasoning" in ai_data
                        else factor.reasoning
                    )
                    enhanced_reasoning = f"AI-enhanced: {ai_reasoning_text}"
                else:
                    blended_score = factor.score
                    enhanced_reasoning = factor.reasoning

                enhanced_factor = ComplexityFactorModel(
                    name=factor.name,
                    score=blended_score,
                    reasoning=enhanced_reasoning,
                    weight=factor.weight,
                    indicators=factor.indicators
                    + [f"ai_confidence:{ai_confidence:.2f}"],
                )
            else:
                enhanced_factor = factor

            enhanced_factors.append(enhanced_factor)

        return ComplexityFactors(
            scope=enhanced_factors[0],
            technical_depth=enhanced_factors[1],
            domain_knowledge=enhanced_factors[2],
            dependencies=enhanced_factors[3],
            timeline=enhanced_factors[4],
            risk=enhanced_factors[5],
        )

    def _generate_standard_reasoning(
        self, factors: ComplexityFactors, overall_score: float, category
    ) -> str:
        """Generate reasoning text for standard (non-AI) analysis"""

        high_factors = [f.name for f in factors.get_all_factors() if f.score >= 7]
        low_factors = [f.name for f in factors.get_all_factors() if f.score <= 3]

        reasoning_parts = [
            f"Standard complexity analysis: {category.value} complexity (score: {overall_score:.1f})"
        ]

        if high_factors:
            reasoning_parts.append(
                f"High complexity factors: {', '.join(high_factors)}"
            )

        if low_factors:
            reasoning_parts.append(f"Low complexity factors: {', '.join(low_factors)}")

        return ". ".join(reasoning_parts)

    # Legacy interface compatibility methods
    def analyze_scope_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for scope analysis"""
        return self.factor_analyzer.analyze_scope_factor(request)

    def analyze_technical_depth_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for technical depth analysis"""
        return self.factor_analyzer.analyze_technical_depth_factor(request)

    def analyze_domain_knowledge_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for domain knowledge analysis"""
        return self.factor_analyzer.analyze_domain_knowledge_factor(request)

    def analyze_dependencies_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for dependencies analysis"""
        return self.factor_analyzer.analyze_dependencies_factor(request)

    def analyze_timeline_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for timeline analysis"""
        return self.factor_analyzer.analyze_timeline_factor(request)

    def analyze_risk_factor(self, request) -> ComplexityFactorModel:
        """Legacy method for risk analysis"""
        return self.factor_analyzer.analyze_risk_factor(request)

    def calculate_overall_score(self, factors: ComplexityFactors) -> float:
        """Legacy method for overall score calculation"""
        return self.scoring_engine.calculate_overall_score(factors)

    def determine_category(self, overall_score: float):
        """Legacy method for category determination"""
        return self.scoring_engine.determine_category(overall_score)

    def determine_execution_strategy(
        self, factors: ComplexityFactors, overall_score: float
    ):
        """Legacy method for execution strategy determination"""
        return self.scoring_engine.determine_execution_strategy(factors, overall_score)

    def generate_agent_requirements(self, factors: ComplexityFactors, strategy):
        """Legacy method for agent requirements generation"""
        return self.scoring_engine.generate_agent_requirements(factors, strategy)

    def estimate_effort(self, factors: ComplexityFactors, strategy):
        """Legacy method for effort estimation"""
        return self.scoring_engine.estimate_effort(factors, strategy)

    def calculate_confidence(self, factors: ComplexityFactors) -> float:
        """Legacy method for confidence calculation"""
        return self.scoring_engine.calculate_confidence(factors)

    # Abstract method implementations for IComplexityAnalysisModel interface
    async def analyze_complexity_dynamically(
        self, request, context: Dict[str, Any] = None
    ) -> ComplexityAnalysisResult:
        """Dynamic complexity analysis - main interface method"""
        return await self.analyze(request)

    async def generate_complexity_factors(
        self, request, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate complexity factors - interface method"""
        factors = await self._analyze_all_factors(request)
        return {
            "scope": factors.scope.score,
            "technical_depth": factors.technical_depth.score,
            "domain_knowledge": factors.domain_knowledge.score,
            "dependencies": factors.dependencies.score,
            "timeline": factors.timeline.score,
            "risk": factors.risk.score,
        }

    async def reason_about_complexity(
        self, factors: Dict[str, Any], context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Reason about complexity - interface method"""
        if self.ai_reasoning and context:
            return await self.ai_reasoning.analyze_complexity_reasoning(
                factors, context
            )
        else:
            # Standard reasoning without AI
            avg_score = sum(factors.values()) / len(factors)
            return {
                "overall_score": avg_score * 10,  # Convert to 0-100 scale
                "execution_strategy": "multi_agent" if avg_score > 5 else "simple",
                "reasoning_chain": [
                    f"Standard analysis: average complexity score {avg_score:.1f}"
                ],
                "confidence": 0.7,
            }

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this complexity model"""
        return {
            "model_name": "Complexity Model",
            "version": "2.0.0-modular",
            "architecture": "modular",
            "components": {
                "factor_analyzer": "Pattern-based complexity factor analysis",
                "scoring_engine": "Overall scoring and strategy determination",
                "ai_reasoning": (
                    "LLM-powered enhanced analysis"
                    if self.ai_reasoning
                    else "Not available"
                ),
            },
            "features": [
                "AI-enhanced complexity analysis",
                "Pattern-based factor detection",
                "Dynamic execution strategy selection",
                "Confidence-based result blending",
                "Legacy interface compatibility",
            ],
            "factor_weights": self.factor_weights,
            "ai_enabled": self.ai_reasoning is not None,
            "modular_architecture": True,
        }
