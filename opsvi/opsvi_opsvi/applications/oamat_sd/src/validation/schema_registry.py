"""
Schema Registry Module

Manages request schemas and validation rules for different request types.
Extracted from request_validation.py for better modularity.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.applications.oamat_sd.src.models.validation_models import (
    RequestField,
    RequestSchema,
    RequestType,
)


class RequestSchemaRegistry:
    """Registry for request schemas and validation rules."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._schemas: Dict[RequestType, RequestSchema] = {}
        self._initialize_default_schemas()

    def _initialize_default_schemas(self):
        """Initialize default schemas for common request types."""

        # Web Application Schema
        web_app_fields = [
            RequestField("name", "Application name", str, required=True),
            RequestField("description", "Application description", str, required=True),
            RequestField(
                "framework",
                "Web framework (React, Vue, etc.)",
                str,
                required=False,
                default="React",
            ),
            RequestField(
                "styling",
                "Styling approach (CSS, Tailwind, etc.)",
                str,
                required=False,
                default="Tailwind",
            ),
            RequestField(
                "authentication",
                "Authentication requirements",
                str,
                required=False,
                default="basic",
            ),
            RequestField(
                "database",
                "Database requirements",
                str,
                required=False,
                default="SQLite",
            ),
            RequestField(
                "deployment", "Deployment target", str, required=False, default="local"
            ),
        ]

        self._schemas[RequestType.WEB_APPLICATION] = RequestSchema(
            request_type=RequestType.WEB_APPLICATION,
            description="Full-stack web application development",
            fields=web_app_fields,
        )

        # Microservices Schema
        microservices_fields = [
            RequestField("service_name", "Primary service name", str, required=True),
            RequestField(
                "architecture", "Service architecture description", str, required=True
            ),
            RequestField("services", "List of required services", list, required=True),
            RequestField(
                "communication",
                "Inter-service communication",
                str,
                required=False,
                default="REST",
            ),
            RequestField(
                "data_storage",
                "Data storage strategy",
                str,
                required=False,
                default="PostgreSQL",
            ),
            RequestField(
                "orchestration",
                "Container orchestration",
                str,
                required=False,
                default="Docker",
            ),
        ]

        self._schemas[RequestType.MICROSERVICES] = RequestSchema(
            request_type=RequestType.MICROSERVICES,
            description="Microservices architecture development",
            fields=microservices_fields,
        )

        # Simple Script Schema
        script_fields = [
            RequestField("purpose", "Script purpose/goal", str, required=True),
            RequestField(
                "language",
                "Programming language",
                str,
                required=False,
                default="Python",
            ),
            RequestField(
                "inputs",
                "Input requirements",
                str,
                required=False,
                default="command line",
            ),
            RequestField(
                "outputs", "Expected outputs", str, required=False, default="console"
            ),
        ]

        self._schemas[RequestType.SIMPLE_SCRIPT] = RequestSchema(
            request_type=RequestType.SIMPLE_SCRIPT,
            description="Simple script or utility development",
            fields=script_fields,
        )

        # Data Analysis Schema
        data_analysis_fields = [
            RequestField("data_source", "Data source description", str, required=True),
            RequestField("analysis_goal", "Analysis objectives", str, required=True),
            RequestField(
                "tools",
                "Analysis tools/libraries",
                str,
                required=False,
                default="pandas",
            ),
            RequestField(
                "output_format",
                "Output format requirements",
                str,
                required=False,
                default="report",
            ),
        ]

        self._schemas[RequestType.DATA_ANALYSIS] = RequestSchema(
            request_type=RequestType.DATA_ANALYSIS,
            description="Data analysis and visualization",
            fields=data_analysis_fields,
        )

        # Automation Schema
        automation_fields = [
            RequestField("task_description", "Task to automate", str, required=True),
            RequestField(
                "trigger", "Automation trigger", str, required=False, default="manual"
            ),
            RequestField(
                "frequency",
                "Execution frequency",
                str,
                required=False,
                default="on-demand",
            ),
            RequestField(
                "notifications",
                "Notification requirements",
                str,
                required=False,
                default="none",
            ),
        ]

        self._schemas[RequestType.AUTOMATION] = RequestSchema(
            request_type=RequestType.AUTOMATION,
            description="Process automation and workflow",
            fields=automation_fields,
        )

        self.logger.info(f"Initialized {len(self._schemas)} default schemas")

    def get_schema(self, request_type: RequestType) -> Optional[RequestSchema]:
        """Get schema for a specific request type."""
        return self._schemas.get(request_type)

    def register_schema(self, schema: RequestSchema):
        """Register a new schema."""
        self._schemas[schema.request_type] = schema
        self.logger.info(f"Registered schema for {schema.request_type}")

    def list_schemas(self) -> List[RequestType]:
        """List all available schema types."""
        return list(self._schemas.keys())

    def validate_compliance(
        self, request_type: RequestType, data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate data compliance with schema."""
        schema = self.get_schema(request_type)
        if not schema:
            return False, [f"No schema found for request type: {request_type}"]

        errors = []
        required_fields = schema.get_required_fields()

        for field in required_fields:
            if field.name not in data:
                errors.append(f"Missing required field: {field.name}")
            elif not isinstance(data[field.name], field.field_type):
                errors.append(
                    f"Invalid type for field {field.name}: expected {field.field_type.__name__}"
                )

        return len(errors) == 0, errors

    def get_field_by_name(
        self, request_type: RequestType, field_name: str
    ) -> Optional[RequestField]:
        """Get a specific field from a schema by name."""
        schema = self.get_schema(request_type)
        if not schema:
            return None

        for field in schema.fields:
            if field.name == field_name:
                return field
        return None

    def get_all_field_names(self, request_type: RequestType) -> List[str]:
        """Get all field names for a request type."""
        schema = self.get_schema(request_type)
        if not schema:
            return []

        return [field.name for field in schema.fields]

    def get_required_field_names(self, request_type: RequestType) -> List[str]:
        """Get all required field names for a request type."""
        schema = self.get_schema(request_type)
        if not schema:
            return []

        return [field.name for field in schema.get_required_fields()]
