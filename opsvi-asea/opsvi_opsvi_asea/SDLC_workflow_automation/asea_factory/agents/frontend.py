from asea_factory.schemas import CodeArtifact
import uuid
from asea_factory.agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Frontend", config, debug)

    def run(self, requirements: list, architecture_id: str) -> CodeArtifact:
        self.log_request(
            "Generating frontend code",
            {"requirements": requirements, "architecture_id": architecture_id},
        )

        prompt = f"Generate production-ready frontend code for requirements: {requirements} and architecture: {architecture_id}. Return a JSON object with fields: id, type, requirements, architecture_id, code, traceability."

        messages = [
            self.create_system_message(
                "You are a senior frontend developer. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            artifact = CodeArtifact.parse_raw(result)
            self.log_response("Frontend code generation", response)
            return artifact
        except Exception as e:
            self.handle_error("Frontend code generation", e)
