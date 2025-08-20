"""Tool-using agent template."""

from typing import Any, Dict, List, Optional

import structlog

from ..core import AgentCapability, AgentConfig, BaseAgent
from ..tools import registry as tool_registry

logger = structlog.get_logger(__name__)


class ToolAgent(BaseAgent):
    """Agent specialized in using tools."""

    def __init__(self, config: AgentConfig):
        """Initialize tool agent."""
        super().__init__(config)
        config.capabilities.append(AgentCapability.TOOL_USE)
        self._logger = logger.bind(agent="ToolAgent")
        self._tool_history: List[Dict[str, Any]] = []

    def _execute(self, prompt: str, **kwargs) -> Any:
        """Execute with tool usage."""
        # Parse prompt to identify required tools
        required_tools = self._identify_tools(prompt)

        if not required_tools:
            return {"error": "No tools identified for this task"}

        results = {}

        for tool_name in required_tools:
            # Get tool parameters from prompt
            parameters = self._extract_parameters(prompt, tool_name)

            # Execute tool
            try:
                result = self._execute_tool(tool_name, parameters)
                results[tool_name] = result

                # Record in history
                self._tool_history.append(
                    {
                        "tool": tool_name,
                        "parameters": parameters,
                        "result": result,
                        "success": True,
                    }
                )

            except Exception as e:
                self._logger.error(f"Tool execution failed: {tool_name}", error=str(e))
                results[tool_name] = {"error": str(e)}

                self._tool_history.append(
                    {
                        "tool": tool_name,
                        "parameters": parameters,
                        "error": str(e),
                        "success": False,
                    }
                )

        # Combine results
        return self._combine_results(results)

    def _identify_tools(self, prompt: str) -> List[str]:
        """Identify which tools to use based on prompt."""
        # In real implementation, use LLM to identify tools
        # For now, return available tools that might be relevant

        available_tools = tool_registry.list_tools()

        # Simple keyword matching
        identified = []
        prompt_lower = prompt.lower()

        for tool in available_tools:
            tool_def = tool_registry.get(tool)
            if tool_def:
                # Check if tool description matches prompt
                if any(word in prompt_lower for word in tool.lower().split("_")):
                    identified.append(tool)

        return identified

    def _extract_parameters(self, prompt: str, tool_name: str) -> Dict[str, Any]:
        """Extract tool parameters from prompt."""
        # In real implementation, use LLM to extract parameters
        # For now, return empty dict

        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return {}

        parameters = {}

        # Try to extract values for required parameters
        for param in tool_def.required:
            # Simple extraction logic - would use LLM in practice
            parameters[param] = f"extracted_{param}_from_prompt"

        return parameters

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a single tool."""
        if tool_name not in tool_registry:
            raise ValueError(f"Tool not found: {tool_name}")

        return tool_registry.execute(tool_name, **parameters)

    def _combine_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from multiple tools."""
        # In real implementation, use LLM to synthesize results

        successful_tools = [k for k, v in results.items() if "error" not in v]
        failed_tools = [k for k, v in results.items() if "error" in v]

        return {
            "tools_executed": len(results),
            "successful": len(successful_tools),
            "failed": len(failed_tools),
            "results": results,
            "tool_history": self._tool_history,
        }

    def register_tool_suite(self, suite_name: str) -> None:
        """Register a suite of related tools."""
        # Get all tools in a category
        tools = tool_registry.list_tools(category=suite_name)

        for tool_name in tools:
            tool_def = tool_registry.get(tool_name)
            if tool_def:
                self.register_tool(tool_name, tool_def.func)

        self._logger.info(f"Registered tool suite: {suite_name} ({len(tools)} tools)")
