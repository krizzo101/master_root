"""
Output schema for CI/CD Pipeline Generator.

This module defines the Pydantic schema for CI/CD pipeline generator output results.
"""

from typing import Any

from pydantic import BaseModel, Field


class CICDPipelineGeneratorOutput(BaseModel):
    """Output schema for CI/CD Pipeline Generator."""

    project_name: str = Field(..., description="Name of the project")

    # Analysis results
    project_analysis: dict[str, Any] = Field(
        ..., description="Project analysis results"
    )

    # Generated pipelines
    generated_pipelines: dict[str, str] = Field(
        ..., description="Generated pipeline configurations"
    )

    # Output files
    output_files: list[str] = Field(
        _default_factory=list, description="Paths to generated files"
    )

    # Status
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    generation_time: float | None = Field(
        _default=None, description="Time taken for generation (seconds)"
    )
    platforms_generated: int | None = Field(
        _default=None, description="Number of platforms generated"
    )
    model_used: str = Field(
        _default="o3-mini", description="AI model used for generation"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
