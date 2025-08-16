"""TODO: Add module-level docstring."""

from typing import Any

from pydantic import BaseModel, Field


class RequirementsInput(BaseModel):
    requirements_text: str = Field(
        ..., description="Natural language requirements description"
    )
    analysis_type: str = Field(
        default="comprehensive", description="Type of analysis to perform"
    )
    output_format: str = Field(
        default="markdown", description="Output format for specifications"
    )
    include_user_stories: bool = Field(
        default=True, description="Include user stories in output"
    )
    include_acceptance_criteria: bool = Field(
        default=True, description="Include acceptance criteria in output"
    )
    include_technical_specs: bool = Field(
        default=True, description="Include technical specifications in output"
    )
    model: str = Field(default="o4-mini", description="O4 model to use for analysis")
    max_tokens: int = Field(default=16000, description="Maximum tokens for O3 model")
    temperature: float = Field(default=0.1, description="Temperature for O3 model")


class RequirementsOutput(BaseModel):
    success: bool = Field(..., description="Whether the analysis was successful")
    user_stories: list[dict[str, Any]] = Field(
        default_factory=list, description="Generated user stories"
    )
    dependencies: list[dict[str, Any]] = Field(
        default_factory=list, description="Project dependencies"
    )
    functional_requirements: list[dict[str, Any]] = Field(
        default_factory=list, description="Functional requirements"
    )
    non_functional_requirements: list[dict[str, Any]] = Field(
        default_factory=list, description="Non-functional requirements"
    )
    constraints: list[dict[str, Any]] = Field(
        default_factory=list, description="Project constraints"
    )
    acceptance_criteria: list[dict[str, Any]] = Field(
        default_factory=list, description="Acceptance criteria"
    )
    output_files: list[str] = Field(
        default_factory=list, description="List of generated output file paths"
    )
    generation_time: float = Field(..., description="Time taken to generate analysis")
    model_used: str = Field(..., description="Model used for generation")
    error_message: str | None = Field(
        None, description="Error message if analysis failed"
    )
