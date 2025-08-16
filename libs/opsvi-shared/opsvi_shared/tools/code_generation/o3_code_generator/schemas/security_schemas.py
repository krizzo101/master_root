"""
Pydantic schemas for security scanner.

This module defines the input and output schemas for the security scanner,
ensuring type safety and validation for all data structures.
"""

from typing import Any

from pydantic import BaseModel, Field


class SecurityInput(BaseModel):
    """Input schema for security scanning."""

    target_path: str = Field(
        ..., description="Path to the target for security scanning"
    )

    scan_type: str = Field(
        _default="comprehensive", description="Type of security scan to perform"
    )

    compliance_standards: list[str] = Field(
        _default=["owasp", "gdpr"], description="Compliance standards to check"
    )

    severity_threshold: str = Field(
        _default="medium", description="Minimum severity threshold for reporting"
    )

    include_remediation: bool = Field(
        _default=True, description="Include remediation plan"
    )

    include_best_practices: bool = Field(
        _default=True, description="Include security best practices"
    )

    model: str = Field(default="o3-mini", description="O3 model to use for generation")

    temperature: float = Field(
        _default=0.1, ge=0.0, le=2.0, description="Temperature for generation"
    )


class SecurityOutput(BaseModel):
    """Output schema for security scanning."""

    security_report: dict[str, Any] = Field(
        ..., description="Generated security report"
    )

    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )

    security_info: dict[str, Any] = Field(
        ..., description="Security analysis information"
    )

    generation_time: float = Field(
        ..., description="Time taken for scanning in seconds"
    )

    model_used: str = Field(..., description="O3 model used for generation")
