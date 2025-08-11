"""
Input schema for Requirements Analyzer.

This module defines the Pydantic schema for requirements analyzer input configuration.
"""

from typing import Optional

from pydantic import BaseModel, Field


class OptimizationConfig(BaseModel):
    """Configuration for requirements optimization settings."""

    include_unused_detection: bool = Field(
        default=True, description="Detect unused dependencies"
    )
    include_version_analysis: bool = Field(
        default=True, description="Analyze version conflicts"
    )
    include_security_scan: bool = Field(
        default=True, description="Include security analysis"
    )
    include_performance_analysis: bool = Field(
        default=True, description="Include performance analysis"
    )
    suggest_alternatives: bool = Field(
        default=True, description="Suggest alternative packages"
    )
    optimize_structure: bool = Field(
        default=True, description="Optimize dependency structure"
    )
    max_analysis_depth: int = Field(default=3, description="Maximum analysis depth")


class RequirementsAnalyzerInput(BaseModel):
    """Input schema for Requirements Analyzer."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")

    # Analysis configuration
    optimization_config: OptimizationConfig = Field(
        default_factory=OptimizationConfig, description="Optimization configuration"
    )

    # Output options
    output_file: Optional[str] = Field(
        default=None, description="Output file for results"
    )
    output_format: str = Field(
        default="json", description="Output format: json, html, markdown"
    )

    # Additional options
    include_recommendations: bool = Field(
        default=True, description="Include optimization recommendations"
    )
    generate_requirements_files: bool = Field(
        default=False, description="Generate optimized requirements files"
    )
    analysis_timeout: int = Field(
        default=300, description="Analysis timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
