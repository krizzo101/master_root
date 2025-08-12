"""
Input schema for Performance Optimizer.

This module defines the Pydantic schema for performance optimizer input configuration.
"""

from typing import Optional

from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    """Configuration for performance analysis settings."""

    max_files_analyzed: int = Field(
        _default=10, description="Maximum number of files to analyze"
    )
    include_algorithm_analysis: bool = Field(
        _default=True, description="Include algorithm analysis"
    )
    include_complexity_analysis: bool = Field(
        _default=True, description="Include complexity analysis"
    )
    include_memory_analysis: bool = Field(
        _default=True, description="Include memory usage analysis"
    )
    include_io_analysis: bool = Field(
        _default=True, description="Include I/O performance analysis"
    )
    analysis_depth: str = Field(
        _default="standard", description="Analysis depth: quick, standard, deep"
    )


class ProfilingConfig(BaseModel):
    """Configuration for profiling settings."""

    max_files_profiled: int = Field(
        _default=5, description="Maximum number of files to profile"
    )
    include_execution_time: bool = Field(
        _default=True, description="Profile execution time"
    )
    include_memory_usage: bool = Field(default=True, description="Profile memory usage")
    include_cpu_usage: bool = Field(default=True, description="Profile CPU usage")
    profiling_duration: int = Field(
        _default=60, description="Profiling duration in seconds"
    )


class OptimizationConfig(BaseModel):
    """Configuration for optimization settings."""

    include_high_priority: bool = Field(
        _default=True, description="Include high-priority optimizations"
    )
    include_medium_priority: bool = Field(
        _default=True, description="Include medium-priority optimizations"
    )
    include_low_priority: bool = Field(
        _default=True, description="Include low-priority optimizations"
    )
    include_implementation_guide: bool = Field(
        _default=True, description="Include implementation guides"
    )
    include_performance_metrics: bool = Field(
        _default=True, description="Include performance metrics"
    )
    include_best_practices: bool = Field(
        _default=True, description="Include best practices"
    )


class PerformanceOptimizerInput(BaseModel):
    """Input schema for Performance Optimizer."""

    project_name: str = Field(..., description="Name of the project")
    project_path: str = Field(..., description="Path to the project directory")
    openai_api_key: str = Field(..., description="OpenAI API key for O3 model access")

    # Configuration options
    analysis_config: AnalysisConfig = Field(
        _default_factory=AnalysisConfig, description="Analysis configuration"
    )
    profiling_config: ProfilingConfig = Field(
        _default_factory=ProfilingConfig, description="Profiling configuration"
    )
    optimization_config: OptimizationConfig = Field(
        _default_factory=OptimizationConfig, description="Optimization configuration"
    )

    # Output options
    output_file: Optional[str] = Field(
        _default=None, description="Output file for results"
    )
    output_format: str = Field(
        _default="json", description="Output format: json, html, markdown"
    )

    # Additional options
    include_recommendations: bool = Field(
        _default=True, description="Include optimization recommendations"
    )
    include_metrics: bool = Field(
        _default=True, description="Include performance metrics"
    )
    optimization_timeout: int = Field(
        _default=300, description="Optimization timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""

        _extra = "forbid"
        _validate_assignment = True
