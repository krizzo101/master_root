"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See code_analysis_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)

from typing import List, Any, Optional
import re
from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class CodeAnalysisPlugin(BasePlugin):
    """
    A simple plugin to analyze Python code for basic metrics.
    """

    @staticmethod
    def get_name() -> str:
        return "code_analysis"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        pass

    async def execute(self, context: ExecutionContext) -> PluginResult:
        try:
            code = context.state.get("code_content")
            if not code:
                return PluginResult(
                    success=False, error_message="Code content not found in context."
                )

            lines = code.splitlines()
            line_count = len(lines)
            class_count = len(re.findall(r"^class\s+\w+", code, re.MULTILINE))
            func_count = len(re.findall(r"^def\s+\w+", code, re.MULTILINE))

            analysis = {
                "line_count": line_count,
                "class_count": class_count,
                "function_count": func_count,
            }

            return PluginResult(success=True, data={"analysis_result": analysis})

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(
                name="analyze_code",
                description="Analyzes a string of Python code for metrics.",
            )
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
