from typing import List, Any, Optional
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class ControlFlowPlugin(BasePlugin):
    """
    A special plugin that enables control flow logic like loops and conditionals.
    The actual logic is handled by the Orchestrator core, which intercepts this plugin.
    This plugin acts as a marker and a placeholder for parameters.
    """

    @staticmethod
    def get_name() -> str:
        return "control_flow"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        pass

    async def execute(self, context: ExecutionContext) -> PluginResult:
        # This plugin does not execute in the traditional sense.
        # The orchestrator intercepts it and handles the logic.
        return PluginResult(success=True)

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(name="if", description="Conditional branching."),
            Capability(name="for_each", description="Looping over a list."),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
