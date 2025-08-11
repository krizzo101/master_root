from typing import List, Any, Optional
from duckduckgo_search import DDGS

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class WebSearchPlugin(BasePlugin):
    """
    A plugin for performing web searches using DuckDuckGo.
    """

    @staticmethod
    def get_name() -> str:
        return "web_search"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        pass

    async def execute(self, context: ExecutionContext) -> PluginResult:
        try:
            query = context.state.get("query")
            max_results = context.state.get("max_results", 5)
            # Default to 0, which means no truncation.
            max_characters = context.state.get("max_characters", 0)

            if not query:
                return PluginResult(
                    success=False, error_message="Search query not specified."
                )

            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(keywords=query, max_results=max_results):
                    # Only truncate if max_characters is set to a positive integer
                    if max_characters and len(r.get("body", "")) > max_characters:
                        r["body"] = r["body"][:max_characters] + "..."
                    results.append(r)

            return PluginResult(success=True, data={"search_results": results})

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="web_search", description="Performs a web search using DuckDuckGo."
            )
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
