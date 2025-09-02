"""
Specialized Agent Module

This module implements the Specialized Agent that is dynamically created
by the Dynamic Agent Proxy, optimized for specific user prompts.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ..communication import call_openai_api
from ..utils.exceptions import APICallError, SpecializedAgentError
from .agent_base import AgentBase


class SpecializedAgent(AgentBase):
    """
    Specialized agent created and configured by the Dynamic Agent Proxy.
    Each instance is optimized for a specific prompt/task based on analysis.
    """

    def __init__(self, agent_config: Dict[str, Any]) -> None:
        """
        Initialize the specialized agent with the provided configuration.

        Args:
            agent_config: Complete agent configuration including system message,
                          model parameters, and contextual data
        """
        super().__init__()
        self.agent_config = agent_config
        self.agent_id = agent_config["agent_id"]
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            "Specialized agent %s initialized for domain: %s, intent: %s",
            self.agent_id,
            agent_config["prompt_analysis"].get("primary_domain", "unknown"),
            agent_config["prompt_analysis"].get("intent_classification", "unknown"),
        )

    def process(
        self, prompt: str, conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user prompt using the specialized configuration.

        Args:
            prompt: The user's prompt
            conversation_history: Previous conversation turns

        Returns:
            The response from the API

        Raises:
            APICallError: If the API call fails
            SpecializedAgentError: If processing fails for other reasons
        """
        start_time = time.time()

        try:
            # Extract configuration parameters
            config = self.agent_config["agent_configuration"]
            system_message = config["system_message"]
            model = config["model"]
            temperature = config["temperature"]
            max_tokens = config["max_tokens"]

            # Call the OpenAI API with the configured parameters
            response = call_openai_api(
                prompt=prompt,
                system_message=system_message,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=config.get("top_p", 1.0),
                frequency_penalty=config.get("frequency_penalty", 0.0),
                presence_penalty=config.get("presence_penalty", 0.0),
                stop=config.get("stop", None),
                conversation_history=conversation_history,
            )

            # Update performance metrics
            elapsed_time = time.time() - start_time
            self.agent_config["performance_metrics"]["response_time"] = elapsed_time

            if "usage" in response:
                self.agent_config["performance_metrics"]["token_usage"] = {
                    "prompt": response["usage"].get("prompt_tokens", 0),
                    "completion": response["usage"].get("completion_tokens", 0),
                    "total": response["usage"].get("total_tokens", 0),
                }

            # Log the interaction
            self.logger.info(
                "Specialized agent %s processed prompt in %.2f seconds with %d total tokens",
                self.agent_id,
                elapsed_time,
                self.agent_config["performance_metrics"]["token_usage"].get("total", 0),
            )

            return response

        except APICallError as e:
            self.logger.error("API call failed: %s", str(e))
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error in specialized agent: %s", str(e), exc_info=True
            )
            raise SpecializedAgentError(f"Failed to process prompt: {str(e)}")

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this specialized agent.

        Returns:
            Dictionary with agent information
        """
        return {
            "agent_id": self.agent_id,
            "creation_time": self.agent_config.get("creation_timestamp"),
            "primary_domain": self.agent_config["prompt_analysis"].get(
                "primary_domain"
            ),
            "intent": self.agent_config["prompt_analysis"].get("intent_classification"),
            "complexity": self.agent_config["prompt_analysis"].get("complexity_level"),
            "model": self.agent_config["agent_configuration"].get("model"),
            "temperature": self.agent_config["agent_configuration"].get("temperature"),
            "evolution_history": [
                {
                    "type": entry.get("modification_type"),
                    "reason": entry.get("modification_reason"),
                }
                for entry in self.agent_config.get("evolution_history", [])
            ],
        }
