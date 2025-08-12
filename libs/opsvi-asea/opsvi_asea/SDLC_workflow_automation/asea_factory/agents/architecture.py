from asea_factory.schemas import ArchitectureSpec
from typing import List, Dict, Any
import uuid
from asea_factory.agents.base_agent import BaseAgent


class ArchitectureAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Architecture", config, debug)

    def run(
        self, requirements_ids: List[str], research_ids: List[str]
    ) -> ArchitectureSpec:
        self.log_request(
            "Generating architecture for requirements and research",
            {"requirements": requirements_ids, "research": research_ids},
        )

        prompt = f"Design a system architecture for requirements: {requirements_ids} and research findings: {research_ids}. Return a JSON object with fields: id, requirements, architecture, decisions, traceability."

        messages = [
            self.create_system_message(
                "You are a software architect. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            arch = ArchitectureSpec.parse_raw(result)
            self.log_response("Architecture generation", response)
            return arch
        except Exception as e:
            self.handle_error("Architecture generation", e)
