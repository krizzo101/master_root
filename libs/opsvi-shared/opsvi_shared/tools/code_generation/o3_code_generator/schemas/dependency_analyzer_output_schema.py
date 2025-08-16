"""
Output schema for dependency analysis.

This module defines the Pydantic models for dependency analysis output data.
"""

from typing import Optional

from pydantic import Field
from typing import Dict, Any, List
from .base_output_schema import BaseGeneratorOutput


class DependencyAnalysisOutput(BaseGeneratorOutput):
    """Output schema for dependency analysis."""

    analysis_results: Dict[str, Any] = Field(
        ..., description="Results of the dependency analysis"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations for dependency improvements"
    )
    vulnerabilities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Identified security vulnerabilities"
    )
    optimization_score: Optional[float] = Field(
        None, description="Overall optimization score (0-100)"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
