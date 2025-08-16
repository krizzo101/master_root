from asea_factory.schemas import ResearchFinding
from asea_factory.agents.base_agent import BaseAgent
from typing import List


class ResearchAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Research", config, debug)

    def run(self, queries: List[str]) -> List[ResearchFinding]:
        findings = []
        for query in queries:
            self.log_request("Researching", query)

            messages = [
                self.create_system_message(
                    "You are a research assistant. Return a JSON object with fields: id, query, summary, sources, related_requirements. Only output valid JSON."
                ),
                self.create_user_message(query),
            ]

            try:
                response = self.make_request(
                    messages, response_format={"type": "json_object"}
                )
                result = response.choices[0].message.content
                finding = ResearchFinding.parse_raw(result)
                findings.append(finding)
                self.log_response("Research", response)
            except Exception as e:
                self.handle_error("Research", e)

        return findings
