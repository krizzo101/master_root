"""
Input schema for Docker Orchestrator.

This module defines the Pydantic schema for Docker orchestrator input configuration.
"""

from typing import Optional

from pydantic import BaseModel, Field


class DockerConfig(BaseModel):
    """Configuration for Docker-specific settings."""

    base_image: str = Field(default="python:3.11-slim", description="Base Docker image")
    multi_stage: bool = Field(default=True, description="Use multi-stage build")
    optimize_layers: bool = Field(default=True, description="Optimize Docker layers")
    security_scan: bool = Field(default=True, description="Include security scanning")
    health_check: bool = Field(default=True, description="Include health checks")
    non_root_user: bool = Field(default=True, description="Use non-root user")
    labels: dict[str, str] = Field(default_factory=dict, description="Docker labels")


class KubernetesConfig(BaseModel):
    """Configuration for Kubernetes-specific settings."""

    namespace: str = Field(default="default", description="Kubernetes namespace")
    replicas: int = Field(default=3, description="Number of replicas")
    include_ingress: bool = Field(
        default=False, description="Include ingress configuration"
    )
    domain: Optional[str] = Field(default=None, description="Domain for ingress")
    resource_limits: dict[str, str] = Field(
        default={"memory": "512Mi", "cpu": "500m"}, description="Resource limits"
    )
    resource_requests: dict[str, str] = Field(
        default={"memory": "256Mi", "cpu": "250m"}, description="Resource requests"
    )
    storage_class: Optional[str] = Field(
        default=None, description="Storage class for volumes"
    )


class DockerOrchestratorInput(BaseModel):
    """Input schema for Docker Orchestrator."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")

    # Configuration options
    docker_config: DockerConfig = Field(
        default_factory=DockerConfig, description="Docker configuration"
    )
    kubernetes_config: KubernetesConfig = Field(
        default_factory=KubernetesConfig, description="Kubernetes configuration"
    )

    # Output options
    write_files: bool = Field(
        default=True, description="Write configuration files to project directory"
    )
    output_file: Optional[str] = Field(
        default=None, description="Output file for results"
    )

    # Additional options
    include_monitoring: bool = Field(
        default=False, description="Include monitoring configuration"
    )
    include_logging: bool = Field(
        default=True, description="Include logging configuration"
    )
    environment: str = Field(default="production", description="Target environment")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
