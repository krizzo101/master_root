"""ReAct pattern agent template."""

import json
from typing import Any, Dict, List

import structlog

from ..core import AgentCapability, AgentConfig, BaseAgent
from ..tools import registry as tool_registry

logger = structlog.get_logger(__name__)


class ReActAgent(BaseAgent):
    """ReAct (Reasoning and Acting) pattern agent."""

    def __init__(self, config: AgentConfig):
        """Initialize ReAct agent."""
        super().__init__(config)
        config.capabilities.append(AgentCapability.REASONING)
        config.capabilities.append(AgentCapability.TOOL_USE)
        self._logger = logger.bind(agent="ReActAgent")

    def _execute(self, prompt: str, **kwargs) -> Any:
        """Execute ReAct loop."""
        max_iterations = kwargs.get("max_iterations", self.config.max_iterations)
        thoughts = []
        actions = []
        observations = []

        for i in range(max_iterations):
            self.context.iteration = i + 1

            # Thought: Reason about the current state
            thought = self._think(prompt, thoughts, actions, observations)
            thoughts.append(thought)
            self._logger.info(f"Thought {i+1}: {thought}")

            # Check if task is complete
            if self._is_complete(thought):
                return self._format_result(thoughts, actions, observations)

            # Action: Decide what to do
            action = self._act(thought)
            actions.append(action)
            self._logger.info(f"Action {i+1}: {action}")

            # Observation: Execute action and observe result
            observation = self._observe(action)
            observations.append(observation)
            self._logger.info(f"Observation {i+1}: {observation}")

            # Create checkpoint
            if self.config.checkpoint_enabled:
                self._create_checkpoint(
                    f"iteration_{i+1}",
                    {
                        "thoughts": thoughts,
                        "actions": actions,
                        "observations": observations,
                    },
                )

        return self._format_result(thoughts, actions, observations)

    def _think(
        self,
        prompt: str,
        thoughts: List[str],
        actions: List[str],
        observations: List[str],
    ) -> str:
        """Generate a thought based on current state."""
        # In a real implementation, this would use an LLM
        # For now, return a simple thought
        if not thoughts:
            return f"I need to solve: {prompt}"
        else:
            return (
                f"Based on the last observation, I should continue working on: {prompt}"
            )

    def _act(self, thought: str) -> Dict[str, Any]:
        """Decide on an action based on thought."""
        # Parse thought to determine action
        # In real implementation, this would use LLM to decide

        # Example action format
        action = {
            "type": "tool_use",
            "tool": "search",
            "parameters": {"query": thought},
        }

        return action

    def _observe(self, action: Dict[str, Any]) -> Any:
        """Execute action and observe result."""
        action_type = action.get("type")

        if action_type == "tool_use":
            tool_name = action.get("tool")
            parameters = action.get("parameters", {})

            # Execute tool if available
            if tool_name in tool_registry:
                try:
                    result = tool_registry.execute(tool_name, **parameters)
                    return {"success": True, "result": result}
                except Exception as e:
                    return {"success": False, "error": str(e)}
            else:
                return {"success": False, "error": f"Tool {tool_name} not found"}

        elif action_type == "finish":
            return {"success": True, "result": action.get("result")}

        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    def _is_complete(self, thought: str) -> bool:
        """Check if task is complete based on thought."""
        # Simple heuristic - check for completion keywords
        completion_keywords = ["complete", "finished", "done", "solved"]
        return any(keyword in thought.lower() for keyword in completion_keywords)

    def _format_result(
        self, thoughts: List[str], actions: List[str], observations: List[str]
    ) -> Dict[str, Any]:
        """Format the final result."""
        return {
            "reasoning_steps": len(thoughts),
            "thoughts": thoughts,
            "actions": actions,
            "observations": observations,
            "final_thought": thoughts[-1] if thoughts else None,
            "final_observation": observations[-1] if observations else None,
        }
