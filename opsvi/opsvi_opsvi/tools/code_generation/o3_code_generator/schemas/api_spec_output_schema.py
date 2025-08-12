"""
API Specification Output Schema

Defines the structure for API specification generation outputs with
validation framework integration.
"""

from typing import Any

from pydantic import Field

from .base_output_schema import BaseGeneratorOutput


class APISpecOutput(BaseGeneratorOutput):
    """
    Output schema for API specification generation.

    Inherits from BaseGeneratorOutput to ensure consistent validation
    framework integration with success/error reporting.
    """

    api_spec: dict[str, Any] = Field(
        default_factory=dict,
        description="Generated API specification in OpenAPI format",
    )

    endpoints: list[dict[str, Any]] = Field(
        default_factory=list, description="List of API endpoints with details"
    )

    models: list[dict[str, Any]] = Field(
        default_factory=list, description="Data models/schemas used in the API"
    )

    authentication: dict[str, Any] | None = Field(
        default=None, description="Authentication configuration"
    )

    version: str = Field(default="1.0.0", description="API version")

    format_type: str = Field(
        default="openapi", description="Specification format (openapi, swagger, etc.)"
    )

    def add_endpoint(self, method: str, path: str, description: str, **kwargs) -> None:
        """Add an endpoint to the API specification."""
        endpoint = {
            "method": method.upper(),
            "path": path,
            "description": description,
            **kwargs,
        }
        self.endpoints.append(endpoint)
        self.add_metadata("endpoint_count", len(self.endpoints))

    def add_model(self, name: str, properties: dict[str, Any], **kwargs) -> None:
        """Add a data model to the API specification."""
        model = {"name": name, "properties": properties, **kwargs}
        self.models.append(model)
        self.add_metadata("model_count", len(self.models))

    def set_authentication(self, auth_type: str, config: dict[str, Any]) -> None:
        """Set authentication configuration for the API."""
        self.authentication = {"type": auth_type, "config": config}
        self.add_metadata("auth_type", auth_type)

    def validate_spec(self) -> bool:
        """Validate that the API specification is complete and valid."""
        if not self.endpoints:
            self.add_warning("No endpoints defined in API specification")
            return False

        if not self.api_spec:
            self.add_warning("API specification object is empty")

        # Check for required fields in endpoints
        for i, endpoint in enumerate(self.endpoints):
            if not endpoint.get("method"):
                self.add_warning(f"Endpoint {i} missing HTTP method")
            if not endpoint.get("path"):
                self.add_warning(f"Endpoint {i} missing path")

        return self.success and not self.error_message

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "error_message": None,
                "warnings": [],
                "metadata": {
                    "endpoint_count": 5,
                    "model_count": 3,
                    "auth_type": "bearer",
                },
                "api_spec": {
                    "openapi": "3.0.0",
                    "info": {"title": "User Management API", "version": "1.0.0"},
                },
                "endpoints": [
                    {"method": "GET", "path": "/users", "description": "List all users"}
                ],
                "models": [
                    {
                        "name": "User",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                    }
                ],
                "authentication": {
                    "type": "bearer",
                    "config": {"scheme": "bearer", "bearerFormat": "JWT"},
                },
                "version": "1.0.0",
                "format_type": "openapi",
            }
        }
