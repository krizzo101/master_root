"""
Input schema for dependency analysis.

This module defines the Pydantic models for dependency analysis input data.
"""

from typing import Optional

from pydantic import BaseModel, Field


class DependencyAnalysisInput(BaseModel):
    """Input schema for dependency analysis."""

    paths: list[str] = Field(
        ..., description="List of project root paths to analyze", min_items=1
    )

    output_format: str = Field(
        _default="json",
        _description="Output format for reports",
        _pattern="^(json|html|markdown)$",
    )

    output_directory: Optional[str] = Field(
        None, description="Output directory for reports"
    )

    include_dev_dependencies: bool = Field(
        _default=True,
        _description="Whether to include development dependencies in analysis",
    )

    scan_vulnerabilities: bool = Field(
        _default=True, description="Whether to scan for security vulnerabilities"
    )

    optimize_dependencies: bool = Field(
        _default=True, description="Whether to provide optimization recommendations"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
