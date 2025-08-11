"""
Output schema for API documentation generation.

This module defines the Pydantic models for API documentation generation output data.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ApiDocGeneratorOutput(BaseModel):
    """Output schema for API documentation generation."""

    success: bool = Field(
        ..., description="Whether the API documentation generation was successful"
    )

    project_path: str = Field(..., description="Path to the analyzed project")

    api_info: dict = Field(
        _default_factory=dict,
        _description="Parsed API information including endpoints, models, and functions",
    )

    openapi_spec: dict = Field(
        _default_factory=dict, description="Generated OpenAPI/Swagger specification"
    )

    documentation: dict = Field(
        _default_factory=dict, description="Generated comprehensive documentation"
    )

    output_files: list[str] = Field(
        _default_factory=list, description="List of generated output files"
    )

    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
