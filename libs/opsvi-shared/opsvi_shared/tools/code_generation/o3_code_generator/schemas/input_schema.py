"""
Input schema for O3 Code Generator.

This module defines the structured input schema for code generation requests,
ensuring consistent and validated input data.
"""

from typing import Any, Optional

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
    file_name: Optional[str] = Field(
        None, description="Target file name for generated code"
    )
    file_path: Optional[str] = Field(None, description="Target file path (directory)")
    language: str = Field(
        "python", description="Programming language for generated code"
    )
    context_files: Optional[list[str]] = Field(
        None, description="List of context file paths"
    )
    variables: Optional[dict[str, Any]] = Field(
        None, description="Variables for prompt substitution"
    )
    requirements: Optional[list[str]] = Field(
        None, description="Additional requirements/dependencies"
    )
    style_guide: Optional[str] = Field(
        None, description="Code style and formatting requirements"
    )
    additional_context: Optional[str] = Field(
        None, description="Additional context or constraints"
    )
