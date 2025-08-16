"""
DRY MIGRATION AVAILABLE - 2025-06-24

This plugin can be significantly simplified using the new DRY infrastructure:

POTENTIAL IMPROVEMENTS:
- Use StandardPluginBase to eliminate initialization boilerplate
- Use execution_wrapper to eliminate error handling patterns  
- Use shared logging_manager to eliminate logging setup
- Use shared config_manager for configuration handling

See file_system_plugin_refactored.py for DRY implementation example.

Original implementation preserved below for backwards compatibility.
"""


# DRY ALTERNATIVE: Replace manual error handling with:
# from ...shared.plugin_execution_base import execution_wrapper
# @execution_wrapper(validate_input=True, log_execution=True)

from typing import List, Any, Optional
from pathlib import Path

from asea_orchestrator.plugins.base_plugin import BasePlugin, EventBus
from asea_orchestrator.plugins.types import (
    PluginConfig,
    ExecutionContext,
    PluginResult,
    Capability,
    ValidationResult,
)


class FileSystemPlugin(BasePlugin):
    """
    A plugin for interacting with the file system using Python's pathlib.
    """

    @staticmethod
    def get_name() -> str:
        return "file_system"

    async def initialize(
        self, config: PluginConfig, event_bus: Optional[EventBus] = None
    ) -> None:
        pass

    async def execute(self, context: ExecutionContext) -> PluginResult:
        operation = context.state.get("operation", "read")

        if operation == "create_improvement_plan":
            return await self._create_improvement_plan(context)
        elif operation == "read":
            return await self._read_file(context)
        elif operation == "write":
            return await self._write_file(context)
        elif operation == "list":
            return await self._list_directory(context)
        else:
            return PluginResult(
                success=False, data={}, error_message=f"Unknown operation: {operation}"
            )

    async def _create_improvement_plan(self, context: ExecutionContext) -> PluginResult:
        """Create a comprehensive improvement plan from analysis data."""
        try:
            improvement_data = context.state.get("improvement_data", {})
            rule_data = context.state.get("rule_data", {})
            output_file = context.state.get("output_file", "/tmp/improvement_plan.md")

            # Generate improvement plan content
            plan_content = f"""# Autonomous Agent Self-Improvement Plan
Generated: {context.state.get('timestamp', 'Unknown')}

## Analysis Summary
- Focus: {context.state.get('analysis_focus', 'General improvement')}
- Token Constraints: Premium {context.state.get('token_constraints', {}).get('premium_limit', 'Unknown')} / Efficient {context.state.get('token_constraints', {}).get('efficient_limit', 'Unknown')}

## Improvement Goals
"""

            goals = context.state.get("improvement_goals", [])
            for i, goal in enumerate(goals, 1):
                plan_content += f"{i}. {goal}\n"

            plan_content += f"""
## Identified Patterns
- Improvement opportunities: {len(improvement_data) if isinstance(improvement_data, (list, dict)) else 'Analysis pending'}
- Rule effectiveness data: {len(rule_data) if isinstance(rule_data, (list, dict)) else 'Analysis pending'}

## Implementation Recommendations
1. **Immediate Actions**: Enhance failure detection protocols
2. **Short-term**: Optimize tool orchestration patterns
3. **Medium-term**: Implement behavioral rule compliance monitoring
4. **Long-term**: Develop autonomous learning integration

## Next Steps
- Execute high-priority improvements
- Validate behavioral changes
- Measure effectiveness
- Iterate based on results
"""

            # Write plan to file
            with open(output_file, "w") as f:
                f.write(plan_content)

            return PluginResult(
                success=True,
                data={
                    "plan_file": output_file,
                    "plan_content": plan_content,
                    "recommendations": [
                        "Enhance failure detection protocols",
                        "Optimize tool orchestration patterns",
                        "Implement behavioral rule compliance monitoring",
                        "Develop autonomous learning integration",
                    ],
                },
            )

        except Exception as e:
            return PluginResult(
                success=False,
                data={},
                error_message=f"Failed to create improvement plan: {str(e)}",
            )

    async def _read_file(self, context: ExecutionContext) -> PluginResult:
        try:
            path_str = context.state.get("path")

            if not path_str:
                return PluginResult(success=False, error_message="Path not specified.")

            path = Path(path_str)

            if not path.is_file():
                return PluginResult(
                    success=False, error_message=f"File not found: {path}"
                )
            content = path.read_text()
            return PluginResult(success=True, data={"content": content})

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def _write_file(self, context: ExecutionContext) -> PluginResult:
        try:
            path_str = context.state.get("path")
            content = context.state.get("content", "")

            if not path_str:
                return PluginResult(success=False, error_message="Path not specified.")

            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return PluginResult(success=True, data={"path": str(path)})

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def _list_directory(self, context: ExecutionContext) -> PluginResult:
        try:
            path_str = context.state.get("path")

            if not path_str:
                return PluginResult(success=False, error_message="Path not specified.")

            path = Path(path_str)

            if not path.is_dir():
                return PluginResult(
                    success=False, error_message=f"Directory not found: {path}"
                )
            files = [str(p) for p in path.iterdir()]
            return PluginResult(success=True, data={"files": files})

        except Exception as e:
            return PluginResult(success=False, error_message=str(e))

    async def cleanup(self) -> None:
        pass

    def get_capabilities(self) -> List[Capability]:
        return [
            Capability(name="read", description="Reads the content of a file."),
            Capability(name="write", description="Writes content to a file."),
            Capability(name="list", description="Lists the contents of a directory."),
        ]

    def validate_input(self, input_data: Any) -> ValidationResult:
        return ValidationResult(is_valid=True, errors=[])
