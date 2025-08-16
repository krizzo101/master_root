"""
Input schema for Security Scanner.

This module defines the Pydantic schema for security scanner input configuration.
"""


from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    """Configuration for security analysis settings."""

    max_files_analyzed: int = Field(
        default=10, description="Maximum number of files to analyze"
    )
    include_dependencies: bool = Field(
        default=True, description="Include dependency scanning"
    )
    include_code_analysis: bool = Field(
        default=True, description="Include code analysis"
    )
    include_secret_detection: bool = Field(
        default=True, description="Include secret detection"
    )
    include_config_review: bool = Field(
        default=True, description="Include configuration review"
    )
    scan_depth: str = Field(
        default="standard", description="Scan depth: quick, standard, deep"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="File patterns to exclude"
    )


class SecurityScannerInput(BaseModel):
    """Input schema for Security Scanner."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")
    model: str = Field(
        default="o4-mini", description="O3 model to use for security analysis"
    )

    # Analysis configuration
    analysis_config: AnalysisConfig = Field(
        default_factory=AnalysisConfig, description="Analysis configuration"
    )

    # Output options
    output_file: str | None = Field(default=None, description="Output file for results")
    output_format: str = Field(
        default="json", description="Output format: json, html, markdown"
    )

    # Additional options
    include_recommendations: bool = Field(
        default=True, description="Include remediation recommendations"
    )
    risk_threshold: int = Field(
        default=50, description="Risk threshold for high priority alerts"
    )
    scan_timeout: int = Field(default=300, description="Scan timeout in seconds")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
