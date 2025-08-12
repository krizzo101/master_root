"""
Input schema for O3 Code Generator.

This module defines the structured input schema for code generation requests,
ensuring consistent and validated input data.
"""

from typing import Any

from pydantic import BaseModel, Field


class CodeGenerationInput(BaseModel):
    """
    Structured input schema for code generation requests.

    This schema defines all the parameters that can be passed to the O3 code generator,
    ensuring type safety and validation of input data.
    """

    prompt: str = Field(..., description="Main prompt describing what code to generate")
    model: str = Field(
        "o4-mini", description="Model to use for generation (o3 or o4-mini)"
    )
    file_name: str | None = Field(
        None, description="Target file name for generated code"
    )
    file_path: str | None = Field(None, description="Target file path (directory)")
    language: str = Field(
        "python", description="Programming language for generated code"
    )
    context_files: list[str] | None = Field(
        None, description="List of context file paths"
    )
    variables: dict[str, Any] | None = Field(
        None, description="Variables for prompt substitution"
    )
    requirements: list[str] | None = Field(
        None, description="Additional requirements/dependencies"
    )
    style_guide: str | None = Field(
        None, description="Code style and formatting requirements"
    )
    additional_context: str | None = Field(
        None, description="Additional context or constraints"
    )
