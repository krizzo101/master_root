"""
Simplified schemas optimized for OpenAI Responses API structured outputs.
These schemas avoid complex nested structures that cause validation issues.
"""

from pydantic import BaseModel, Field


class BudgetAnalysisSimple(BaseModel):
    """Simplified budget analysis schema for Responses API compatibility."""

    total_cost: float = Field(description="Total estimated cost in USD")
    risk_level: str = Field(description="Risk assessment: high, medium, or low")
    viable: bool = Field(description="Whether the decision is financially viable")
    recommendation: str = Field(description="Budget recommendation summary")
    cost_breakdown: str = Field(description="Detailed cost breakdown as text")
    decision_factors: str = Field(description="Key decision factors as text")


class WorkflowOptimizationSimple(BaseModel):
    """Simplified workflow optimization schema for Responses API compatibility."""

    complexity_score: int = Field(description="Workflow complexity score (1-10)")
    optimization_potential: str = Field(
        description="Optimization potential: high, medium, or low"
    )
    recommended_changes: str = Field(description="Recommended workflow changes as text")
    efficiency_gain: str = Field(description="Expected efficiency improvements as text")
    implementation_priority: str = Field(
        description="Implementation priority: high, medium, or low"
    )


class CritiqueAnalysisSimple(BaseModel):
    """Simplified critique analysis schema for Responses API compatibility."""

    quality_score: int = Field(description="Overall quality score (1-10)")
    strengths: str = Field(description="Key strengths identified as text")
    weaknesses: str = Field(description="Areas for improvement as text")
    specific_improvements: str = Field(
        description="Specific improvement suggestions as text"
    )
    overall_assessment: str = Field(description="Overall assessment summary")


class ResponseImprovementSimple(BaseModel):
    """Simplified response improvement schema for Responses API compatibility."""

    improvement_score: int = Field(description="Improvement quality score (1-10)")
    enhanced_content: str = Field(description="Enhanced response content")
    key_additions: str = Field(description="Key additions made as text")
    refinements: str = Field(description="Refinements and improvements as text")
    final_quality: str = Field(description="Final quality assessment")


class GeneralAnalysisSimple(BaseModel):
    """General-purpose simplified analysis schema for any plugin."""

    analysis_type: str = Field(description="Type of analysis performed")
    summary: str = Field(description="Analysis summary")
    key_findings: str = Field(description="Key findings as text")
    recommendations: str = Field(description="Recommendations as text")
    confidence_level: str = Field(description="Confidence level: high, medium, or low")
    additional_notes: str = Field(description="Additional notes or context")


# Schema mapping for plugin types
SIMPLIFIED_SCHEMA_MAP = {
    "budget_manager": BudgetAnalysisSimple,
    "workflow_intelligence": WorkflowOptimizationSimple,
    "ai_reasoning": CritiqueAnalysisSimple,
    "response_improvement": ResponseImprovementSimple,
    "general": GeneralAnalysisSimple,
}


def get_simplified_schema(plugin_type: str) -> type[BaseModel]:
    """Get the appropriate simplified schema for a plugin type."""
    return SIMPLIFIED_SCHEMA_MAP.get(plugin_type, GeneralAnalysisSimple)


def get_simplified_schema_for_operation(operation: str) -> type[BaseModel]:
    """Get simplified schema based on operation name."""
    operation_map = {
        "analyze_decision_costs": BudgetAnalysisSimple,
        "optimize_decision_process": WorkflowOptimizationSimple,
        "critique_response": CritiqueAnalysisSimple,
        "improve_response": ResponseImprovementSimple,
        "analyze_reasoning": CritiqueAnalysisSimple,
        "generate_insights": GeneralAnalysisSimple,
    }
    return operation_map.get(operation, GeneralAnalysisSimple)
