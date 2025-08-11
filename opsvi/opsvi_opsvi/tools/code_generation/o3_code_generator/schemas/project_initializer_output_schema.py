"""
Output schema for project initialization.

This module defines the Pydantic models for project initialization output data.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ProjectInitializationOutput(BaseModel):
    """Output schema for project initialization."""

    success: bool = Field(
        ..., description="Whether the project initialization was successful"
    )

    project_path: str = Field(..., description="Path to the created project directory")

    created_files: list[str] = Field(
        _default_factory=list, description="List of files that were created"
    )

    next_steps: list[str] = Field(
        _default_factory=list, description="List of next steps for the user to follow"
    )

    error_message: Optional[str] = Field(
        None, description="Error message if initialization failed"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
