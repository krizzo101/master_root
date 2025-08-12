"""
Input schema for Testing Framework Generator.

This module defines the Pydantic schema for testing framework generator input configuration.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TestGenerationConfig(BaseModel):
    """Configuration for test generation settings."""

    max_components: int = Field(
        default=10, description="Maximum number of components to generate tests for"
    )
    include_unit_tests: bool = Field(default=True, description="Include unit tests")
    include_integration_tests: bool = Field(
        default=True, description="Include integration tests"
    )
    include_e2e_tests: bool = Field(
        default=False, description="Include end-to-end tests"
    )
    include_performance_tests: bool = Field(
        default=False, description="Include performance tests"
    )
    include_security_tests: bool = Field(
        default=False, description="Include security tests"
    )
    test_coverage_target: int = Field(
        default=80, description="Target test coverage percentage"
    )
    include_mocks: bool = Field(default=True, description="Include mock configurations")
    include_fixtures: bool = Field(default=True, description="Include test fixtures")


class FrameworkConfig(BaseModel):
    """Configuration for testing framework settings."""

    test_discovery_patterns: list[str] = Field(
        default_factory=list, description="Test discovery patterns"
    )
    test_reporting: bool = Field(default=True, description="Enable test reporting")
    test_coverage: bool = Field(default=True, description="Enable test coverage")
    test_parallelization: bool = Field(
        default=False, description="Enable test parallelization"
    )
    test_timeout: int = Field(default=30, description="Test timeout in seconds")
    test_filtering: dict[str, Any] = Field(
        default_factory=dict, description="Test filtering configuration"
    )
    test_data_management: bool = Field(
        default=True, description="Enable test data management"
    )
    test_logging: bool = Field(default=True, description="Enable test logging")
    ci_cd_integration: bool = Field(
        default=True, description="Enable CI/CD integration"
    )


class TestingFrameworkGeneratorInput(BaseModel):
    """Input schema for Testing Framework Generator."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")

    # Framework selection
    framework: str = Field(default="pytest", description="Testing framework to use")

    # Configuration options
    test_generation_config: TestGenerationConfig = Field(
        default_factory=TestGenerationConfig,
        description="Test generation configuration",
    )
    framework_config: FrameworkConfig = Field(
        default_factory=FrameworkConfig, description="Framework configuration"
    )

    # Output options
    write_files: bool = Field(
        default=True, description="Write test files to project directory"
    )
    output_file: Optional[str] = Field(
        default=None, description="Output file for results"
    )

    # Additional options
    include_examples: bool = Field(default=True, description="Include example tests")
    include_documentation: bool = Field(
        default=True, description="Include test documentation"
    )
    generation_timeout: int = Field(
        default=300, description="Generation timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
