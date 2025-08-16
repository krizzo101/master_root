"""
Output Schema for O3 Code Generator

This module defines the Pydantic models for code generation output validation.
"""

from pydantic import BaseModel, Field


class CodeGenerationOutput(BaseModel):
    """
    Output schema for code generation responses.

    All fields are required by OpenAI's structured output API to ensure
    the AI model provides complete, consistent responses every time.
    No fallbacks needed - the system works correctly on first attempt.
    """

    code: str = Field(..., description="The generated code content")
    file_name: str = Field(..., description="The target file name")
    file_path: str = Field(..., description="The target file path")
    language: str = Field(..., description="Programming language")
    explanation: str = Field(..., description="Explanation of the generated code")
    issues: list[str] = Field(
        ...,
        description="List of issues, questions, or uncertainties reported by the model",
    )
    prompt_feedback: str = Field(
        ..., description="Model suggestions for improving the prompt or output schema"
    )
    success: bool = Field(..., description="Whether generation was successful")
    error_message: str = Field(..., description="Error message if generation failed")
