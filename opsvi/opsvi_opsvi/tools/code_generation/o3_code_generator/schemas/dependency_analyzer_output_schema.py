"""
Output schema for dependency analysis.

This module defines the Pydantic models for dependency analysis output data.
"""


from typing import Any

from pydantic import Field

from .base_output_schema import BaseGeneratorOutput


class DependencyAnalysisOutput(BaseGeneratorOutput):
    """Output schema for dependency analysis."""

    analysis_results: dict[str, Any] = Field(
        ..., description="Results of the dependency analysis"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for dependency improvements"
    )
    vulnerabilities: list[dict[str, Any]] = Field(
        default_factory=list, description="Identified security vulnerabilities"
    )
    optimization_score: float | None = Field(
        None, description="Overall optimization score (0-100)"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
