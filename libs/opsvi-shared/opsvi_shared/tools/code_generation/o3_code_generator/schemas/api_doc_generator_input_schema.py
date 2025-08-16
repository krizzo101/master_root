"""
Input schema for API documentation generation.

This module defines the Pydantic models for API documentation generation input data.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ApiDocGeneratorInput(BaseModel):
    """Input schema for API documentation generation."""

    project_path: str = Field(
        ..., description="Path to the project directory to analyze", min_length=1
    )

    output_format: str = Field(
        default="all",
        description="Output format for documentation",
        pattern="^(json|html|markdown|all)$",
    )

    include_examples: bool = Field(
        default=True, description="Whether to include code examples in documentation"
    )

    include_schemas: bool = Field(
        default=True, description="Whether to include request/response schemas"
    )

    generate_openapi: bool = Field(
        default=True, description="Whether to generate OpenAPI/Swagger specification"
    )

    generate_client_sdks: bool = Field(
        default=False, description="Whether to generate client SDKs"
    )

    output_directory: Optional[str] = Field(
        None, description="Custom output directory for generated files"
    )

    framework_detection: bool = Field(
        default=True, description="Whether to automatically detect the web framework"
    )

    include_authentication: bool = Field(
        default=True, description="Whether to include authentication documentation"
    )

    include_error_handling: bool = Field(
        default=True, description="Whether to include error handling documentation"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
