"""Coder agent output schemas."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class CodeFile(BaseModel):
    """A code file with its content."""

    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")
    language: str = Field(..., description="Programming language")
    dependencies: List[str] = Field(
        default_factory=list, description="File dependencies"
    )


class TestCase(BaseModel):
    """A test case."""

    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test description")
    test_code: str = Field(..., description="Test code")
    expected_result: str = Field(..., description="Expected test result")


class CodeOutput(BaseModel):
    """Coder agent output schema."""

    files: List[CodeFile] = Field(..., description="Generated code files")
    tests: List[TestCase] = Field(default_factory=list, description="Test cases")
    documentation: str = Field(default="", description="Code documentation")
    dependencies: List[str] = Field(
        default_factory=list, description="External dependencies"
    )
    build_instructions: str = Field(default="", description="Build instructions")
    deployment_notes: str = Field(default="", description="Deployment notes")
    code_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Code quality score"
    )
    test_coverage_estimate: float = Field(
        ..., ge=0.0, le=1.0, description="Estimated test coverage"
    )
    complexity_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Complexity analysis"
    )
    security_considerations: List[str] = Field(
        default_factory=list, description="Security considerations"
    )
