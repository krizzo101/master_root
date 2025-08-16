"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See arango_db_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)


import httpx
from typing import List, Any, Optional
import os

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)

# --- Configuration ---
# The service URL for the standalone ArangoDB service
ARANGO_SERVICE_URL = os.getenv("ARANGO_SERVICE_URL", "http://127.0.0.1:5001")


class ArangoDBPlugin(BasePlugin):
    """
    A multi-purpose plugin to interact with a standalone ArangoDB service.
    This plugin acts as a client to the service, which handles direct
    database communication.
    """

    def __init__(self):
        # The client is now an HTTPX client for talking to our service
        self.http_client: Optional[httpx.AsyncClient] = None
        self.service_url = ARANGO_SERVICE_URL

    @staticmethod
    def get_name() -> str:
        return "arango_db"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initializes the HTTP client."""
        self.event_bus = event_bus
        # Configuration can be used to override the default service URL if needed
        config_data = config.config if hasattr(config, "config") else config
        self.service_url = config_data.get("service_url", self.service_url)

        self.http_client = httpx.AsyncClient(base_url=self.service_url, timeout=30.0)

        try:
            # Check if the service is responsive on initialization
            response = await self.http_client.get("/status")
            response.raise_for_status()
            status_data = response.json()
            if status_data.get("database_connection") == "ok":
                print(
                    f"ArangoDB service client initialized successfully. Connected to: {self.service_url}"
                )
            else:
                print(
                    f"!! Warning: ArangoDB service is running, but has no DB connection: {status_data.get('message')}"
                )

        except httpx.RequestError as e:
            print(
                f"!! ArangoDB service at {self.service_url} is not reachable on initialization: {e}"
            )
            # We don't raise an error, allowing for lazy startup of the service
        except Exception as e:
            print(
                f"!! An unexpected error occurred during ArangoDB plugin initialization: {e}"
            )

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """
        Routes the execution request to the appropriate endpoint in the
        ArangoDB service.
        """
        if not self.http_client:
            return PluginResult(
                success=False, error_message="ArangoDB service client not initialized."
            )

        params = context.state
        action = params.get("action", "query")

        # Map the plugin action to a service endpoint and payload
        endpoint_map = {
            "query": (
                "/aql/query",
                {
                    "query": params.get("query"),
                    "bind_vars": params.get("bind_vars", {}),
                },
            ),
            "get_document": (
                "/documents/get",
                {"collection": params.get("collection"), "key": params.get("key")},
            ),
            "upsert_document": (
                "/documents/upsert",
                {
                    "collection": params.get("collection"),
                    "document": params.get("document"),
                },
            ),
            "insert": (
                "/documents/insert",
                {
                    "collection": params.get("collection"),
                    "document": params.get("document"),
                },
            ),
            "create_collection": ("/collections/create", {"name": params.get("name")}),
        }

        if action not in endpoint_map:
            return PluginResult(
                success=False, error_message=f"Unknown action: {action}"
            )

        endpoint, json_payload = endpoint_map[action]

        try:
            response = await self.http_client.post(endpoint, json=json_payload)

            # Forward the response from the service
            if response.is_success:
                return PluginResult(success=True, data=response.json())
            else:
                # Pass the detailed error from the service back to the orchestrator
                error_details = response.json()
                return PluginResult(
                    success=False,
                    error_message=f"Error from ArangoDB service (HTTP {response.status_code})",
                    data=error_details,
                )

        except httpx.RequestError as e:
            return PluginResult(
                success=False,
                error_message=f"Failed to connect to ArangoDB service: {e}",
                data={"service_url": self.service_url, "endpoint": endpoint},
            )
        except Exception as e:
            return PluginResult(success=False, data={"error_message": str(e)})

    async def cleanup(self) -> None:
        """Closes the HTTP client."""
        if self.http_client:
            await self.http_client.aclose()

    def get_capabilities(self) -> List[Capability]:
        """The capabilities remain the same from the perspective of the orchestrator."""
        return [
            Capability(
                name="query",
                description="Executes an AQL query via the ArangoDB service.",
            ),
            Capability(
                name="get_document",
                description="Retrieves a single document by its _key via the ArangoDB service.",
            ),
            Capability(
                name="upsert_document",
                description="Inserts or updates a document via the ArangoDB service.",
            ),
            Capability(
                name="insert",
                description="Inserts a document into a collection via the ArangoDB service.",
            ),
            Capability(
                name="create_collection",
                description="Creates a new collection via the ArangoDB service.",
            ),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Input validation is now primarily handled by the service, but basic checks can remain."""
        # For now, we assume the service performs all necessary validation.
        return ValidationResult(is_valid=True, errors=[])
