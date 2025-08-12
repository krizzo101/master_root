"""
ASEA Plugin Adapter for LangGraph Integration

This module provides the ASEAPluginNode class that wraps existing ASEA plugins
to work as LangGraph nodes while preserving all existing functionality.
"""

import time
from typing import Dict, Any, Optional

from ..plugins.base_plugin import BasePlugin
from .state import ASEAState, update_state_for_plugin


class TemplateEngine:
    """
    Template engine for processing ASEA workflow input/output mappings.

    Handles template strings like "{{ workflow.input.user_prompt }}" and
    "{{ plugin_outputs.cognitive_pre_analysis.enhanced_understanding }}"
    """

    @staticmethod
    def render_template(template: str, context: Dict[str, Any]) -> Any:
        """
        Render a template string using the provided context.

        Args:
            template: Template string with {{ }} placeholders
            context: Context data for template rendering

        Returns:
            Rendered value (string, dict, list, etc.)
        """
        if not isinstance(template, str):
            return template

        if not template.startswith("{{") or not template.endswith("}}"):
            return template

        # Extract the path from {{ path }}
        path = template.strip("{{ }}")

        # Navigate the context using dot notation
        return TemplateEngine._get_nested_value(context, path)

    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """
        Get nested value from data using dot notation path.

        Args:
            data: Data dictionary to navigate
            path: Dot-separated path like "workflow.input.user_prompt"

        Returns:
            Value at the specified path, or None if not found
        """
        try:
            parts = path.split(".")
            current = data

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None

            return current
        except (KeyError, TypeError, AttributeError):
            return None


class ASEAPluginNode:
    """
    LangGraph node adapter for ASEA plugins.

    This class wraps existing ASEA plugins to work as LangGraph nodes,
    preserving all existing functionality while adding LangGraph capabilities.
    """

    def __init__(
        self,
        plugin: BasePlugin,
        input_mapping: Dict[str, str],
        output_mapping: Dict[str, str],
        plugin_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the plugin adapter.

        Args:
            plugin: The ASEA plugin instance to wrap
            input_mapping: Maps plugin parameters to state values
            output_mapping: Maps plugin outputs to state keys
            plugin_config: Additional configuration for the plugin
        """
        self.plugin = plugin
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.plugin_config = plugin_config or {}
        self.plugin_name = plugin.__class__.__name__.replace("Plugin", "").lower()

    def __call__(self, state: ASEAState) -> ASEAState:
        """
        Execute the plugin as a LangGraph node.

        Args:
            state: Current workflow state

        Returns:
            Updated state with plugin results
        """
        start_time = time.time()

        try:
            # Prepare plugin parameters using template engine
            plugin_params = self._prepare_plugin_parameters(state)

            # Execute the plugin using existing ASEA interface
            # Handle both sync and async execute methods
            import asyncio
            from ..plugins.types import ExecutionContext

            # Create execution context
            execution_context = ExecutionContext(
                workflow_id="langgraph_workflow",
                task_id=f"{self.plugin_name}_{int(time.time())}",
                state=plugin_params,
            )

            if asyncio.iscoroutinefunction(self.plugin.execute):
                plugin_result = asyncio.run(self.plugin.execute(execution_context))
                plugin_output = (
                    plugin_result.data
                    if plugin_result.success
                    else {"error": plugin_result.error_message}
                )
            else:
                plugin_output = self.plugin.execute(plugin_params)

            # Update state with plugin results
            execution_time = time.time() - start_time
            new_state = update_state_for_plugin(
                state=state,
                plugin_name=self.plugin_name,
                plugin_output=plugin_output,
                execution_time=execution_time,
                metadata={
                    "plugin_class": self.plugin.__class__.__name__,
                    "input_mapping": self.input_mapping,
                    "output_mapping": self.output_mapping,
                    "success": True,
                },
            )

            # Apply output mapping to workflow state
            new_state = self._apply_output_mapping(new_state, plugin_output)

            return new_state

        except Exception as e:
            # Handle errors gracefully
            execution_time = time.time() - start_time
            error_message = f"Plugin {self.plugin_name} failed: {str(e)}"

            new_state = state.copy()
            new_state["errors"].append(error_message)
            new_state["step_timings"][self.plugin_name] = execution_time
            new_state["plugin_metadata"][self.plugin_name] = {
                "plugin_class": self.plugin.__class__.__name__,
                "success": False,
                "error": error_message,
            }

            return new_state

    def _prepare_plugin_parameters(self, state: ASEAState) -> Dict[str, Any]:
        """
        Prepare plugin parameters using input mapping and template engine.

        Args:
            state: Current workflow state

        Returns:
            Parameters dictionary for plugin execution
        """
        params = {}

        # Create template context from state
        template_context = {
            "workflow": {
                "input": state["workflow_state"],
                "state": state["workflow_state"],
            },
            "plugin_outputs": state["plugin_outputs"],
            "execution_context": state["execution_context"],
            "cognitive_metadata": state["cognitive_metadata"],
        }

        # Apply input mapping using template engine
        for param_name, template in self.input_mapping.items():
            rendered_value = TemplateEngine.render_template(template, template_context)
            if rendered_value is not None:
                params[param_name] = rendered_value

        # Add any additional configuration
        params.update(self.plugin_config)

        return params

    def _apply_output_mapping(self, state: ASEAState, plugin_output: Any) -> ASEAState:
        """
        Apply output mapping to update workflow state.

        Args:
            state: Current workflow state
            plugin_output: Output from plugin execution

        Returns:
            Updated state with output mapping applied
        """
        new_state = state.copy()

        # If plugin output is a dictionary, apply individual mappings
        if isinstance(plugin_output, dict):
            for output_key, state_key in self.output_mapping.items():
                if output_key in plugin_output:
                    # Update workflow state directly
                    new_state["workflow_state"][state_key] = plugin_output[output_key]
        else:
            # If plugin output is not a dict, use the first output mapping
            if self.output_mapping:
                first_state_key = list(self.output_mapping.values())[0]
                new_state["workflow_state"][first_state_key] = plugin_output

        return new_state


def create_plugin_node(
    plugin_class: type,
    input_mapping: Dict[str, str],
    output_mapping: Dict[str, str],
    plugin_config: Optional[Dict[str, Any]] = None,
) -> ASEAPluginNode:
    """
    Factory function to create an ASEA plugin node.

    Args:
        plugin_class: Class of the ASEA plugin to wrap
        input_mapping: Maps plugin parameters to state values
        output_mapping: Maps plugin outputs to state keys
        plugin_config: Additional configuration for the plugin

    Returns:
        Configured ASEAPluginNode ready for use in LangGraph
    """
    from ..plugins.types import PluginConfig

    plugin_instance = plugin_class()

    # Create plugin config for initialization
    config = PluginConfig(name=plugin_class.get_name(), config=plugin_config or {})

    # Initialize plugin (some plugins need async, handle both)
    import asyncio

    try:
        if asyncio.iscoroutinefunction(plugin_instance.initialize):
            asyncio.run(plugin_instance.initialize(config))
        else:
            plugin_instance.initialize(config)
    except Exception as e:
        print(f"Warning: Plugin initialization failed: {e}")
        # Continue anyway for compatibility

    return ASEAPluginNode(
        plugin=plugin_instance,
        input_mapping=input_mapping,
        output_mapping=output_mapping,
        plugin_config=plugin_config,
    )
