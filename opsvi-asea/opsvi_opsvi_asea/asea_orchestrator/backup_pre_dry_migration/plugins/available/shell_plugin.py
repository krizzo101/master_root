from typing import List, Any, Optional
import subprocess

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class ShellPlugin(BasePlugin):
    """
    A plugin for executing shell commands using Python's subprocess module.
    """

    @staticmethod
    def get_name() -> str:
        return "shell"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        pass

    async def execute(self, context: ExecutionContext) -> PluginResult:
        try:
            command = context.state.get("command")

            if not command:
                return PluginResult(
                    success=False,
                    error_message="Command not specified in context state.",
                )

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,  # We will check the return code manually
            )

            return PluginResult(
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [Capability(name="run_command", description="Executes a shell command.")]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
