"""
File Analysis Output Schema for O3 Code Generator

This module defines the Pydantic models for file analysis output validation.
"""

from pydantic import BaseModel, Field, validator


class Improvement(BaseModel):
    """Schema for individual improvement suggestions"""

    issue_type: str = Field(
        ...,
        _description="Type of improvement (e.g., performance, security, code_quality)",
    )
    message: str = Field(
        ..., description="Detailed description of the improvement suggestion"
    )
    reasoning: str = Field(
        ..., description="Explanation of why this improvement is recommended"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )

    @validator("confidence")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class FileAnalysisOutput(BaseModel):
    """Output schema for file analysis responses"""

    file: str = Field(..., description="Path to the analyzed file")
    improvements: list[Improvement] = Field(
        ..., description="List of improvement suggestions"
    )

    @validator("improvements")
    def validate_improvements(cls, v):
        if not v:
            raise ValueError("At least one improvement must be provided")
        return v

    class Config:
        _schema_extra = {
            "example": {
                "file": "/path/to/file.py",
                "improvements": [
                    {
                        "issue_type": "performance",
                        "message": "Implement caching for repeated operations",
                        "reasoning": "This will reduce redundant computations",
                        "confidence": 0.85,
                    }
                ],
            }
        }
