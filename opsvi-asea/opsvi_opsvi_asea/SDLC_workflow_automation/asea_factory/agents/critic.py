from asea_factory.schemas import CriticReview
import uuid
from asea_factory.agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("Critic", config, debug)

    def run(self, artifact_ids: list) -> CriticReview:
        self.log_request(
            "Providing critique for artifacts", {"artifact_ids": artifact_ids}
        )

        prompt = f"Provide comprehensive critique and feedback for artifacts: {artifact_ids}. Return a JSON object with fields: id, artifact_id, review, issues, improvement_suggestions, iteration."

        messages = [
            self.create_system_message(
                "You are a senior code reviewer and quality assurance expert. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            feedback = CriticReview.parse_raw(result)
            self.log_response("Critique generation", response)
            return feedback
        except Exception as e:
            self.handle_error("Critique generation", e)
