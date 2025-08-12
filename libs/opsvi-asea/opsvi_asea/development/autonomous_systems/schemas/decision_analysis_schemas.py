"""
Pydantic schemas for external reasoning service decision analysis.
These schemas ensure type safety and validation for AI model responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ReasoningStep(BaseModel):
    """Individual step in the reasoning process"""

    step_number: int = Field(description="Step number in reasoning sequence")
    description: str = Field(description="Description of this reasoning step")
    conclusion: str = Field(description="Conclusion reached in this step")
    confidence: float = Field(
        description="Confidence level (0.0 to 1.0)", ge=0.0, le=1.0
    )
    evidence_cited: List[str] = Field(
        description="Evidence or context used in this step", default_factory=list
    )


class EvidenceAssessment(BaseModel):
    """Assessment of evidence supporting the decision"""

    strength_score: float = Field(
        description="Evidence strength (0.0 to 1.0)", ge=0.0, le=1.0
    )
    evidence_types: List[str] = Field(
        description="Types of evidence found", default_factory=list
    )
    gaps_identified: List[str] = Field(
        description="Gaps in evidence", default_factory=list
    )
    supporting_facts: List[str] = Field(
        description="Supporting facts from context", default_factory=list
    )
    contradicting_factors: List[str] = Field(
        description="Factors that contradict the decision", default_factory=list
    )


class OperationalFeasibility(BaseModel):
    """Assessment of operational feasibility"""

    feasibility_score: float = Field(
        description="Feasibility score (0.0 to 1.0)", ge=0.0, le=1.0
    )
    implementation_complexity: str = Field(
        description="Complexity level (low/medium/high)"
    )
    resource_requirements: List[str] = Field(
        description="Required resources", default_factory=list
    )
    potential_blockers: List[str] = Field(
        description="Potential implementation blockers", default_factory=list
    )
    success_probability: float = Field(
        description="Probability of successful execution (0.0 to 1.0)", ge=0.0, le=1.0
    )


class StrategicAlignment(BaseModel):
    """Assessment of strategic alignment with goals"""

    alignment_score: float = Field(
        description="Strategic alignment score (0.0 to 1.0)", ge=0.0, le=1.0
    )
    goal_advancement: List[str] = Field(
        description="Goals this decision advances", default_factory=list
    )
    goal_conflicts: List[str] = Field(
        description="Goals this decision conflicts with", default_factory=list
    )
    long_term_impact: str = Field(description="Expected long-term impact")
    strategic_value: str = Field(description="Strategic value assessment")


class CompoundLearningPotential(BaseModel):
    """Assessment of compound learning opportunities"""

    learning_score: float = Field(
        description="Compound learning potential (0.0 to 1.0)", ge=0.0, le=1.0
    )
    knowledge_connections: List[str] = Field(
        description="Knowledge areas this connects", default_factory=list
    )
    skill_development: List[str] = Field(
        description="Skills this decision develops", default_factory=list
    )
    future_decision_enablement: List[str] = Field(
        description="Future decisions this enables", default_factory=list
    )
    multiplicative_effects: List[str] = Field(
        description="Multiplicative learning effects", default_factory=list
    )


class RiskOpportunityAnalysis(BaseModel):
    """Risk and opportunity analysis"""

    risk_level: str = Field(description="Overall risk level (low/medium/high)")
    identified_risks: List[str] = Field(
        description="Identified risks", default_factory=list
    )
    risk_mitigation: List[str] = Field(
        description="Risk mitigation strategies", default_factory=list
    )
    opportunities: List[str] = Field(
        description="Opportunities identified", default_factory=list
    )
    opportunity_cost: str = Field(description="Assessment of opportunity cost")


class ReasoningValidation(BaseModel):
    """Validation of reasoning consistency"""

    logical_consistency: float = Field(
        description="Logical consistency score (0.0 to 1.0)", ge=0.0, le=1.0
    )
    reasoning_gaps: List[str] = Field(
        description="Gaps in reasoning", default_factory=list
    )
    assumption_validity: List[str] = Field(
        description="Assessment of assumptions", default_factory=list
    )
    conclusion_support: float = Field(
        description="How well rationale supports decision (0.0 to 1.0)", ge=0.0, le=1.0
    )
    alternative_considerations: List[str] = Field(
        description="Alternative approaches considered", default_factory=list
    )


class ContextualFactors(BaseModel):
    """Contextual factors from knowledge base"""

    relevant_memories: List[Dict[str, Any]] = Field(
        description="Relevant memories from knowledge base", default_factory=list
    )
    cognitive_concepts: List[Dict[str, Any]] = Field(
        description="Related cognitive concepts", default_factory=list
    )
    semantic_relationships: List[Dict[str, Any]] = Field(
        description="Relevant semantic relationships", default_factory=list
    )
    historical_patterns: List[str] = Field(
        description="Historical decision patterns", default_factory=list
    )


class DecisionQualityMetrics(BaseModel):
    """Comprehensive decision quality metrics"""

    overall_quality_score: float = Field(
        description="Overall decision quality (0.0 to 1.0)", ge=0.0, le=1.0
    )
    evidence_strength: float = Field(
        description="Evidence strength component", ge=0.0, le=1.0
    )
    operational_feasibility: float = Field(
        description="Operational feasibility component", ge=0.0, le=1.0
    )
    strategic_alignment: float = Field(
        description="Strategic alignment component", ge=0.0, le=1.0
    )
    compound_learning: float = Field(
        description="Compound learning component", ge=0.0, le=1.0
    )
    risk_adjusted_score: float = Field(
        description="Risk-adjusted quality score", ge=0.0, le=1.0
    )


class ExternalReasoningAnalysis(BaseModel):
    """Complete external reasoning analysis result"""

    analysis_id: str = Field(description="Unique analysis identifier")
    decision: str = Field(description="Decision being analyzed")
    rationale: str = Field(description="Provided rationale")
    analysis_timestamp: datetime = Field(description="When analysis was performed")

    # Core reasoning components
    reasoning_steps: List[ReasoningStep] = Field(
        description="Step-by-step reasoning analysis"
    )
    evidence_assessment: EvidenceAssessment = Field(
        description="Evidence strength analysis"
    )
    operational_feasibility: OperationalFeasibility = Field(
        description="Feasibility assessment"
    )
    strategic_alignment: StrategicAlignment = Field(
        description="Strategic alignment analysis"
    )
    compound_learning_potential: CompoundLearningPotential = Field(
        description="Learning opportunity analysis"
    )
    risk_opportunity_analysis: RiskOpportunityAnalysis = Field(
        description="Risk and opportunity assessment"
    )
    reasoning_validation: ReasoningValidation = Field(
        description="Reasoning consistency validation"
    )

    # Context and metrics
    contextual_factors: ContextualFactors = Field(
        description="Relevant context from knowledge base"
    )
    quality_metrics: DecisionQualityMetrics = Field(
        description="Comprehensive quality metrics"
    )

    # Recommendations and insights
    recommendations: List[str] = Field(
        description="Specific recommendations for improvement"
    )
    key_insights: List[str] = Field(description="Key insights from analysis")
    alternative_approaches: List[str] = Field(
        description="Alternative decision approaches"
    )

    # Meta information
    model_used: str = Field(description="AI model used for analysis")
    analysis_cost: float = Field(description="Cost of analysis in USD")
    confidence_level: float = Field(
        description="Overall confidence in analysis", ge=0.0, le=1.0
    )
    context_quality: float = Field(
        description="Quality of context gathered", ge=0.0, le=1.0
    )


class DecisionOutcome(BaseModel):
    """Decision outcome tracking for learning"""

    decision_id: str = Field(description="Reference to original decision analysis")
    outcome_timestamp: datetime = Field(description="When outcome was recorded")
    actual_result: str = Field(description="What actually happened")
    success_level: float = Field(
        description="Success level (0.0 to 1.0)", ge=0.0, le=1.0
    )
    lessons_learned: List[str] = Field(description="Lessons learned from outcome")
    prediction_accuracy: float = Field(
        description="How accurate was the analysis", ge=0.0, le=1.0
    )
    unexpected_factors: List[str] = Field(description="Unexpected factors that emerged")


class ReasoningPattern(BaseModel):
    """Learned reasoning patterns for improvement"""

    pattern_id: str = Field(description="Unique pattern identifier")
    pattern_type: str = Field(description="Type of reasoning pattern")
    decision_contexts: List[str] = Field(
        description="Contexts where this pattern applies"
    )
    effectiveness_score: float = Field(
        description="Pattern effectiveness (0.0 to 1.0)", ge=0.0, le=1.0
    )
    usage_count: int = Field(description="How often this pattern has been used")
    success_rate: float = Field(
        description="Success rate when pattern is applied", ge=0.0, le=1.0
    )
    pattern_description: str = Field(description="Description of the reasoning pattern")


class ExternalReasoningConfig(BaseModel):
    """Configuration for external reasoning service"""

    enabled: bool = Field(description="Whether external reasoning is enabled")
    openai_api_key: str = Field(description="OpenAI API key")
    reasoning_model: str = Field(description="Model for complex reasoning")
    standard_model: str = Field(description="Model for standard analysis")
    fallback_model: str = Field(description="Fallback model")
    max_context_tokens: int = Field(description="Maximum context tokens")
    cost_per_analysis_limit: float = Field(description="Maximum cost per analysis")


# Schema registry for dynamic lookup
EXTERNAL_REASONING_SCHEMAS = {
    "decision_analysis": ExternalReasoningAnalysis,
    "decision_outcome": DecisionOutcome,
    "reasoning_pattern": ReasoningPattern,
    "config": ExternalReasoningConfig,
}


def get_schema_for_operation(operation: str) -> BaseModel:
    """
    Get the appropriate Pydantic schema for an operation.

    Args:
        operation: Operation name

    Returns:
        Appropriate Pydantic schema class
    """
    return EXTERNAL_REASONING_SCHEMAS.get(operation, ExternalReasoningAnalysis)
