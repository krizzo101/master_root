"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See hello_world_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""

from typing import List, Any, Optional


# Forward declaration
class EventBus:
    pass


from asea_orchestrator.plugins.base_plugin import BasePlugin
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class HelloWorldPlugin(BasePlugin):
    """
    A simple example plugin that prints 'Hello, World!'.
    """

    @staticmethod
    def get_name() -> str:
        return "hello_world"

    def __init__(self):
        self.config = None

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        """Initializes the plugin."""
        self.config = config
        print(f"HelloWorldPlugin initialized with config: {config.name}")

    async def execute(self, context: ExecutionContext) -> PluginResult:
        """Executes the plugin's main logic."""
        # Get the name from the context state (mapped from workflow inputs)
        name = context.state.get("name", "World")

        # Get the prefix from the plugin config
        prefix = self.config.config.get("prefix", "Hello") if self.config else "Hello"

        # Create the greeting message
        greeting_message = f"{prefix} {name}"

        print(f"HelloWorldPlugin: {greeting_message}")

        # Return with 'greeting' key as expected by the workflow
        return PluginResult(success=True, data={"greeting": greeting_message})

    def execute_sync(self, context: ExecutionContext) -> PluginResult:
        """Synchronous version of execute for Celery workers."""
        # Get the name from the context state (mapped from workflow inputs)
        name = context.state.get("name", "World")

        # Get the prefix from the plugin config
        prefix = self.config.config.get("prefix", "Hello") if self.config else "Hello"

        # Create the greeting message
        greeting_message = f"{prefix} {name}"

        print(f"HelloWorldPlugin: {greeting_message}")

        # Return with 'greeting' key as expected by the workflow
        return PluginResult(success=True, data={"greeting": greeting_message})

    async def cleanup(self) -> None:
        """Cleans up resources."""
        print("HelloWorldPlugin cleaned up.")

    def get_capabilities(self) -> List[Capability]:
        """Gets the plugin's capabilities."""
        return [
            Capability(name="say_hello", description="Prints a hello world message.")
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validates input data."""
        return ValidationResult(is_valid=True, errors=[])
