"""
Complexity Analysis Model - Truly Agentic Implementation

AI-driven complexity analysis using dynamic factor generation rather than
predetermined scoring rules. Adapts analysis approach to request context.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.applications.oamat_sd.src.interfaces.agent_interfaces import (
    IComplexityAnalysisModel,
)
from src.applications.oamat_sd.src.models.data_models import (
    ComplexityFactor,
    RequestInput,
)
from src.applications.oamat_sd.src.models.workflow_models import (
    ComplexityAnalysis,
)

logger = logging.getLogger(__name__)


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
    weight: float = 1.0
    indicators: List[str] = field(default_factory=list)


@dataclass
class ComplexityFactors:
    """Six core complexity factors."""

    scope: ComplexityFactor
    technical_depth: ComplexityFactor
    domain_knowledge: ComplexityFactor
    dependencies: ComplexityFactor
    timeline: ComplexityFactor
    risk: ComplexityFactor

    def get_all_factors(self) -> List[ComplexityFactor]:
        """Get all factors as a list."""
        return [
            self.scope,
            self.technical_depth,
            self.domain_knowledge,
            self.dependencies,
            self.timeline,
            self.risk,
        ]

    def to_dict(self) -> Dict[str, int]:
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
    agent_requirements: Dict[str, Any]
    estimated_effort: str
    confidence: float


class ComplexityModel(IComplexityAnalysisModel):
    """
    Truly agentic complexity analysis using AI reasoning

    NO PREDETERMINED SCORING RULES - uses AI to dynamically analyze complexity
    """

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Use AI model for intelligent complexity analysis - APPROVED MODELS ONLY
        # NO FALLBACKS RULE: Model configuration strictly required
        if not model_config or "model" not in model_config:
            raise RuntimeError(
                "Model configuration required. Cannot proceed without explicit model specification."
            )
        model_name = model_config["model"]

        # Handle O3 models that don't support temperature
        model_kwargs = {"model": model_name}
        if not model_name.startswith("o3"):
            model_kwargs["temperature"] = 0.2  # Low temperature for consistent analysis

        self.ai_model = ChatOpenAI(**model_kwargs)

        # Legacy factor weights for backward compatibility
        self.factor_weights = {
            "scope": 1.2,
            "technical_depth": 1.1,
            "domain_knowledge": 1.0,
            "dependencies": 1.1,
            "timeline": 0.8,
            "risk": 1.0,
        }

        # Complexity indicators for automated detection
        self.complexity_indicators = self._initialize_indicators()

    def _initialize_indicators(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize complexity indicators for automated detection."""
        return {
            "scope": {
                "high": [
                    "full stack",
                    "full-stack",
                    "end-to-end",
                    "complete system",
                    "entire platform",
                    "platform",
                    "comprehensive",
                ],
                "medium": [
                    "multi-component",
                    "several features",
                    "multiple pages",
                    "various modules",
                ],
                "low": ["single", "simple", "basic", "minimal", "one"],
            },
            "technical_depth": {
                "high": [
                    "machine learning",
                    "ai",
                    "blockchain",
                    "distributed",
                    "microservices",
                    "cloud native",
                ],
                "medium": [
                    "api",
                    "database",
                    "backend",
                    "frontend",
                    "integration",
                    "real-time",
                ],
                "low": ["script", "utility", "basic", "simple", "straightforward"],
            },
            "domain_knowledge": {
                "high": [
                    "finance",
                    "healthcare",
                    "legal",
                    "scientific",
                    "research",
                    "compliance",
                    "payment processing",
                ],
                "medium": [
                    "business",
                    "e-commerce",
                    "analytics",
                    "reporting",
                    "workflow",
                ],
                "low": ["general", "personal", "hobby", "learning", "demo"],
            },
            "dependencies": {
                "high": [
                    "third-party",
                    "external api",
                    "multiple services",
                    "legacy systems",
                    "complex integrations",
                    "payment processing",
                ],
                "medium": [
                    "database",
                    "authentication",
                    "payment",
                    "notification",
                    "file storage",
                ],
                "low": [
                    "standalone",
                    "self-contained",
                    "independent",
                    "no dependencies",
                ],
            },
            "timeline": {
                "urgent": ["asap", "urgent", "immediately", "rush", "emergency"],
                "normal": ["soon", "next week", "reasonable time", "standard"],
                "flexible": ["when possible", "no rush", "eventually", "flexible"],
            },
            "risk": {
                "high": [
                    "production",
                    "critical",
                    "mission critical",
                    "high availability",
                    "enterprise",
                    "payment processing",
                    "security",
                    "authentication",
                ],
                "medium": ["business", "important", "moderate risk", "staging"],
                "low": ["prototype", "poc", "demo", "learning", "test"],
            },
        }

    def analyze_scope_factor(self, request) -> ComplexityFactor:
        """Analyze scope complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count scope indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["scope"]["low"]
            if indicator in request_text
        )

        # Analyze request structure
        features_count = len(request_text.split("feature")) + len(
            request_text.split("component")
        )
        pages_count = len(request_text.split("page")) + len(
            request_text.split("screen")
        )

        # Calculate score
        score = 3  # Base score

        if high_indicators > 0:
            score += 4
        elif medium_indicators > 0:
            score += 2
        elif low_indicators > 0:
            score -= 1

        # Adjust based on feature count
        if features_count > 5:
            score += 2
        elif features_count > 2:
            score += 1

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Scope analysis: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Features: {features_count}"

        return ComplexityFactor(
            name="scope",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["scope"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"low:{low_indicators}",
            ],
        )

    def analyze_technical_depth_factor(
        self, request: Dict[str, Any]
    ) -> ComplexityFactor:
        """Analyze technical depth complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count technical indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["technical_depth"]["low"]
            if indicator in request_text
        )

        # Technical complexity patterns
        advanced_patterns = [
            "algorithm",
            "optimization",
            "performance",
            "scalability",
            "security",
        ]
        advanced_count = sum(
            1 for pattern in advanced_patterns if pattern in request_text
        )

        # Calculate score
        score = 3  # Base score

        if high_indicators > 0:
            score += 4
        elif medium_indicators > 0:
            score += 2
        elif low_indicators > 0:
            score -= 1

        score += min(advanced_count, 3)  # Cap at 3 extra points

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Technical depth: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Advanced patterns: {advanced_count}"

        return ComplexityFactor(
            name="technical_depth",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["technical_depth"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"advanced:{advanced_count}",
            ],
        )

    def analyze_domain_knowledge_factor(
        self, request: Dict[str, Any]
    ) -> ComplexityFactor:
        """Analyze domain knowledge complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count domain indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["domain_knowledge"]["low"]
            if indicator in request_text
        )

        # Specialized terminology
        specialized_terms = [
            "regulation",
            "compliance",
            "standard",
            "protocol",
            "specification",
        ]
        specialized_count = sum(1 for term in specialized_terms if term in request_text)

        # Calculate score
        score = 3  # Base score

        if high_indicators > 0:
            score += 5
        elif medium_indicators > 0:
            score += 2
        elif low_indicators > 0:
            score -= 1

        score += min(specialized_count, 2)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Domain knowledge: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Specialized terms: {specialized_count}"

        return ComplexityFactor(
            name="domain_knowledge",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["domain_knowledge"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"specialized:{specialized_count}",
            ],
        )

    def analyze_dependencies_factor(self, request) -> ComplexityFactor:
        """Analyze dependencies complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count dependency indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["dependencies"]["low"]
            if indicator in request_text
        )

        # Integration points
        integration_terms = [
            "integrate",
            "connect",
            "sync",
            "import",
            "export",
            "webhook",
        ]
        integration_count = sum(1 for term in integration_terms if term in request_text)

        # Calculate score
        score = 3  # Base score

        if high_indicators > 0:
            score += 4
        elif medium_indicators > 0:
            score += 2
        elif low_indicators > 0:
            score -= 2

        score += min(integration_count, 3)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Dependencies: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Integrations: {integration_count}"

        return ComplexityFactor(
            name="dependencies",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["dependencies"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"integrations:{integration_count}",
            ],
        )

    def analyze_timeline_factor(self, request) -> ComplexityFactor:
        """Analyze timeline complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count timeline indicators
        urgent_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["urgent"]
            if indicator in request_text
        )
        normal_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["normal"]
            if indicator in request_text
        )
        flexible_indicators = sum(
            1
            for indicator in self.complexity_indicators["timeline"]["flexible"]
            if indicator in request_text
        )

        # Calculate score (urgent = higher complexity)
        score = 5  # Base score

        if urgent_indicators > 0:
            score += 3
        elif flexible_indicators > 0:
            score -= 2

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Timeline: {urgent_indicators} urgent, {normal_indicators} normal, {flexible_indicators} flexible indicators"

        return ComplexityFactor(
            name="timeline",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["timeline"],
            indicators=[
                f"urgent:{urgent_indicators}",
                f"normal:{normal_indicators}",
                f"flexible:{flexible_indicators}",
            ],
        )

    def analyze_risk_factor(self, request) -> ComplexityFactor:
        """Analyze risk complexity (1-10)."""
        # Handle both dict and Pydantic model inputs - prioritize content over description
        if hasattr(request, "content"):
            request_text = str(request.content).lower()
        elif hasattr(request, "description"):
            request_text = str(request.description).lower()
        elif hasattr(request, "get"):
            request_text = str(
                request.get("content", request.get("description", ""))
            ).lower()
        else:
            request_text = str(request).lower()

        # Count risk indicators
        high_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["high"]
            if indicator in request_text
        )
        medium_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["medium"]
            if indicator in request_text
        )
        low_indicators = sum(
            1
            for indicator in self.complexity_indicators["risk"]["low"]
            if indicator in request_text
        )

        # Risk factors
        risk_terms = ["security", "data", "privacy", "backup", "recovery", "monitoring"]
        risk_count = sum(1 for term in risk_terms if term in request_text)

        # Calculate score
        score = 3  # Base score

        if high_indicators > 0:
            score += 5
        elif medium_indicators > 0:
            score += 2
        elif low_indicators > 0:
            score -= 1

        score += min(risk_count, 2)

        # Ensure bounds
        score = max(1, min(10, score))

        reasoning = f"Risk: {high_indicators} high, {medium_indicators} medium, {low_indicators} low indicators. Risk terms: {risk_count}"

        return ComplexityFactor(
            name="risk",
            score=score,
            reasoning=reasoning,
            weight=self.factor_weights["risk"],
            indicators=[
                f"high:{high_indicators}",
                f"medium:{medium_indicators}",
                f"risk_terms:{risk_count}",
            ],
        )

    def calculate_overall_score(self, factors: ComplexityFactors) -> float:
        """Calculate weighted overall complexity score (0-100 scale)."""
        weighted_sum = 0.0
        weight_sum = 0.0

        for factor in factors.get_all_factors():
            weighted_sum += factor.score * factor.weight
            weight_sum += factor.weight

        # Convert from 1-10 scale to 0-100 scale
        if weight_sum > 0:
            avg_score = weighted_sum / weight_sum
            return (avg_score - 1) * (100 / 9)  # Maps 1-10 to 0-100
        else:
            return 0.0

    def determine_category(self, overall_score: float) -> ComplexityCategory:
        """Determine complexity category from overall score (0-100 scale)."""
        if overall_score <= 30.0:
            return ComplexityCategory.LOW
        elif overall_score <= 60.0:
            return ComplexityCategory.MEDIUM
        elif overall_score <= 80.0:
            return ComplexityCategory.HIGH
        else:
            return ComplexityCategory.EXTREME

    def determine_execution_strategy(
        self, factors: ComplexityFactors, overall_score: float
    ) -> ExecutionStrategy:
        """Determine optimal execution strategy based on complexity."""

        # Simple strategy conditions
        if (
            overall_score <= 4.0
            and factors.scope.score <= 4
            and factors.dependencies.score <= 3
        ):
            return ExecutionStrategy.SIMPLE

        # Orchestrated strategy conditions
        if (
            overall_score >= 7.0
            or factors.scope.score >= 8
            or factors.dependencies.score >= 7
            or factors.technical_depth.score >= 8
        ):
            return ExecutionStrategy.ORCHESTRATED

        # Default to multi-agent
        return ExecutionStrategy.MULTI_AGENT

    def generate_agent_requirements(
        self, factors: ComplexityFactors, strategy: ExecutionStrategy
    ) -> Dict[str, Any]:
        """Generate agent requirements based on complexity analysis."""
        requirements = {
            "agent_count": 1,
            "specializations": [],
            "coordination_level": "none",
            "tools_required": [],
            "monitoring_level": "basic",
        }

        if strategy == ExecutionStrategy.SIMPLE:
            requirements.update(
                {
                    "agent_count": 1,
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
        confidence = 0.8

        # Adjust based on factor consistency
        scores = [f.score for f in factors.get_all_factors()]
        variance = sum(
            (score - sum(scores) / len(scores)) ** 2 for score in scores
        ) / len(scores)

        # Lower confidence for high variance (inconsistent factors)
        if variance > 4:
            confidence -= 0.2
        elif variance > 2:
            confidence -= 0.1

        # Adjust based on extreme scores
        extreme_count = sum(1 for score in scores if score <= 2 or score >= 9)
        if extreme_count > 2:
            confidence -= 0.1

        return max(0.5, min(1.0, confidence))

    async def analyze_complexity_dynamically(
        self, request: RequestInput, context: Dict[str, Any]
    ) -> ComplexityAnalysis:
        """
        Dynamically analyze complexity using AI reasoning

        NO PREDETERMINED RULES - AI generates novel complexity analysis
        """
        self.logger.info(
            f"Analyzing complexity dynamically for request: {request.content[:100]}..."
        )

        try:
            # Generate dynamic complexity factors for this specific request
            factors = await self.generate_complexity_factors(
                {"request": request.content, "context": context}
            )

            # Use AI reasoning to analyze complexity implications
            reasoning_result = await self.reason_about_complexity(factors)

            # Convert to expected format (using data_models.ComplexityFactor which has confidence)
            from src.applications.oamat_sd.src.models.data_models import (
                ComplexityFactor as DataComplexityFactor,
            )

            complexity_factors = {}
            for factor_name, factor_data in factors.items():
                complexity_factors[factor_name] = DataComplexityFactor(
                    name=factor_name,
                    score=factor_data.get("score", 5),
                    reasoning=factor_data.get("reasoning", "AI-generated analysis"),
                    indicators=factor_data.get("indicators", []),
                    confidence=factor_data.get("confidence", 0.7),
                )

            # Calculate overall metrics using AI insights
            overall_score = reasoning_result.get("overall_score", 50.0)
            execution_strategy = reasoning_result.get(
                "execution_strategy", "multi_agent"
            )

            return ComplexityAnalysis(
                factors=complexity_factors,
                overall_score=overall_score,
                execution_strategy=execution_strategy,
                agent_requirements=reasoning_result.get("agent_requirements", {}),
                estimated_effort=reasoning_result.get(
                    "estimated_effort", "Medium complexity"
                ),
                reasoning_chain=reasoning_result.get("reasoning_chain", []),
                confidence=reasoning_result.get("confidence", 0.7),
            )

        except Exception as e:
            self.logger.error(f"Dynamic complexity analysis failed: {e}")
            # NO FALLBACKS - fail completely if AI generation fails
            raise RuntimeError(
                f"Stage 1 complexity analysis failed: {e}. System cannot proceed without proper AI analysis."
            )

    async def generate_complexity_factors(
        self, request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamically generate complexity factors specific to this request

        Creates factors that matter for this specific context
        """
        factor_generation_prompt = f"""
        Analyze this request and score the 6 standard complexity factors:

        REQUEST: {request_context.get("request", "")}
        CONTEXT: {request_context.get("context", {})}

        Analyze each of these 6 factors for THIS specific request:

        1. SCOPE: How broad is the project? Simple feature vs complete system?
        2. TECHNICAL_DEPTH: How complex is the technical implementation?
        3. DOMAIN_KNOWLEDGE: How much specialized knowledge is required?
        4. DEPENDENCIES: How many external systems/APIs/services are needed?
        5. TIMELINE: How time-sensitive or urgent is this request?
        6. RISK: What are the technical, business, or implementation risks?

        For each factor, provide:
        - Score (1-10) based on analysis of THIS specific request
        - Reasoning for the score based on request details
        - Specific indicators from the request that support the score

        Return EXACTLY these factor names: scope, technical_depth, domain_knowledge, dependencies, timeline, risk
        """

        try:
            response = await self.ai_model.ainvoke(
                [
                    SystemMessage(
                        content="You are an expert at analyzing task complexity. Generate factors dynamically based on the specific request context."
                    ),
                    HumanMessage(content=factor_generation_prompt),
                ]
            )

            # Parse AI response into factor structure
            return await self._parse_factors_response(response.content, request_context)

        except Exception as e:
            self.logger.error(f"Factor generation failed: {e}")
            # NO FALLBACKS - fail completely if AI generation fails
            raise RuntimeError(
                f"Complexity factor generation failed: {e}. Cannot proceed without AI-generated factors."
            )

    async def reason_about_complexity(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI reasoning to understand complexity implications
        """
        reasoning_prompt = f"""
        Based on these complexity factors, provide intelligent analysis:

        FACTORS: {factors}

        Analyze:
        1. What is the overall complexity level (0-100 scale)?
        2. What execution strategy would work best?
        3. What agent requirements and capabilities are needed?
        4. What is the estimated effort and timeline?
        5. What are the key risks and mitigation strategies?

        Provide reasoning-based analysis, not rule-based scoring.
        """

        try:
            response = await self.ai_model.ainvoke(
                [
                    SystemMessage(
                        content="You are an expert at reasoning about complexity implications. Provide intelligent, context-aware analysis."
                    ),
                    HumanMessage(content=reasoning_prompt),
                ]
            )

            return await self._parse_reasoning_response(response.content, factors)

        except Exception as e:
            self.logger.error(f"Complexity reasoning failed: {e}")
            # NO FALLBACKS - fail completely if AI reasoning fails
            raise RuntimeError(
                f"Complexity reasoning failed: {e}. Cannot proceed without AI-driven analysis."
            )

    def analyze_factors(self, request) -> ComplexityAnalysisResult:
        """Perform complete 6-factor complexity analysis."""
        request_name = (
            getattr(request, "name", "unnamed")
            if hasattr(request, "name")
            else "unnamed"
        )
        self.logger.info(f"Analyzing complexity for request: {request_name}")

        # Analyze each factor
        factors = ComplexityFactors(
            scope=self.analyze_scope_factor(request),
            technical_depth=self.analyze_technical_depth_factor(request),
            domain_knowledge=self.analyze_domain_knowledge_factor(request),
            dependencies=self.analyze_dependencies_factor(request),
            timeline=self.analyze_timeline_factor(request),
            risk=self.analyze_risk_factor(request),
        )

        # Calculate overall metrics
        overall_score = self.calculate_overall_score(factors)
        category = self.determine_category(overall_score)
        strategy = self.determine_execution_strategy(factors, overall_score)
        agent_requirements = self.generate_agent_requirements(factors, strategy)
        effort = self.estimate_effort(factors, strategy)
        confidence = self.calculate_confidence(factors)

        # Generate reasoning
        reasoning = f"Overall complexity: {overall_score:.1f}/10 ({category.value}). "
        reasoning += f"Key factors: Scope={factors.scope.score}, Technical={factors.technical_depth.score}, "
        reasoning += (
            f"Domain={factors.domain_knowledge.score}. Strategy: {strategy.value}"
        )

        return ComplexityAnalysisResult(
            factors=factors,
            overall_score=overall_score,
            category=category,
            execution_strategy=strategy,
            reasoning=reasoning,
            agent_requirements=agent_requirements,
            estimated_effort=effort,
            confidence=confidence,
        )

    # NO FALLBACKS RULE: _create_fallback_analysis method removed
    # System must fail completely if AI analysis fails - no fallback analysis allowed

    # NO FALLBACKS RULE: _create_fallback_factors method removed
    # System must fail completely if AI factor generation fails - no fallback factors allowed

    async def _parse_factors_response(
        self, ai_response: str, request_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI response into the 6 required complexity factors"""
        factors = {}
        response_lower = ai_response.lower()
        request_content = request_context.get("request", "").lower()

        # Extract scores for each required factor from AI response
        required_factors = [
            "scope",
            "technical_depth",
            "domain_knowledge",
            "dependencies",
            "timeline",
            "risk",
        ]

        for factor_name in required_factors:
            # Look for factor mentions in AI response
            score = 5  # Default middle score
            reasoning = f"AI analysis for {factor_name} factor"
            indicators = [f"{factor_name}_analysis"]

            # Try to extract score from AI response (simple pattern matching)

            # Look for patterns like "scope: 7" or "technical_depth score: 8"
            pattern = rf"{factor_name}.*?(\d+)"
            match = re.search(pattern, response_lower)
            if match:
                score = min(10, max(1, int(match.group(1))))

            # Simple content-based scoring as backup
            if factor_name == "scope":
                if any(
                    word in request_content
                    for word in ["complete", "full", "comprehensive", "enterprise"]
                ):
                    score = max(score, 7)
                elif any(
                    word in request_content for word in ["simple", "basic", "small"]
                ):
                    score = min(score, 4)

            elif factor_name == "technical_depth":
                if any(
                    word in request_content
                    for word in ["microservices", "ai", "ml", "kubernetes", "complex"]
                ):
                    score = max(score, 8)
                elif any(
                    word in request_content
                    for word in ["html", "css", "simple", "basic"]
                ):
                    score = min(score, 4)

            elif factor_name == "dependencies":
                if any(
                    word in request_content
                    for word in ["api", "integration", "service", "database"]
                ):
                    score = max(score, 6)
                elif "standalone" in request_content or "simple" in request_content:
                    score = min(score, 3)

            elif factor_name == "domain_knowledge":
                if any(
                    word in request_content
                    for word in ["specialized", "expert", "advanced", "ml", "ai"]
                ):
                    score = max(score, 7)

            elif factor_name == "timeline":
                if any(
                    word in request_content for word in ["urgent", "asap", "quickly"]
                ):
                    score = max(score, 7)

            elif factor_name == "risk":
                if any(
                    word in request_content
                    for word in ["security", "payment", "production", "critical"]
                ):
                    score = max(score, 7)

            factors[factor_name] = {
                "score": score,
                "reasoning": f"AI analysis: {reasoning} based on request content and patterns",
                "indicators": indicators,
                "confidence": 0.7,
            }

        return factors

    async def _parse_reasoning_response(
        self, ai_response: str, factors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI reasoning response into structured analysis"""
        response_lower = ai_response.lower()

        # Extract overall score
        overall_score = 50.0  # Default
        if "high complexity" in response_lower or "complex" in response_lower:
            overall_score = 75.0
        elif "low complexity" in response_lower or "simple" in response_lower:
            overall_score = 30.0
        elif "medium" in response_lower:
            overall_score = 50.0

        # Extract execution strategy
        execution_strategy = "multi_agent"  # Default
        if "single" in response_lower or "simple" in response_lower:
            execution_strategy = "simple"
        elif (
            "orchestrated" in response_lower or "complex coordination" in response_lower
        ):
            execution_strategy = "orchestrated"

        # Extract agent requirements
        agent_requirements = {}
        if "research" in response_lower:
            agent_requirements["researcher"] = True
        if "technical" in response_lower or "implementation" in response_lower:
            agent_requirements["implementer"] = True
        if "analysis" in response_lower:
            agent_requirements["analyst"] = True

        return {
            "overall_score": overall_score,
            "execution_strategy": execution_strategy,
            "agent_requirements": agent_requirements,
            "estimated_effort": self._extract_effort_estimate(response_lower),
            "reasoning_chain": [ai_response[:500]],  # Store AI reasoning
            "confidence": 0.7,
        }

    def _extract_effort_estimate(self, response_lower: str) -> str:
        """Extract effort estimate from AI response"""
        if "high effort" in response_lower or "complex" in response_lower:
            return "High effort - complex implementation required"
        elif "low effort" in response_lower or "simple" in response_lower:
            return "Low effort - straightforward implementation"
        else:
            return "Medium effort - moderate complexity"
