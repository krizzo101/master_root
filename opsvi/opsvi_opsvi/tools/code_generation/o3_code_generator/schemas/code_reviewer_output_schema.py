"""
Output schema for code review.

This module defines the Pydantic models for code review output data.
"""


from pydantic import BaseModel, Field


class CodeReviewOutput(BaseModel):
    """Output schema for code review."""

    success: bool = Field(..., description="Whether the code review was successful")

    file_path: str = Field(..., description="Path to the reviewed file")

    security_issues: list = Field(
        _default_factory=list, description="List of security vulnerabilities found"
    )

    quality_analysis: dict = Field(
        _default_factory=dict, description="Code quality analysis results"
    )

    performance_issues: list = Field(
        _default_factory=list, description="List of performance issues found"
    )

    review_summary: dict = Field(
        _default_factory=dict, description="Summary of the code review"
    )

    report_path: str = Field(..., description="Path to the generated review report")

    error_message: str | None = Field(
        None, description="Error message if review failed"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
