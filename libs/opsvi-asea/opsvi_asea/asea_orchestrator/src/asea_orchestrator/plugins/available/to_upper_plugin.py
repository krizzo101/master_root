"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See to_upper_plugin_refactored.py for DRY implementation example.

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


class ToUpperPlugin(BasePlugin):
    """
    A simple plugin to convert a string to uppercase.
    """

    @staticmethod
    def get_name() -> str:
        return "to_upper"

    def __init__(self):
        self.config = None

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        self.config = config

    async def execute(self, context: ExecutionContext) -> PluginResult:
        text = context.state.get("text")
        if not isinstance(text, str):
            return PluginResult(
                success=False,
                data={},
                error_message="Input 'text' must be a string.",
            )

        result = text.upper()
        return PluginResult(success=True, data={"result": result})

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(name="to_upper", description="Converts a string to uppercase.")
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
