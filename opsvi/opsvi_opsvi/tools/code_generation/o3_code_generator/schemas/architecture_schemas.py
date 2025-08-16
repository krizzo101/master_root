"""
Architecture Design Schemas for O3 Code Generator

This module defines the Pydantic models for architecture design input and output validation,
ensuring consistent and validated data handling across all architecture design components.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ArchitectureInput(BaseModel):
    """Input schema for architecture design requests."""

    system_requirements: str = Field(
        ..., description="Natural language description of system requirements"
    )
    architecture_type: str = Field(
        default="microservices",
        description="Type of architecture (microservices, monolithic, event-driven, etc.)",
    )
    scalability_requirements: str = Field(
        default="medium",
        description="Scalability requirements (low, medium, high, enterprise)",
    )
    security_requirements: str = Field(
        default="standard",
        description="Security requirements (basic, standard, enterprise, compliance)",
    )
    integration_requirements: list[str] = Field(
        default=[],
        description="List of integration requirements (database, api, messaging, etc.)",
    )
    design_type: str = Field(
        default="comprehensive",
        description="Type of design (basic, comprehensive, detailed)",
    )
    include_diagrams: bool = Field(
        default=True, description="Whether to include visual diagrams"
    )
    output_format: str = Field(
        default="markdown",
        description="Output format (json, markdown, html, plantuml)",
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for design generation"
    )
    max_tokens: int = Field(default=6000, description="Maximum tokens for O3 model")
    temperature: float = Field(default=0.1, description="Temperature for O3 model")
    context_files: Optional[list[str]] = Field(
        default=None, description="List of context file paths"
    )
    additional_constraints: Optional[str] = Field(
        default=None,
        description="Additional architectural constraints or requirements",
    )


class ComponentInput(BaseModel):
    """Input schema for component design requests."""

    architecture_design: dict[str, Any] = Field(
        ..., description="Architecture design specification"
    )
    component_requirements: str = Field(
        ..., description="Component requirements description"
    )
    component_type: str = Field(
        default="service",
        description="Type of component (service, database, api, ui, etc.)",
    )
    interface_requirements: list[str] = Field(
        default=[], description="List of interface requirements"
    )
    dependency_requirements: list[str] = Field(
        default=[], description="List of dependency requirements"
    )
    design_detail_level: str = Field(
        default="detailed",
        description="Level of design detail (basic, detailed, comprehensive)",
    )
    include_diagrams: bool = Field(
        default=True, description="Whether to include component diagrams"
    )
    output_format: str = Field(
        default="markdown", description="Output format for component specifications"
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for component design"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens for O3 model")


class DataFlowInput(BaseModel):
    """Input schema for data flow design requests."""

    system_architecture: dict[str, Any] = Field(
        ..., description="System architecture specification"
    )
    data_requirements: str = Field(
        ..., description="Data flow requirements description"
    )
    data_volume: str = Field(
        default="medium",
        description="Expected data volume (low, medium, high, massive)",
    )
    data_velocity: str = Field(
        default="batch",
        description="Data velocity (batch, near-real-time, real-time, streaming)",
    )
    data_variety: list[str] = Field(
        default=[],
        description="Types of data (structured, unstructured, semi-structured)",
    )
    integration_patterns: list[str] = Field(
        default=[],
        description="Integration patterns (etl, elt, streaming, event-driven)",
    )
    include_diagrams: bool = Field(
        default=True, description="Whether to include data flow diagrams"
    )
    output_format: str = Field(
        default="markdown", description="Output format for data flow specifications"
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for data flow design"
    )
    max_tokens: int = Field(default=5000, description="Maximum tokens for O3 model")


class InterfaceInput(BaseModel):
    """Input schema for interface design requests."""

    component_specifications: dict[str, Any] = Field(
        ..., description="Component specifications"
    )
    interface_requirements: str = Field(
        ..., description="Interface requirements description"
    )
    interface_type: str = Field(
        default="rest",
        description="Type of interface (rest, graphql, grpc, message-queue, etc.)",
    )
    protocol_requirements: list[str] = Field(
        default=[], description="Protocol requirements (http, https, tcp, udp, etc.)"
    )
    authentication_requirements: list[str] = Field(
        default=[],
        description="Authentication requirements (oauth, jwt, api-key, etc.)",
    )
    documentation_requirements: list[str] = Field(
        default=["openapi"],
        description="Documentation requirements (openapi, markdown, html, etc.)",
    )
    include_diagrams: bool = Field(
        default=True, description="Whether to include interface diagrams"
    )
    output_format: str = Field(
        default="markdown", description="Output format for interface specifications"
    )
    model: str = Field(
        default="o3-mini", description="O3 model to use for interface design"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens for O3 model")


class ValidationInput(BaseModel):
    """Input schema for architecture validation requests."""

    architecture_design: dict[str, Any] = Field(
        ..., description="Architecture design to validate"
    )
    validation_scope: list[str] = Field(
        default=["consistency", "scalability", "security", "performance"],
        description="Scope of validation checks",
    )
    validation_level: str = Field(
        default="comprehensive",
        description="Level of validation (basic, standard, comprehensive)",
    )
    include_recommendations: bool = Field(
        default=True, description="Whether to include improvement recommendations"
    )
    include_metrics: bool = Field(
        default=True, description="Whether to include validation metrics"
    )
    output_format: str = Field(
        default="markdown", description="Output format for validation report"
    )
    model: str = Field(default="o3-mini", description="O3 model to use for validation")
    max_tokens: int = Field(default=4000, description="Maximum tokens for O3 model")


class ArchitectureOutput(BaseModel):
    """Output schema for architecture design responses."""

    success: bool = Field(
        ..., description="Whether the design generation was successful"
    )
    architecture_design: dict[str, Any] = Field(
        ..., description="Generated architecture design"
    )
    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )
    diagrams: list[str] = Field(
        default=[], description="List of generated diagram file paths"
    )
    generation_time: float = Field(..., description="Time taken to generate design")
    model_used: str = Field(..., description="Model used for generation")
    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )


class ComponentOutput(BaseModel):
    """Output schema for component design responses."""

    success: bool = Field(
        ..., description="Whether the component design was successful"
    )
    component_specifications: dict[str, Any] = Field(
        ..., description="Generated component specifications"
    )
    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )
    diagrams: list[str] = Field(
        default=[], description="List of generated component diagram paths"
    )
    generation_time: float = Field(
        ..., description="Time taken to generate specifications"
    )
    model_used: str = Field(..., description="Model used for generation")
    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )


class DataFlowOutput(BaseModel):
    """Output schema for data flow design responses."""

    success: bool = Field(
        ..., description="Whether the data flow design was successful"
    )
    data_flow_specifications: dict[str, Any] = Field(
        ..., description="Generated data flow specifications"
    )
    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )
    diagrams: list[str] = Field(
        default=[], description="List of generated data flow diagram paths"
    )
    generation_time: float = Field(
        ..., description="Time taken to generate specifications"
    )
    model_used: str = Field(..., description="Model used for generation")
    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )


class InterfaceOutput(BaseModel):
    """Output schema for interface design responses."""

    success: bool = Field(
        ..., description="Whether the interface design was successful"
    )
    interface_specifications: dict[str, Any] = Field(
        ..., description="Generated interface specifications"
    )
    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )
    diagrams: list[str] = Field(
        default=[], description="List of generated interface diagram paths"
    )
    generation_time: float = Field(
        ..., description="Time taken to generate specifications"
    )
    model_used: str = Field(..., description="Model used for generation")
    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )


class ValidationOutput(BaseModel):
    """Output schema for architecture validation responses."""

    success: bool = Field(..., description="Whether the validation was successful")
    validation_report: dict[str, Any] = Field(
        ..., description="Generated validation report"
    )
    output_files: list[str] = Field(
        ..., description="List of generated output file paths"
    )
    validation_time: float = Field(..., description="Time taken to perform validation")
    model_used: str = Field(..., description="Model used for validation")
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )
