from asea_factory.schemas import IntegrationResult
from asea_factory.agents.base_agent import BaseAgent


class IntegrationAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Integration", config, debug)

    def run(self, artifact_ids: list) -> IntegrationResult:
        self.log_request("Integrating artifacts", {"artifact_ids": artifact_ids})

        prompt = f"Integrate and validate compatibility of artifacts: {artifact_ids}. Return a JSON object with fields: id, artifacts, integration_status, issues, recommendations."

        messages = [
            self.create_system_message(
                "You are a senior integration engineer. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            integration = IntegrationResult.parse_raw(result)
            self.log_response("Integration", response)
            return integration
        except Exception as e:
            self.handle_error("Integration", e)
