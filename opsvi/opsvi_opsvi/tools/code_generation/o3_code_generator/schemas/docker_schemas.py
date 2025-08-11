"""
Pydantic schemas for Docker orchestrator.

This module defines the input and output schemas for the Docker orchestrator,
ensuring type safety and validation for all data structures.
"""

from typing import Any

from pydantic import BaseModel, Field


class DockerInput(BaseModel):
    """Input schema for Docker configuration generation."""

    app_path: str = Field(..., description="Path to the application to containerize")

    orchestration: str = Field(
        _default="docker-compose",
        _description="Orchestration type (docker-compose, kubernetes, dockerfile)",
    )

    multi_stage: bool = Field(default=False, description="Use multi-stage build")

    security_scanning: bool = Field(
        _default=True, description="Include security scanning configuration"
    )

    resource_limits: bool = Field(default=True, description="Include resource limits")

    health_checks: bool = Field(default=True, description="Include health checks")

    base_image: str = Field(
        _default="python:3.11", description="Base Docker image to use"
    )

    optimization_level: str = Field(
        _default="standard", description="Optimization level for the build"
    )

    model: str = Field(default="o4-mini", description="O4 model to use for generation")

    temperature: float = Field(
        _default=0.1, ge=0.0, le=2.0, description="Temperature for generation"
    )


class DockerOutput(BaseModel):
    """Output schema for Docker configuration generation."""

    docker_config: dict[str, Any] = Field(
        ..., description="Generated Docker configuration"
    )

    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )

    app_info: dict[str, Any] = Field(
        ..., description="Application analysis information"
    )

    generation_time: float = Field(
        ..., description="Time taken for generation in seconds"
    )

    model_used: str = Field(..., description="O3 model used for generation")
