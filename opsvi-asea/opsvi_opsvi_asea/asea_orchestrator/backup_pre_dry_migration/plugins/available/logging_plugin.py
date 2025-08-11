from typing import Optional

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
    Event,
)


class LoggingPlugin(BasePlugin):
    """
    A simple plugin that logs all system events to the console.
    """

    @staticmethod
    def get_name() -> str:
        return "logger"

    def __init__(self):
        self.config = None

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        self.config = config
        if event_bus:
            # Subscribe to all events
            event_bus.subscribe("workflow_started", self.on_event)
            event_bus.subscribe("step_started", self.on_event)
            event_bus.subscribe("step_completed", self.on_event)
            event_bus.subscribe("workflow_finished", self.on_event)

    async def execute(self, context: ExecutionContext) -> PluginResult:
        # This plugin doesn't have a direct execution action
        return PluginResult(success=True, data={})

    async def on_event(self, event: Event) -> None:
        print(f"  [LoggerPlugin] Event received: {event.event_type} -> {event.payload}")

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> list[Capability]:
        return []

    def validate_input(self, input_data: any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
