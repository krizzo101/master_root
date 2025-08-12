# /home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available/qa_plugin.py
import os
import requests
import logging
from typing import Dict, Any

from asea_orchestrator.plugins.base_plugin import BasePlugin
from asea_orchestrator.plugins.types import (
    ExecutionContext,
    PluginConfig,
    PluginResult,
)

# Set up logging for the plugin
logger = logging.getLogger(__name__)


class QAPlugin(BasePlugin):
    """
    A plugin for Quality Assurance testing. It validates the integration
    with the foundational core systems by calling the dedicated service.
    """

    def __init__(self):
        super().__init__()
        # The service URL is now the single point of configuration
        self.service_url = "http://127.0.0.1:5001"

    @staticmethod
    def get_name() -> str:
        return "QA Plugin"

    @staticmethod
    def get_description() -> str:
        return (
            "Performs QA checks against core functionalities, "
            "validating the service-oriented architecture."
        )

    def initialize(self, config: PluginConfig, event_bus):
        """Initializes the plugin with its configuration."""
        super().initialize(config, event_bus)
        logger.info(f"QA Plugin initialized. Target service URL: {self.service_url}")

    def execute(self, context: ExecutionContext) -> PluginResult:
        """
        Executes the QA test by calling the core systems service.
        """
        target = self.config.get("test_target")
        if target != "core_systems_service":
            return PluginResult(
                success=False,
                error_message=f"Invalid test target: {target}. This plugin only tests 'core_systems_service'.",
            )

        logger.info("Executing QA test against Core Systems Service.")

        # The path to be validated is now hardcoded as it's a known test case
        # for the 'validate_session_continuity' workflow.
        test_file_path = "/home/opsvi/asea/README.md"

        try:
            # Call the /validate_paths endpoint of the service
            response = requests.post(
                f"{self.service_url}/validate_paths",
                json={"paths": [test_file_path]},
                timeout=10,  # 10 second timeout
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            validation_result = response.json()
            logger.info(f"Received validation result from service: {validation_result}")

            # Process the result from the service
            file_status = validation_result.get(test_file_path, {})
            is_valid = file_status.get("exists", False)

            if is_valid:
                logger.info("QA test PASSED: Path validation successful.")
                return PluginResult(
                    success=True,
                    data={"validation_status": "passed", "details": file_status},
                )
            else:
                logger.warning("QA test FAILED: Path validation returned false.")
                return PluginResult(
                    success=False,
                    data={"validation_status": "failed", "details": file_status},
                    error_message=f"Validation failed for path: {test_file_path}",
                )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"QA test FAILED: Could not connect to Core Systems Service. Error: {e}"
            )
            return PluginResult(
                success=False,
                error_message=f"Failed to communicate with the core systems service: {e}",
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during QA execution: {e}", exc_info=True
            )
            return PluginResult(
                success=False,
                error_message=f"An unexpected error occurred: {e}",
            )

    # These methods are required by the BasePlugin abstract class.
    # Since this plugin operates synchronously via HTTP, they don't need complex implementations.
    def get_required_tools(self) -> list:
        return []

    def handle_tool_result(self, result):
        pass

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "name": self.get_name(),
            "initialized": self.initialized,
            "service_url": self.service_url,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Returns the capabilities of the QA plugin."""
        return {
            "name": self.name,
            "description": self.description,
            "methods": {
                "run_qa_test": "Runs a quality assurance test against a specified target."
            },
        }

    def validate_input(self, method: str, data: Dict[str, Any]) -> (bool, str):
        """Validates the input for a given method."""
        if method == "execute":  # Corresponds to the main execute method
            if "test_target" in data and isinstance(data.get("test_target"), str):
                return True, ""
            return False, "Input must contain a 'test_target' string."
        return False, f"Unknown method: {method}"

    def cleanup(self):
        """Perform any cleanup, if necessary."""
        logger.info(f"Performing cleanup for {self.name}.")
        pass
