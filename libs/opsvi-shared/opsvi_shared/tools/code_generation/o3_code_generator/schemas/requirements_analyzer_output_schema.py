"""
Output schema for Requirements Analyzer.

This module defines the Pydantic schema for requirements analyzer output results.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class OptimizationRecommendation(BaseModel):
    """Optimization recommendation."""

    category: str = Field(..., description="Recommendation category")
    priority: str = Field(..., description="Priority level: high, medium, low")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action: str = Field(..., description="Recommended action")


class RequirementsAnalyzerOutput(BaseModel):
    """Output schema for Requirements Analyzer."""

    project_name: str = Field(..., description="Name of the project")

    # Analysis results
    dependency_analysis: dict[str, Any] = Field(
        ..., description="Dependency analysis results"
    )
    optimization_recommendations: dict[str, Any] = Field(
        ..., description="AI-generated optimization recommendations"
    )

    # Recommendations
    recommendations: list[OptimizationRecommendation] = Field(
        ..., description="Actionable recommendations"
    )

    # Optimization assessment
    optimization_score: int = Field(..., description="Optimization score (0-100)")

    # Status
    success: bool = Field(..., description="Whether the analysis was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    analysis_time: Optional[float] = Field(
        _default=None, description="Time taken for analysis (seconds)"
    )
    dependencies_analyzed: Optional[int] = Field(
        _default=None, description="Number of dependencies analyzed"
    )
    model_used: str = Field(
        _default="o3-mini", description="AI model used for optimization"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
