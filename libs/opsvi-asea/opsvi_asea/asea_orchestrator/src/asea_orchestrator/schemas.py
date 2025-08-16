"""
Pydantic schemas for structured outputs in ASEA orchestrator plugins.
These schemas ensure type safety and validation for AI model responses.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Budget Manager Plugin Schemas
class BudgetStatus(BaseModel):
    """Budget status information"""

    can_proceed: bool = Field(
        description="Whether the operation can proceed within budget"
    )
    remaining_budget: float = Field(description="Remaining budget amount in USD")
    estimated_cost: float = Field(description="Estimated cost for the operation")
    current_usage: float = Field(description="Current usage amount")
    limit: float = Field(description="Budget limit amount")
    utilization_percent: float = Field(description="Budget utilization percentage")


class OptionAnalysis(BaseModel):
    """Analysis of a single decision option"""

    description: str = Field(description="Description of the decision option")
    estimated_cost: float = Field(description="Estimated cost in USD")
    budget_impact: str = Field(description="Budget impact level (high/medium/low)")
    recommendation: str = Field(description="Recommendation for this option")


class BudgetAnalysisResponse(BaseModel):
    """Complete budget analysis response"""

    budget_status: BudgetStatus = Field(description="Current budget status")
    decision_cost_analysis: Dict[str, OptionAnalysis] = Field(
        description="Analysis of individual decision options", default_factory=dict
    )
    decision_viability: str = Field(
        description="Overall decision viability (approved/budget_constrained)"
    )
    recommendations: List[str] = Field(
        description="List of budget-related recommendations"
    )


# Workflow Intelligence Plugin Schemas
class ComplexityFactors(BaseModel):
    """Factors contributing to decision complexity"""

    option_count: int = Field(description="Number of decision options")
    constraint_count: int = Field(description="Number of constraints")
    budget_complexity: str = Field(
        description="Budget complexity level (high/medium/low)"
    )


class DecisionComplexity(BaseModel):
    """Decision complexity analysis"""

    level: str = Field(description="Complexity level (high/medium/low)")
    score: float = Field(description="Numerical complexity score")
    factors: ComplexityFactors = Field(description="Factors contributing to complexity")


class ConstraintHandling(BaseModel):
    """Constraint handling analysis"""

    description: str = Field(description="Description of the constraint")
    type: str = Field(
        description="Type of constraint (financial/temporal/resource/unknown)"
    )
    optimization_approach: str = Field(description="Recommended optimization approach")


class OptionPatterns(BaseModel):
    """Patterns found in decision options"""

    has_cost_tradeoffs: bool = Field(description="Whether options have cost tradeoffs")
    has_time_tradeoffs: bool = Field(description="Whether options have time tradeoffs")
    has_quality_tradeoffs: bool = Field(
        description="Whether options have quality tradeoffs"
    )
    option_diversity: str = Field(
        description="Diversity level of options (high/medium/low)"
    )


class HistoricalInsights(BaseModel):
    """Historical insights for similar decisions"""

    similar_decision_count: int = Field(description="Number of similar decisions found")
    success_rate: float = Field(description="Success rate of similar decisions")
    common_pitfalls: List[str] = Field(description="Common pitfalls to avoid")
    best_practices: List[str] = Field(description="Recommended best practices")


class ProcessOptimization(BaseModel):
    """Process optimization details"""

    constraint_handling: Optional[Dict[str, ConstraintHandling]] = Field(
        description="Constraint handling strategies", default=None
    )
    option_analysis: Optional[OptionPatterns] = Field(
        description="Option pattern analysis", default=None
    )
    historical_insights: Optional[HistoricalInsights] = Field(
        description="Historical insights for optimization", default=None
    )


class WorkflowOptimizationResponse(BaseModel):
    """Complete workflow optimization response"""

    decision_complexity: DecisionComplexity = Field(
        description="Decision complexity analysis"
    )
    process_optimization: ProcessOptimization = Field(
        description="Process optimization recommendations"
    )
    recommendations: List[str] = Field(
        description="List of optimization recommendations"
    )


# AI Reasoning Plugin Schemas
class ReasoningStep(BaseModel):
    """Individual reasoning step"""

    step_number: int = Field(description="Step number in reasoning process")
    description: str = Field(description="Description of the reasoning step")
    conclusion: str = Field(description="Conclusion reached in this step")
    confidence: float = Field(description="Confidence level (0.0 to 1.0)")


class ReasoningAnalysis(BaseModel):
    """AI reasoning analysis result"""

    reasoning_steps: List[ReasoningStep] = Field(description="List of reasoning steps")
    final_conclusion: str = Field(description="Final conclusion from reasoning")
    overall_confidence: float = Field(description="Overall confidence in reasoning")
    key_insights: List[str] = Field(description="Key insights discovered")
    assumptions: List[str] = Field(description="Assumptions made during reasoning")
    recommendations: List[str] = Field(description="Recommendations based on reasoning")


# Generic Plugin Response Schema
class PluginResponse(BaseModel):
    """Generic plugin response schema"""

    success: bool = Field(description="Whether the plugin execution was successful")
    data: Dict[str, Any] = Field(description="Plugin-specific response data")
    error_message: Optional[str] = Field(
        description="Error message if execution failed", default=None
    )
    execution_time: Optional[float] = Field(
        description="Execution time in seconds", default=None
    )
    metadata: Optional[Dict[str, Any]] = Field(
        description="Additional metadata", default=None
    )


# Workflow State Schema
class WorkflowStateResponse(BaseModel):
    """Workflow state response schema"""

    run_id: str = Field(description="Unique workflow run identifier")
    workflow_name: str = Field(description="Name of the workflow")
    status: str = Field(description="Current workflow status")
    current_step: int = Field(description="Current step number")
    total_steps: int = Field(description="Total number of steps")
    state: Dict[str, Any] = Field(description="Current workflow state data")
    execution_time: Optional[float] = Field(
        description="Total execution time", default=None
    )
    success_rate: Optional[float] = Field(
        description="Success rate of completed steps", default=None
    )


# Cognitive Enhancement Schemas
class CognitiveEnhancementRequest(BaseModel):
    """Request schema for cognitive enhancement"""

    prompt: str = Field(description="User prompt to be enhanced")
    context: Optional[Dict[str, Any]] = Field(
        description="Additional context", default=None
    )
    enhancement_level: str = Field(
        description="Enhancement level (basic/standard/advanced)", default="standard"
    )
    budget_limit: Optional[float] = Field(
        description="Budget limit in USD", default=None
    )


class CognitiveEnhancementResponse(BaseModel):
    """Response schema for cognitive enhancement"""

    enhanced_response: str = Field(description="Enhanced response to the user prompt")
    enhancement_summary: Dict[str, Any] = Field(
        description="Summary of enhancements applied"
    )
    quality_score: float = Field(
        description="Quality score of the enhanced response (0.0 to 10.0)"
    )
    cost_analysis: Optional[BudgetAnalysisResponse] = Field(
        description="Cost analysis", default=None
    )
    workflow_optimization: Optional[WorkflowOptimizationResponse] = Field(
        description="Workflow optimization", default=None
    )
    processing_time: float = Field(description="Total processing time in seconds")
    model_usage: Dict[str, Dict[str, Any]] = Field(description="Model usage statistics")


# Schema registry for dynamic lookup
PLUGIN_SCHEMAS = {
    "budget_manager": {
        "analyze_decision_costs": BudgetAnalysisResponse,
        "check_budget": BudgetStatus,
        "default": PluginResponse,
    },
    "workflow_intelligence": {
        "optimize_decision_process": WorkflowOptimizationResponse,
        "analyze_workflow": PluginResponse,
        "default": PluginResponse,
    },
    "ai_reasoning": {"analyze": ReasoningAnalysis, "default": PluginResponse},
    "cognitive_enhancement": {
        "enhance": CognitiveEnhancementResponse,
        "default": PluginResponse,
    },
}


def get_schema_for_plugin(plugin_name: str, operation: str = "default") -> BaseModel:
    """
    Get the appropriate Pydantic schema for a plugin operation.

    Args:
        plugin_name: Name of the plugin
        operation: Specific operation being performed

    Returns:
        Appropriate Pydantic schema class
    """
    plugin_schemas = PLUGIN_SCHEMAS.get(plugin_name, {})
    return plugin_schemas.get(operation, plugin_schemas.get("default", PluginResponse))


def get_json_schema_for_plugin(
    plugin_name: str, operation: str = "default"
) -> Dict[str, Any]:
    """
    Get the JSON schema for a plugin operation.

    Args:
        plugin_name: Name of the plugin
        operation: Specific operation being performed

    Returns:
        JSON schema dictionary
    """
    schema_class = get_schema_for_plugin(plugin_name, operation)
    return schema_class.model_json_schema()
