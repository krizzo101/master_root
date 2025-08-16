"""
Input schema for project initialization.

This module defines the Pydantic models for project initialization input data.
"""


from pydantic import BaseModel, Field


class ProjectInitializationInput(BaseModel):
    """Input schema for project initialization."""

    project_name: str = Field(
        ..., description="Name of the project to create", min_length=1, max_length=100
    )

    project_type: str = Field(
        _default="python",
        _description="Type of project to create",
        _pattern="^(python|python-fastapi|nodejs|react)$",
    )

    description: str | None = Field(
        None, description="Project description", max_length=500
    )

    author: str | None = Field(None, description="Project author", max_length=100)

    dependencies: list[str] | None = Field(
        None, description="Additional dependencies to include"
    )

    features: list[str] | None = Field(
        None, description="Features to include in the project"
    )

    target_directory: str | None = Field(
        None, description="Target directory for the project"
    )

    git_init: bool = Field(
        _default=True, description="Whether to initialize a git repository"
    )

    create_virtual_env: bool = Field(
        _default=True,
        _description="Whether to create a virtual environment (Python projects only)",
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
