"""Specifier agent output schemas."""

from typing import List

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """A single requirement."""

    id: str = Field(..., description="Requirement identifier")
    description: str = Field(..., description="Requirement description")
    priority: str = Field(..., description="Priority level (high/medium/low)")
    type: str = Field(..., description="Requirement type (functional/non-functional)")
    acceptance_criteria: List[str] = Field(..., description="Acceptance criteria")


class Constraint(BaseModel):
    """A constraint on the system."""

    id: str = Field(..., description="Constraint identifier")
    description: str = Field(..., description="Constraint description")
    type: str = Field(
        ..., description="Constraint type (technical/business/regulatory)"
    )
    impact: str = Field(..., description="Impact level (high/medium/low)")


class SpecificationOutput(BaseModel):
    """Specifier agent output schema."""

    requirements: List[Requirement] = Field(..., description="List of requirements")
    constraints: List[Constraint] = Field(
        default_factory=list, description="System constraints"
    )
    architecture_hints: List[str] = Field(
        default_factory=list, description="Architecture suggestions"
    )
    technology_recommendations: List[str] = Field(
        default_factory=list, description="Technology recommendations"
    )
    data_models: List[str] = Field(
        default_factory=list, description="Data model descriptions"
    )
    api_specifications: List[str] = Field(
        default_factory=list, description="API specifications"
    )
    security_considerations: List[str] = Field(
        default_factory=list, description="Security considerations"
    )
    performance_requirements: List[str] = Field(
        default_factory=list, description="Performance requirements"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in specification quality"
    )
