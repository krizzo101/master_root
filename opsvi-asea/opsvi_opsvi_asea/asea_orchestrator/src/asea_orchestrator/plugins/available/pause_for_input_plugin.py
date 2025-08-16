"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See pause_for_input_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""

from typing import Optional, List, Any
import asyncio

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
    Event,
)


class PauseForInputPlugin(BasePlugin):
    """
    A plugin that pauses workflow execution and waits for human input.
    """

    @staticmethod
    def get_name() -> str:
        return "pause_for_input"

    def __init__(self):
        self.config = None
        self.event_bus: Optional[EventBus] = None
        self.input_received_event: Optional[asyncio.Event] = None
        self.received_data: Any = None

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        self.config = config
        self.event_bus = event_bus
        if self.event_bus:
            # Listen for the specific event that will provide the input
            self.event_bus.subscribe("input_received", self.on_input_received)

    async def execute(self, context: ExecutionContext) -> PluginResult:
        prompt = context.state.get("prompt", "Please provide input:")

        # Create an asyncio.Event for this specific execution
        self.input_received_event = asyncio.Event()

        # Publish the event asking for input
        await self.event_bus.publish("waiting_for_input", {"prompt": prompt})

        # Wait until the on_input_received handler sets the event
        await self.input_received_event.wait()

        return PluginResult(success=True, data={"human_input": self.received_data})

    async def on_input_received(self, event: Event) -> None:
        """Handles the event that provides the required input."""
        if self.input_received_event and not self.input_received_event.is_set():
            self.received_data = event.payload.get("data")
            self.input_received_event.set()
            print("  [PausePlugin] Input received, resuming workflow.")

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(name="pause", description="Pauses workflow for human input.")
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
