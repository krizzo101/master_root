"""
Pydantic schemas for API documentation generator.

This module defines the input and output schemas for the API documentation generator,
ensuring type safety and validation for all data structures.
"""

from typing import Any

from pydantic import BaseModel, Field


class APIDocInput(BaseModel):
    """Input schema for API documentation generation."""

    code_files: list[str] = Field(
        ..., description="List of code files to analyze for API documentation"
    )

    output_format: str = Field(
        _default="openapi",
        _description="Output format for documentation (openapi, markdown, html)",
    )

    model: str = Field(default="o3-mini", description="O3 model to use for generation")

    language: str = Field(default="python", description="Language for code examples")

    framework: str = Field(default="", description="Framework used in the code")

    include_examples: bool = Field(
        _default=True, description="Include code examples in documentation"
    )

    include_authentication: bool = Field(
        _default=True, description="Include authentication documentation"
    )

    include_error_handling: bool = Field(
        _default=True, description="Include error handling documentation"
    )

    temperature: float = Field(
        _default=0.1, ge=0.0, le=2.0, description="Temperature for generation"
    )


class APIDocOutput(BaseModel):
    """Output schema for API documentation generation."""

    documentation: dict[str, Any] = Field(
        ..., description="Generated documentation content"
    )

    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )

    examples: dict[str, str] = Field(
        _default_factory=dict, description="Generated code examples by name"
    )

    api_info: dict[str, Any] = Field(
        ..., description="Extracted API information from code analysis"
    )

    generation_time: float = Field(
        ..., description="Time taken for generation in seconds"
    )

    model_used: str = Field(..., description="O3 model used for generation")
