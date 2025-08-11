import logging
from typing import Dict, List

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


class ExpertAssignerAgent:
    """
    Assigns a panel of expert types for a given question and generates system messages for each using an allowed LLM.
    """

    def __init__(self, model: str = "gpt-4.1"):
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.openai_interface = OpenAIResponsesInterface()

    def assign_experts(self, question: str, context: str = "") -> List[Dict]:
        """
        Decide which expert types to assign and generate system messages for each.
        Returns a list of dicts: {expert_type, system_message}
        """
        # Always include Researcher as a permanent member
        expert_types = ["MLExpert", "StatsExpert", "EthicsExpert", "Researcher"]
        results = []
        for expert_type in expert_types:
            if expert_type == "Researcher":
                system_message = "You are a world-class research agent. Your job is to ensure accuracy, resolve disputes, and fact-check using up-to-date sources. When a fact-check is needed, pause the discussion, use the research tool, and curate findings for the group before resuming."
            else:
                system_message = f"You are a world-class expert in {expert_type}. Provide authoritative, up-to-date, and well-reasoned answers."
            results.append(
                {"expert_type": expert_type, "system_message": system_message}
            )
        return results
