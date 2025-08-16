from asea_factory.schemas import DocumentationArtifact
from asea_factory.agents.base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Documentation", config, debug)

    def run(self, artifact_ids: list) -> DocumentationArtifact:
        self.log_request(
            "Generating documentation for artifacts", {"artifact_ids": artifact_ids}
        )

        prompt = f"Generate comprehensive documentation for artifacts: {artifact_ids}. Return a JSON object with fields: id, artifact_id, content, doc_type, version."

        messages = [
            self.create_system_message(
                "You are a technical writer creating comprehensive documentation. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            doc = DocumentationArtifact.parse_raw(result)
            self.log_response("Documentation generation", response)
            return doc
        except Exception as e:
            self.handle_error("Documentation generation", e)
