"""
Output schema for Testing Framework Generator.

This module defines the Pydantic schema for testing framework generator output results.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TestingFrameworkGeneratorOutput(BaseModel):
    """Output schema for Testing Framework Generator."""

    project_name: str = Field(..., description="Name of the project")

    # Analysis results
    project_analysis: dict[str, Any] = Field(
        ..., description="Project analysis results"
    )

    # Generated content
    generated_tests: dict[str, str] = Field(..., description="Generated test files")
    framework_configurations: dict[str, str] = Field(
        ..., description="Framework configuration files"
    )

    # Output files
    output_files: list[str] = Field(
        _default_factory=list, description="Paths to generated files"
    )

    # Status
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    generation_time: Optional[float] = Field(
        _default=None, description="Time taken for generation (seconds)"
    )
    tests_generated: Optional[int] = Field(
        _default=None, description="Number of test files generated"
    )
    model_used: str = Field(
        _default="o3-mini", description="AI model used for generation"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
