import sys
import os
from typing import Any

# This import strategy is based on the assumption that the top-level 'src'
# directory is on the Python path when the plugin is loaded.
from asea_orchestrator.plugins.base_plugin import BasePlugin
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)

# This plugin is for testing workflow resumption after a crash.
# It simulates a failure during a specific execution attempt.


class CrashablePlugin(BasePlugin):
    """
    A plugin that can be configured to fail on a specific execution count.
    This is used to test the orchestrator's ability to resume a failed workflow.
    """

    @staticmethod
    def get_name() -> str:
        return "crashable_plugin"

    async def initialize(self, config: PluginConfig, event_bus=None):
        await super().initialize(config, event_bus)
        self.config = config.config
        self.run_id = self.config.get("run_id", "default_run")
        self.crash_on_attempt = self.config.get("crash_on_attempt", -1)

        # Use a file-based counter to persist state across plugin instances
        self.counter_file = f"/tmp/crashable_plugin_{self.run_id}.count"

        if not os.path.exists(self.counter_file):
            with open(self.counter_file, "w") as f:
                f.write("0")

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """
        Execute the plugin. Will crash on the first attempt, succeed on subsequent attempts.
        """
        run_id = context.workflow_id

        # Track attempt count using a fixed key name for proper output mapping
        attempt_key = "crashable_attempt_count"
        current_attempt = context.state.get(attempt_key, 0) + 1

        # Set tracking information in the result
        result_data = {
            "crashable_plugin_ran_at_attempt": current_attempt,
            "crashable_attempt_count": current_attempt,
        }

        if current_attempt == 1:
            # First attempt: simulate crash
            return PluginResult(
                success=False,
                data=result_data,
                error_message=f"Simulated crash for run {run_id} on attempt {current_attempt}",
            )
        else:
            # Subsequent attempts: succeed
            result_data["message"] = f"Success on attempt {current_attempt}"
            return PluginResult(success=True, data=result_data)

    async def cleanup(self) -> None:
        """Cleans up resources used by the plugin."""
        pass

    def get_capabilities(self) -> list[Capability]:
        """Returns the capabilities of this plugin."""
        return []

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validates the input data for the plugin."""
        return ValidationResult(is_valid=True)
