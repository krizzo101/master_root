"""
Output schema for Performance Optimizer.

This module defines the Pydantic schema for performance optimizer output results.
"""

from typing import Any

from pydantic import BaseModel, Field


class PerformanceOptimizerOutput(BaseModel):
    """Output schema for Performance Optimizer."""

    project_name: str = Field(..., description="Name of the project")

    # Analysis results
    code_analysis: dict[str, Any] = Field(
        ..., description="Code performance analysis results"
    )
    profiling_results: dict[str, Any] = Field(..., description="Code profiling results")

    # Optimization results
    optimization_recommendations: dict[str, Any] = Field(
        ..., description="Optimization recommendations"
    )

    # Assessment
    optimization_score: int = Field(..., description="Optimization score (0-100)")

    # Status
    success: bool = Field(..., description="Whether the optimization was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    optimization_time: float | None = Field(
        _default=None, description="Time taken for optimization (seconds)"
    )
    files_analyzed: int | None = Field(
        _default=None, description="Number of files analyzed"
    )
    model_used: str = Field(default="o3-mini", description="AI model used for analysis")

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
