"""
Output schema for Docker Orchestrator.

This module defines the Pydantic schema for Docker orchestrator output results.
"""

from typing import Any

from pydantic import BaseModel, Field


class DockerOrchestratorOutput(BaseModel):
    """Output schema for Docker Orchestrator."""

    project_name: str = Field(..., description="Name of the project")
    project_analysis: dict[str, Any] = Field(
        ..., description="Project analysis results"
    )

    # Generated configurations
    dockerfile_content: str = Field(..., description="Generated Dockerfile content")
    docker_compose_content: str = Field(
        ..., description="Generated docker-compose.yml content"
    )
    kubernetes_manifests: dict[str, str] = Field(
        ..., description="Generated Kubernetes manifests"
    )

    # Output files
    output_files: list[str] = Field(
        _default_factory=list, description="Paths to generated files"
    )

    # Status
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    generation_time: float | None = Field(
        _default=None, description="Time taken for generation (seconds)"
    )
    model_used: str = Field(
        _default="o3-mini", description="AI model used for generation"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
