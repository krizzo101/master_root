"""Critic agent output schemas."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Issue(BaseModel):
    """An issue found during review."""

    severity: str = Field(..., description="Issue severity (critical/high/medium/low)")
    category: str = Field(
        ..., description="Issue category (security/performance/quality/etc)"
    )
    description: str = Field(..., description="Issue description")
    location: str = Field(default="", description="Issue location (file/line)")
    suggestion: str = Field(default="", description="Suggested fix")


class Recommendation(BaseModel):
    """A recommendation for improvement."""

    priority: str = Field(..., description="Recommendation priority (high/medium/low)")
    category: str = Field(..., description="Recommendation category")
    description: str = Field(..., description="Recommendation description")
    impact: str = Field(..., description="Expected impact")
    effort: str = Field(..., description="Implementation effort")


class CriticOutput(BaseModel):
    """Critic agent output schema."""

    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall quality score"
    )
    passed: bool = Field(..., description="Whether the output passes quality standards")
    issues: List[Issue] = Field(default_factory=list, description="Issues found")
    recommendations: List[Recommendation] = Field(
        default_factory=list, description="Recommendations"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Strengths identified"
    )
    weaknesses: List[str] = Field(
        default_factory=list, description="Weaknesses identified"
    )
    risk_assessment: Dict[str, Any] = Field(
        default_factory=dict, description="Risk assessment"
    )
    compliance_check: Dict[str, bool] = Field(
        default_factory=dict, description="Compliance checks"
    )
    quality_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Quality metrics"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in assessment"
    )
