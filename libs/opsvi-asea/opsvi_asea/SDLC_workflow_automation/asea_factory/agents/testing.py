from asea_factory.schemas import TestSuite
from asea_factory.agents.base_agent import BaseAgent


class TestingAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Testing", config, debug)

    def run(self, artifact_ids: list) -> TestSuite:
        self.log_request(
            "Generating tests for artifacts", {"artifact_ids": artifact_ids}
        )

        prompt = f"Generate comprehensive tests for artifacts: {artifact_ids}. Return a JSON object with fields: id, artifact_id, requirements, tests, results."

        messages = [
            self.create_system_message(
                "You are a senior QA engineer and test automation expert. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            test = TestSuite.parse_raw(result)
            self.log_response("Test generation", response)
            return test
        except Exception as e:
            self.handle_error("Test generation", e)
