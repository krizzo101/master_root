"""Planner agent output schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TaskStep(BaseModel):
    """A single task step in a plan."""

    id: str = Field(..., description="Unique step identifier")
    description: str = Field(..., description="Step description")
    estimated_duration_minutes: int = Field(
        ..., ge=1, description="Estimated duration in minutes"
    )
    dependencies: List[str] = Field(
        default_factory=list, description="Step dependencies"
    )
    resources: List[str] = Field(default_factory=list, description="Required resources")


class PlanOutput(BaseModel):
    """Planner agent output schema."""

    plan_summary: str = Field(..., description="High-level plan summary")
    tasks: List[TaskStep] = Field(..., description="List of task steps")
    timeline_hours: int = Field(
        ..., ge=1, description="Total estimated timeline in hours"
    )
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    success_criteria: List[str] = Field(..., description="Success criteria")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in plan quality"
    )


class PlanRevision(BaseModel):
    """Plan revision output."""

    original_plan_id: str = Field(..., description="Original plan identifier")
    changes: List[str] = Field(..., description="List of changes made")
    rationale: str = Field(..., description="Reason for changes")
    new_confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Updated confidence score"
    )
