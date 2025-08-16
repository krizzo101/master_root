"""
Output schema for Security Scanner.

This module defines the Pydantic schema for security scanner output results.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """Security recommendation."""

    category: str = Field(..., description="Recommendation category")
    priority: str = Field(..., description="Priority level: high, medium, low")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    action: str = Field(..., description="Recommended action")


class SecurityScannerOutput(BaseModel):
    """Output schema for Security Scanner."""

    project_name: str = Field(..., description="Name of the project")

    # Scan results
    dependency_vulnerabilities: dict[str, Any] = Field(
        ..., description="Dependency vulnerability scan results"
    )
    code_vulnerabilities: dict[str, Any] = Field(
        ..., description="Code vulnerability analysis results"
    )
    detected_secrets: list[dict[str, Any]] = Field(
        ..., description="Detected secrets and sensitive information"
    )

    # Recommendations
    recommendations: list[Recommendation] = Field(
        ..., description="Remediation recommendations"
    )

    # Risk assessment
    overall_risk_score: int = Field(..., description="Overall risk score (0-100)")

    # Status
    success: bool = Field(..., description="Whether the scan was successful")
    message: str = Field(..., description="Status message")

    # Metadata
    scan_time: Optional[float] = Field(
        _default=None, description="Time taken for scan (seconds)"
    )
    files_scanned: Optional[int] = Field(
        _default=None, description="Number of files scanned"
    )
    model_used: str = Field(default="o3-mini", description="AI model used for analysis")

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
