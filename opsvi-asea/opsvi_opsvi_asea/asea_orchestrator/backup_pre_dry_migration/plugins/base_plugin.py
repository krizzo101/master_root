from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
import asyncio

from .types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
    HealthStatus,
)
from ..event_bus import EventBus
from .ai_mixin import AIMixin, shared_ai_manager


class BasePlugin(AIMixin, ABC):
    """
    Abstract base class for all plugins.
    Includes AI capabilities through AIMixin for structured responses.
    """

    def __init__(self):
        super().__init__()  # Initialize AIMixin
        self.event_bus: Optional[EventBus] = None

    @classmethod
    def get_name(cls) -> str:
        """
        Returns the snake_case name of the plugin from its class name.
        e.g., MyPlugin -> my_plugin
        """
        return (
            re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower().replace("_plugin", "")
        )

    async def initialize(self, config: PluginConfig, event_bus: Optional[EventBus]):
        """
        Initializes the plugin with its configuration.
        This method is called once when the plugin is loaded.
        """
        self.event_bus = event_bus

        # Initialize AI capabilities if API key is available
        api_key = config.config.get("openai_api_key") or shared_ai_manager.api_key
        if api_key:
            ai_config = config.config.get("ai_config", shared_ai_manager.get_config())
            self.initialize_ai_client(api_key, ai_config)
            print(f"AI client initialized for plugin: {self.get_name()}")
        else:
            print(
                f"Warning: AI client not initialized for plugin {self.get_name()} - no API key available"
            )

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> PluginResult:
        """
        Executes the plugin's main logic.
        """
        pass

    def initialize_sync(self, config: PluginConfig, event_bus: Optional[EventBus]):
        """Synchronous version of initialize for Celery workers."""
        asyncio.run(self.initialize(config, event_bus))

    def execute_sync(self, context: ExecutionContext) -> PluginResult:
        """Synchronous version of execute for Celery workers."""
        return asyncio.run(self.execute(context))

    async def on_event(self, event_name: str, data: Dict[str, Any]):
        """
        Handles events from the event bus.
        """
        pass

    @staticmethod
    def get_dependencies() -> List[str]:
        """
        Returns a list of external dependencies required by the plugin.
        """
        return []

    @staticmethod
    def get_configuration_schema() -> Dict[str, Any]:
        """
        Returns a JSON schema for the plugin's configuration.
        """
        return {}

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleans up any resources used by the plugin.
        This method is called once when the plugin is unloaded.
        """
        # Cleanup AI client resources
        await self.cleanup_ai_client()

    @abstractmethod
    def get_capabilities(self) -> List[Capability]:
        """
        Returns a list of capabilities that this plugin provides.
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Any) -> ValidationResult:
        """
        Validates the input data for the plugin's execute method.
        """
        pass

    # Optional methods with default implementations

    def health_check(self) -> HealthStatus:
        """
        Performs a health check on the plugin.
        """
        return HealthStatus(status="OK", details="Plugin is healthy.")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Returns a dictionary of metrics for the plugin.
        """
        return {}
