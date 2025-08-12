from asea_factory.schemas import DesignReviewSummary
import uuid
from asea_factory.agents.base_agent import BaseAgent


class DesignReviewAgent(BaseAgent):
    def __init__(self, config, debug=True):
        super().__init__("DesignReview", config, debug)

    def run(self, architecture_id: str) -> DesignReviewSummary:
        self.log_request(
            "Conducting design review", {"architecture_id": architecture_id}
        )

        prompt = f"Conduct a comprehensive design review for architecture: {architecture_id}. Return a JSON object with fields: id, architecture_id, summary, approval, reviewer_comments."

        messages = [
            self.create_system_message(
                "You are a senior software architect conducting design reviews. Return only valid JSON."
            ),
            self.create_user_message(prompt),
        ]

        try:
            response = self.make_request(
                messages, response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            review = DesignReviewSummary.parse_raw(result)
            self.log_response("Design review", response)
            return review
        except Exception as e:
            self.handle_error("Design review", e)
