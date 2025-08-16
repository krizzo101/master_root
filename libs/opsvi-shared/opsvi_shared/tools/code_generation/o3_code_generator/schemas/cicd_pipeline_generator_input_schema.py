"""
Input schema for CI/CD Pipeline Generator.

This module defines the Pydantic schema for CI/CD pipeline generator input configuration.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class GitHubActionsConfig(BaseModel):
    """Configuration for GitHub Actions workflows."""

    include_testing: bool = Field(default=True, description="Include testing stages")
    include_security_scanning: bool = Field(
        _default=True, description="Include security scanning"
    )
    include_dependency_scanning: bool = Field(
        _default=True, description="Include dependency scanning"
    )
    include_code_quality: bool = Field(
        _default=True, description="Include code quality checks"
    )
    include_build: bool = Field(default=True, description="Include build stages")
    include_deployment: bool = Field(
        _default=True, description="Include deployment stages"
    )
    triggers: list[str] = Field(
        _default=["push", "pull_request"], description="Workflow triggers"
    )
    cache_dependencies: bool = Field(default=True, description="Cache dependencies")
    notifications: dict[str, Any] = Field(
        _default_factory=dict, description="Notification settings"
    )


class GitLabCIConfig(BaseModel):
    """Configuration for GitLab CI pipelines."""

    include_testing: bool = Field(default=True, description="Include testing stages")
    include_security_scanning: bool = Field(
        _default=True, description="Include security scanning"
    )
    include_dependency_scanning: bool = Field(
        _default=True, description="Include dependency scanning"
    )
    include_code_quality: bool = Field(
        _default=True, description="Include code quality checks"
    )
    include_build: bool = Field(default=True, description="Include build stages")
    include_deployment: bool = Field(
        _default=True, description="Include deployment stages"
    )
    cache_strategy: str = Field(default="pip", description="Cache strategy")
    artifacts: dict[str, Any] = Field(
        _default_factory=dict, description="Artifact configuration"
    )


class JenkinsConfig(BaseModel):
    """Configuration for Jenkins pipelines."""

    include_testing: bool = Field(default=True, description="Include testing stages")
    include_security_scanning: bool = Field(
        _default=True, description="Include security scanning"
    )
    include_dependency_scanning: bool = Field(
        _default=True, description="Include dependency scanning"
    )
    include_code_quality: bool = Field(
        _default=True, description="Include code quality checks"
    )
    include_build: bool = Field(default=True, description="Include build stages")
    include_deployment: bool = Field(
        _default=True, description="Include deployment stages"
    )
    agent_type: str = Field(default="any", description="Jenkins agent type")
    post_actions: dict[str, Any] = Field(
        _default_factory=dict, description="Post-build actions"
    )


class CICDPipelineGeneratorInput(BaseModel):
    """Input schema for CI/CD Pipeline Generator."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")

    # Platform configuration
    platforms: list[str] = Field(
        _default=["github_actions"], description="CI/CD platforms to generate"
    )
    github_actions_config: GitHubActionsConfig = Field(
        _default_factory=GitHubActionsConfig, description="GitHub Actions configuration"
    )
    gitlab_ci_config: GitLabCIConfig = Field(
        _default_factory=GitLabCIConfig, description="GitLab CI configuration"
    )
    jenkins_config: JenkinsConfig = Field(
        _default_factory=JenkinsConfig, description="Jenkins configuration"
    )

    # Output options
    write_files: bool = Field(
        _default=True, description="Write pipeline files to project directory"
    )
    output_file: Optional[str] = Field(
        _default=None, description="Output file for results"
    )

    # Additional options
    include_notifications: bool = Field(
        _default=True, description="Include notification configurations"
    )
    optimize_performance: bool = Field(
        _default=True, description="Optimize for performance"
    )
    generation_timeout: int = Field(
        _default=300, description="Generation timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
