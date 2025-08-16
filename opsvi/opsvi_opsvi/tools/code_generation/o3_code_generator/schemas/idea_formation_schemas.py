"""
Idea Formation Schemas for O3 Code Generator

This module defines the structured input and output schemas for idea formation
and concept development tools, ensuring consistent and validated data handling.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Types of analysis available for idea formation."""

    SIMPLE = "simple"
    COMPREHENSIVE = "comprehensive"
    MARKET_FOCUSED = "market_focused"
    TECHNICAL_FOCUSED = "technical_focused"


class IdeaFormationOutputFormat(str, Enum):
    """Available output formats for idea formation tools."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class ImpactLevel(str, Enum):
    """Impact levels for ideas and concepts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FeasibilityLevel(str, Enum):
    """Feasibility assessment levels."""

    HIGHLY_FEASIBLE = "highly_feasible"
    FEASIBLE = "feasible"
    MODERATELY_FEASIBLE = "moderately_feasible"
    CHALLENGING = "challenging"
    NOT_FEASIBLE = "not_feasible"


class IdeaFormationInput(BaseModel):
    """Structured input schema for idea formation analysis."""

    concept_description: str = Field(
        ..., description="Natural language description of the concept or idea"
    )
    target_market: str | None = Field(
        None, description="Target market or audience for the concept"
    )
    analysis_type: AnalysisType = Field(
        default=AnalysisType.COMPREHENSIVE, description="Type of analysis to perform"
    )
    include_market_research: bool = Field(
        default=True, description="Whether to include market research analysis"
    )
    include_feasibility_assessment: bool = Field(
        default=True, description="Whether to include feasibility assessment"
    )
    output_format: IdeaFormationOutputFormat = Field(
        default=IdeaFormationOutputFormat.JSON, description="Output format for results"
    )
    model: str = Field(default="o3-mini", description="O3 model to use for analysis")
    max_tokens: int = Field(
        default=4000, description="Maximum tokens for O3 model response"
    )
    additional_context: str | None = Field(
        None, description="Additional context or constraints for analysis"
    )


class IdeaFormationOutput(BaseModel):
    """Structured output schema for idea formation analysis."""

    success: bool = Field(..., description="Whether the analysis was successful")
    idea_analysis: dict[str, Any] = Field(
        ..., description="Comprehensive analysis results"
    )
    output_files: list[str] = Field(
        default_factory=list, description="Paths to generated output files"
    )
    generation_time: float = Field(
        ..., description="Time taken for analysis in seconds"
    )
    model_used: str = Field(..., description="O3 model used for analysis")
    error_message: str | None = Field(
        None, description="Error message if analysis failed"
    )


class BrainstormingInput(BaseModel):
    """Structured input schema for brainstorming sessions."""

    problem_statement: str = Field(
        ..., description="Problem statement or domain description"
    )
    target_audience: str | None = Field(
        None, description="Target audience for the brainstorming session"
    )
    idea_count: int = Field(default=10, description="Number of ideas to generate")
    categories: list[str] | None = Field(
        None, description="Specific categories to focus on"
    )
    include_prioritization: bool = Field(
        default=True, description="Whether to prioritize generated ideas"
    )
    output_format: IdeaFormationOutputFormat = Field(
        default=IdeaFormationOutputFormat.JSON, description="Output format for results"
    )
    model: str = Field(default="gpt-4.1", description="Model to use for brainstorming")
    max_tokens: int = Field(
        default=16000, description="Maximum tokens for model response"
    )
    conversation_history: list[dict[str, str]] | None = Field(
        None, description="Conversation history for context"
    )
    conversation_insights: dict[str, Any] | None = Field(
        None, description="Extracted insights from conversation"
    )
    session_type: str | None = Field(None, description="Type of brainstorming session")


class BrainstormingOutput(BaseModel):
    """Structured output schema for brainstorming sessions."""

    success: bool = Field(..., description="Whether brainstorming was successful")
    ideas: list[dict[str, Any]] = Field(
        ..., description="Generated ideas with metadata"
    )
    categories: list[str] = Field(
        ..., description="Categories used for idea organization"
    )
    prioritized_ideas: list[dict[str, Any]] = Field(
        default_factory=list, description="Ideas sorted by priority"
    )
    output_files: list[str] = Field(
        default_factory=list, description="Paths to generated output files"
    )
    generation_time: float = Field(
        ..., description="Time taken for brainstorming in seconds"
    )
    model_used: str = Field(..., description="O3 model used for brainstorming")
    error_message: str | None = Field(
        None, description="Error message if brainstorming failed"
    )


class MarketResearchInput(BaseModel):
    """Structured input schema for market research analysis."""

    product_concept: str = Field(
        ..., description="Product or service concept to analyze"
    )
    target_market: str = Field(..., description="Target market for the product")
    include_competitor_analysis: bool = Field(
        default=True, description="Whether to include competitor analysis"
    )
    include_demand_assessment: bool = Field(
        default=True, description="Whether to include demand assessment"
    )
    include_market_fit_validation: bool = Field(
        default=True, description="Whether to include market fit validation"
    )
    output_format: IdeaFormationOutputFormat = Field(
        default=IdeaFormationOutputFormat.JSON, description="Output format for results"
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for market research"
    )
    max_tokens: int = Field(
        default=4000, description="Maximum tokens for O3 model response"
    )


class MarketResearchOutput(BaseModel):
    """Structured output schema for market research analysis."""

    success: bool = Field(..., description="Whether market research was successful")
    market_analysis: dict[str, Any] = Field(
        ..., description="Comprehensive market analysis results"
    )
    competitors: list[dict[str, Any]] = Field(
        default_factory=list, description="Competitor analysis results"
    )
    demand_assessment: dict[str, Any] = Field(
        ..., description="Demand assessment results"
    )
    market_fit_validation: dict[str, Any] = Field(
        ..., description="Market fit validation results"
    )
    output_files: list[str] = Field(
        default_factory=list, description="Paths to generated output files"
    )
    generation_time: float = Field(
        ..., description="Time taken for market research in seconds"
    )
    model_used: str = Field(..., description="O3 model used for market research")
    error_message: str | None = Field(
        None, description="Error message if market research failed"
    )


class FeasibilityInput(BaseModel):
    """Structured input schema for feasibility assessment."""

    concept_description: str = Field(
        ..., description="Detailed description of the concept to assess"
    )
    include_technical_feasibility: bool = Field(
        default=True, description="Whether to assess technical feasibility"
    )
    include_economic_feasibility: bool = Field(
        default=True, description="Whether to assess economic feasibility"
    )
    include_operational_feasibility: bool = Field(
        default=True, description="Whether to assess operational feasibility"
    )
    budget_constraints: str | None = Field(
        None, description="Budget constraints for the project"
    )
    timeline_constraints: str | None = Field(
        None, description="Timeline constraints for the project"
    )
    output_format: IdeaFormationOutputFormat = Field(
        default=IdeaFormationOutputFormat.JSON, description="Output format for results"
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for feasibility assessment"
    )
    max_tokens: int = Field(
        default=4000, description="Maximum tokens for O3 model response"
    )


class FeasibilityOutput(BaseModel):
    """Structured output schema for feasibility assessment."""

    success: bool = Field(
        ..., description="Whether feasibility assessment was successful"
    )
    technical_feasibility: dict[str, Any] = Field(
        ..., description="Technical feasibility assessment results"
    )
    economic_feasibility: dict[str, Any] = Field(
        ..., description="Economic feasibility assessment results"
    )
    operational_feasibility: dict[str, Any] = Field(
        ..., description="Operational feasibility assessment results"
    )
    overall_feasibility: FeasibilityLevel = Field(
        ..., description="Overall feasibility assessment"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations based on assessment"
    )
    risks: list[dict[str, Any]] = Field(
        default_factory=list, description="Identified risks and mitigation strategies"
    )
    output_files: list[str] = Field(
        default_factory=list, description="Paths to generated output files"
    )
    generation_time: float = Field(
        ..., description="Time taken for feasibility assessment in seconds"
    )
    model_used: str = Field(..., description="O3 model used for feasibility assessment")
    error_message: str | None = Field(
        None, description="Error message if feasibility assessment failed"
    )
