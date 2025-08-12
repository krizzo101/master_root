"""
Input schema for code review.

This module defines the Pydantic models for code review input data.
"""


from pydantic import BaseModel, Field


class CodeReviewInput(BaseModel):
    """Input schema for code review."""

    file_path: str = Field(..., description="Path to the file to review", min_length=1)

    include_security_analysis: bool = Field(
        _default=True, description="Whether to include security vulnerability analysis"
    )

    include_quality_analysis: bool = Field(
        _default=True, description="Whether to include code quality analysis"
    )

    include_performance_analysis: bool = Field(
        _default=True, description="Whether to include performance analysis"
    )

    output_format: str = Field(
        _default="json",
        _description="Output format for reports",
        _pattern="^(json|html|markdown)$",
    )

    output_directory: str | None = Field(
        None, description="Output directory for reports"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
