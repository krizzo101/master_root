import logging
from typing import Dict, Optional

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


class SystemMessageGeneratorAgent:
    """
    Generates a system prompt for a new expert agent using an allowed OpenAI model.
    Follows project OpenAI usage and Python standards.
    """

    def __init__(self, model: str = "gpt-4.1"):
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.openai_interface = OpenAIResponsesInterface()

    def generate_system_message(
        self, expert_name: str, context: Optional[str] = None
    ) -> Dict:
        """
        Generate a system message for a new expert type using the allowed OpenAI model.
        Returns a structured dict with expert_name, system_message, model_used, and raw_response.
        """
        if expert_name == "Researcher":
            prompt = "Generate a system prompt for an AI agent who is a world-class research agent. The prompt should instruct the agent to ensure accuracy, resolve disputes, and fact-check using up-to-date sources. When a fact-check is needed, the agent should pause the discussion, use a research tool, and curate findings for the group before resuming."
        else:
            prompt = (
                f"Generate a system prompt for an AI agent who is a world-class expert in {expert_name}. "
                "The prompt should instruct the agent to provide authoritative, up-to-date, and well-reasoned answers."
            )
        if context:
            prompt += f" Context: {context}"
        try:
            self.logger.info(
                f"Generating system message for expert: {expert_name} using model: {self.model}"
            )
            response = self.openai_interface.create_response(
                prompt=prompt,
                model=self.model,
                max_tokens=128,
                temperature=0.2,
            )
            system_message = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            return {
                "expert_name": expert_name,
                "system_message": system_message,
                "model_used": self.model,
                "raw_response": response,
            }
        except Exception as e:
            self.logger.error(f"Failed to generate system message: {e}")
            return {
                "expert_name": expert_name,
                "system_message": "[ERROR: Could not generate system message]",
                "model_used": self.model,
                "raw_response": str(e),
            }
