"""
Shared pydantic models for agent hand-offs.

Updated for OpenAI Structured Outputs compatibility (July 2025).
Removed default values that aren't supported by OpenAI's structured outputs.
"""

from __future__ import annotations

from pathlib import Path

# Import ProjectType from project_templates
from project_templates import ProjectType
from pydantic import BaseModel, Field

# Re-export for convenience
__all__ = ["ProjectType", "RequirementsSpec", "ArchitectureSpec", "ResearchTopics"]

# Functional specifications ----------------------------------------------------


class RequirementsSpec(BaseModel):
    """Structured requirements extracted from the user request."""

    title: str = Field(..., description="Project title")
    original_request: str = Field(..., description="Raw text provided by user.")
    description: str = Field(..., description="Project description")
    functional_requirements: list[str] = Field(
        ..., description="List of functional requirements."
    )
    non_functional_requirements: list[str] = Field(
        ..., description="List of non-functional requirements."
    )
    technologies: list[str] = Field(
        ..., description="Preferred technologies mentioned by user."
    )
    constraints: list[str] = Field(
        ..., description="Limitations or special requirements."
    )


class ArchitectureComponent(BaseModel):
    """Individual component in the architecture."""

    name: str = Field(..., description="Component name")
    responsibility: str = Field(..., description="What this component does")
    technologies: list[str] = Field(
        ..., description="Technologies used by this component"
    )


class ArchitectureSpec(BaseModel):
    """High-level architecture artifacts produced by ArchitectureAgent."""

    components: list[ArchitectureComponent] = Field(
        ...,
        description="List of system components",
    )
    technology_stack: list[str] = Field(
        ...,
        description="Overall technology stack as a simple list",
    )
    deployment_strategy: str = Field(
        ...,
        description="How to deploy the application",
    )
    design_decisions: list[str] = Field(
        ...,
        description="Key architectural decisions",
    )

    # Legacy fields for backward compatibility (made optional)
    adr_paths: list[str] | None = Field(
        None, description="Paths to Architecture Decision Records (as strings)"
    )
    diagrams: list[str] | None = Field(
        None, description="Paths to architecture diagrams (as strings)"
    )
    openapi_spec: str | None = Field(
        None, description="Path to generated OpenAPI YAML file (as string)."
    )


class CodeBundle(BaseModel):
    """Container for generated code and documentation directories."""

    src_dir: Path = Field(..., description="Source directory path")
    tests_dir: Path = Field(..., description="Tests directory path")
    docs_dir: Path = Field(..., description="Documentation directory path")


class TestReport(BaseModel):
    """Summarised test execution results."""

    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    coverage: float = Field(..., ge=0.0, le=1.0, description="Test coverage percentage")
    mutation_score: float | None = Field(
        None, ge=0.0, le=1.0, description="Mutation testing score"
    )


class DocSet(BaseModel):
    """Documentation artifacts."""

    docs_dir: str = Field(..., description="Documentation directory path")
    index_file: str | None = Field(
        None, description="Path to main documentation index file"
    )


# Helper models for AI agents -------------------------------------------------


class ProjectTypeDetection(BaseModel):
    """Response model for project type detection by AI."""

    project_type: str = Field(
        ...,
        description="Detected project type (e.g., 'cli_tool', 'web_api', 'simple_script')",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level in the detection (0.0 to 1.0)",
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why this project type was chosen"
    )


class SecurityAnalysis(BaseModel):
    """Response model for security analysis by AI."""

    risk_level: str = Field(
        ..., description="Overall risk level: 'low', 'medium', 'high'"
    )
    concerns: list[str] = Field(
        ..., description="List of specific security concerns identified"
    )
    recommendations: list[str] = Field(
        ..., description="List of security recommendations"
    )
    is_safe: bool = Field(
        ..., description="Whether the request is considered safe to proceed with"
    )


class ResearchTopics(BaseModel):
    """Technologies and topics identified for research."""

    primary_technologies: list[str] = Field(
        ...,
        description="Core technologies, frameworks, and libraries mentioned or implied",
    )
    secondary_topics: list[str] = Field(
        ..., description="Related concepts, patterns, or best practices to research"
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why these topics were selected"
    )


__all__ = [
    "RequirementsSpec",
    "ArchitectureSpec",
    "ArchitectureComponent",
    "CodeBundle",
    "TestReport",
    "DocSet",
    "ProjectTypeDetection",
    "SecurityAnalysis",
    "ResearchTopics",
]
