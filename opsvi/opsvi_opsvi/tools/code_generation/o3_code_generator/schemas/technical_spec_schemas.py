"""
Technical Specification Schemas

This module defines the Pydantic models for technical specification generation input and output data.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SpecificationType(str, Enum):
    """Types of technical specifications."""

    COMPREHENSIVE = "comprehensive"
    API_ONLY = "api_only"
    DATABASE_ONLY = "database_only"
    INTEGRATION_ONLY = "integration_only"
    PERFORMANCE_ONLY = "performance_only"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    """Output formats for specifications."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    YAML = "yaml"
    OPENAPI = "openapi"
    SQL = "sql"


class TechnologyStack(BaseModel):
    """Technology stack configuration."""

    language: str = Field(..., description="Primary programming language")
    framework: Optional[str] = Field(None, description="Primary framework")
    database: Optional[str] = Field(None, description="Database technology")
    cache: Optional[str] = Field(None, description="Caching technology")
    message_queue: Optional[str] = Field(None, description="Message queue technology")
    containerization: Optional[str] = Field(
        None, description="Containerization technology"
    )
    cloud_platform: Optional[str] = Field(None, description="Cloud platform")
    monitoring: Optional[str] = Field(None, description="Monitoring technology")


class APISpecification(BaseModel):
    """API specification configuration."""

    include_rest: bool = Field(
        default=True, description="Include REST API specifications"
    )
    include_graphql: bool = Field(
        default=False, description="Include GraphQL specifications"
    )
    include_websocket: bool = Field(
        default=False, description="Include WebSocket specifications"
    )
    authentication_methods: list[str] = Field(
        default=["jwt"], description="Authentication methods"
    )
    rate_limiting: bool = Field(
        default=True, description="Include rate limiting specifications"
    )
    versioning: bool = Field(default=True, description="Include API versioning")
    documentation: bool = Field(default=True, description="Include API documentation")


class DatabaseSpecification(BaseModel):
    """Database specification configuration."""

    database_type: str = Field(default="postgresql", description="Database type")
    include_schema: bool = Field(default=True, description="Include database schema")
    include_migrations: bool = Field(
        default=True, description="Include migration scripts"
    )
    include_indexes: bool = Field(
        default=True, description="Include index specifications"
    )
    include_constraints: bool = Field(
        default=True, description="Include constraint specifications"
    )
    include_triggers: bool = Field(
        default=False, description="Include trigger specifications"
    )
    include_stored_procedures: bool = Field(
        default=False, description="Include stored procedures"
    )


class IntegrationSpecification(BaseModel):
    """Integration specification configuration."""

    external_apis: list[str] = Field(
        default=[], description="External APIs to integrate with"
    )
    message_queues: list[str] = Field(default=[], description="Message queue systems")
    event_streams: list[str] = Field(
        default=[], description="Event streaming platforms"
    )
    data_sync: bool = Field(
        default=False, description="Include data synchronization specifications"
    )
    service_mesh: bool = Field(
        default=False, description="Include service mesh specifications"
    )
    api_gateway: bool = Field(
        default=False, description="Include API gateway specifications"
    )


class PerformanceSpecification(BaseModel):
    """Performance specification configuration."""

    load_testing: bool = Field(
        default=True, description="Include load testing specifications"
    )
    performance_benchmarks: bool = Field(
        default=True, description="Include performance benchmarks"
    )
    scalability_requirements: bool = Field(
        default=True, description="Include scalability requirements"
    )
    resource_utilization: bool = Field(
        default=True, description="Include resource utilization specs"
    )
    monitoring_alerting: bool = Field(
        default=True, description="Include monitoring and alerting"
    )
    optimization_guidelines: bool = Field(
        default=True, description="Include optimization guidelines"
    )


class SecuritySpecification(BaseModel):
    """Security specification configuration."""

    authentication: bool = Field(
        default=True, description="Include authentication specifications"
    )
    authorization: bool = Field(
        default=True, description="Include authorization specifications"
    )
    data_encryption: bool = Field(
        default=True, description="Include data encryption specifications"
    )
    network_security: bool = Field(
        default=True, description="Include network security specifications"
    )
    compliance: list[str] = Field(default=[], description="Compliance requirements")
    vulnerability_scanning: bool = Field(
        default=True, description="Include vulnerability scanning"
    )


class TechnicalSpecInput(BaseModel):
    """Input schema for technical specification generation."""

    system_architecture: str = Field(
        ...,
        description="Description of the system architecture",
        min_length=10,
        max_length=1000,
    )

    specification_type: SpecificationType = Field(
        default=SpecificationType.COMPREHENSIVE,
        description="Type of specification to generate",
    )

    technology_stack: TechnologyStack = Field(
        ..., description="Technology stack configuration"
    )

    api_specs: Optional[APISpecification] = Field(
        default_factory=APISpecification, description="API specification configuration"
    )

    database_specs: Optional[DatabaseSpecification] = Field(
        default_factory=DatabaseSpecification,
        description="Database specification configuration",
    )

    integration_specs: Optional[IntegrationSpecification] = Field(
        default_factory=IntegrationSpecification,
        description="Integration specification configuration",
    )

    performance_specs: Optional[PerformanceSpecification] = Field(
        default_factory=PerformanceSpecification,
        description="Performance specification configuration",
    )

    security_specs: Optional[SecuritySpecification] = Field(
        default_factory=SecuritySpecification,
        description="Security specification configuration",
    )

    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN, description="Output format for specifications"
    )

    model: str = Field(default="o4-mini", description="O4 model to use for generation")

    max_tokens: int = Field(
        default=8000, ge=1000, le=32000, description="Maximum tokens for generation"
    )

    additional_requirements: Optional[str] = Field(
        None, description="Additional requirements or constraints", max_length=2000
    )

    context_files: Optional[list[str]] = Field(
        None, description="List of context file paths"
    )

    variables: Optional[dict[str, Any]] = Field(
        None, description="Variables for template substitution"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class APISpecOutput(BaseModel):
    """API specification output."""

    openapi_spec: dict[str, Any] = Field(..., description="OpenAPI 3.0 specification")
    endpoints: list[dict[str, Any]] = Field(..., description="API endpoint definitions")
    authentication_spec: dict[str, Any] = Field(
        ..., description="Authentication specifications"
    )
    rate_limiting_spec: dict[str, Any] = Field(
        ..., description="Rate limiting specifications"
    )
    error_handling_spec: dict[str, Any] = Field(
        ..., description="Error handling specifications"
    )
    documentation: str = Field(..., description="API documentation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class DatabaseSpecOutput(BaseModel):
    """Database specification output."""

    schema_definition: dict[str, Any] = Field(
        ..., description="Database schema definition"
    )
    table_definitions: list[dict[str, Any]] = Field(
        ..., description="Table definitions"
    )
    relationships: list[dict[str, Any]] = Field(..., description="Table relationships")
    indexes: list[dict[str, Any]] = Field(..., description="Index specifications")
    constraints: list[dict[str, Any]] = Field(
        ..., description="Constraint specifications"
    )
    migration_scripts: list[str] = Field(..., description="Migration scripts")
    data_validation_rules: list[dict[str, Any]] = Field(
        ..., description="Data validation rules"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class IntegrationSpecOutput(BaseModel):
    """Integration specification output."""

    external_integrations: list[dict[str, Any]] = Field(
        ..., description="External service integrations"
    )
    message_queue_specs: list[dict[str, Any]] = Field(
        ..., description="Message queue specifications"
    )
    event_stream_specs: list[dict[str, Any]] = Field(
        ..., description="Event streaming specifications"
    )
    data_sync_specs: dict[str, Any] = Field(
        ..., description="Data synchronization specifications"
    )
    service_mesh_config: dict[str, Any] = Field(
        ..., description="Service mesh configuration"
    )
    api_gateway_config: dict[str, Any] = Field(
        ..., description="API gateway configuration"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class PerformanceSpecOutput(BaseModel):
    """Performance specification output."""

    load_testing_specs: dict[str, Any] = Field(
        ..., description="Load testing specifications"
    )
    performance_benchmarks: dict[str, Any] = Field(
        ..., description="Performance benchmarks"
    )
    scalability_requirements: dict[str, Any] = Field(
        ..., description="Scalability requirements"
    )
    resource_utilization: dict[str, Any] = Field(
        ..., description="Resource utilization specifications"
    )
    monitoring_alerting: dict[str, Any] = Field(
        ..., description="Monitoring and alerting specifications"
    )
    optimization_guidelines: list[str] = Field(
        ..., description="Optimization guidelines"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class SecuritySpecOutput(BaseModel):
    """Security specification output."""

    authentication_spec: dict[str, Any] = Field(
        ..., description="Authentication specifications"
    )
    authorization_spec: dict[str, Any] = Field(
        ..., description="Authorization specifications"
    )
    data_encryption_spec: dict[str, Any] = Field(
        ..., description="Data encryption specifications"
    )
    network_security_spec: dict[str, Any] = Field(
        ..., description="Network security specifications"
    )
    compliance_spec: dict[str, Any] = Field(
        ..., description="Compliance specifications"
    )
    vulnerability_scanning_spec: dict[str, Any] = Field(
        ..., description="Vulnerability scanning specifications"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class TechnicalSpecOutput(BaseModel):
    """Output schema for technical specification generation."""

    success: bool = Field(..., description="Whether generation was successful")

    technical_specifications: dict[str, Any] = Field(
        ..., description="Generated technical specifications"
    )

    system_overview: str = Field(..., description="System overview and architecture")

    api_specifications: Optional[APISpecOutput] = Field(
        None, description="API specifications"
    )

    database_schemas: Optional[DatabaseSpecOutput] = Field(
        None, description="Database schema specifications"
    )

    integration_specifications: Optional[IntegrationSpecOutput] = Field(
        None, description="Integration specifications"
    )

    performance_specifications: Optional[PerformanceSpecOutput] = Field(
        None, description="Performance specifications"
    )

    security_specifications: Optional[SecuritySpecOutput] = Field(
        None, description="Security specifications"
    )

    implementation_guidelines: dict[str, Any] = Field(
        ..., description="Implementation guidelines and best practices"
    )

    output_files: list[str] = Field(..., description="Paths to generated output files")

    generation_time: float = Field(
        ..., description="Time taken for generation in seconds"
    )

    model_used: str = Field(..., description="O3 model used for generation")

    error_message: Optional[str] = Field(
        None, description="Error message if generation failed"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


# Individual specification input schemas for specific generators
class APISpecInput(BaseModel):
    """Input schema for API specification generation."""

    interface_design: str = Field(..., description="Interface design description")
    api_requirements: dict[str, Any] = Field(..., description="API requirements")
    authentication_requirements: Optional[dict[str, Any]] = Field(
        None, description="Authentication requirements"
    )
    rate_limiting_requirements: Optional[dict[str, Any]] = Field(
        None, description="Rate limiting requirements"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.OPENAPI, description="Output format"
    )
    model: str = Field(default="o4-mini", description="O4 model to use")
    max_tokens: int = Field(default=8000, description="Maximum tokens for generation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class DatabaseSchemaInput(BaseModel):
    """Input schema for database schema generation."""

    data_models: dict[str, Any] = Field(..., description="Data models and entities")
    requirements: dict[str, Any] = Field(..., description="Database requirements")
    database_type: str = Field(default="postgresql", description="Database type")
    include_migrations: bool = Field(
        default=True, description="Include migration scripts"
    )
    include_indexes: bool = Field(
        default=True, description="Include index specifications"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.SQL, description="Output format"
    )
    model: str = Field(default="o4-mini", description="O4 model to use")
    max_tokens: int = Field(default=8000, description="Maximum tokens for generation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class IntegrationSpecInput(BaseModel):
    """Input schema for integration specification generation."""

    system_architecture: str = Field(..., description="System architecture description")
    integration_requirements: dict[str, Any] = Field(
        ..., description="Integration requirements"
    )
    external_services: list[str] = Field(
        default=[], description="External services to integrate with"
    )
    protocols: list[str] = Field(default=[], description="Integration protocols")
    output_format: OutputFormat = Field(
        default=OutputFormat.JSON, description="Output format"
    )
    model: str = Field(default="o4-mini", description="O4 model to use")
    max_tokens: int = Field(default=8000, description="Maximum tokens for generation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True


class PerformanceSpecInput(BaseModel):
    """Input schema for performance specification generation."""

    performance_requirements: dict[str, Any] = Field(
        ..., description="Performance requirements"
    )
    constraints: dict[str, Any] = Field(..., description="Performance constraints")
    load_patterns: Optional[dict[str, Any]] = Field(None, description="Load patterns")
    scalability_requirements: Optional[dict[str, Any]] = Field(
        None, description="Scalability requirements"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN, description="Output format"
    )
    model: str = Field(default="o4-mini", description="O4 model to use")
    max_tokens: int = Field(default=8000, description="Maximum tokens for generation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
