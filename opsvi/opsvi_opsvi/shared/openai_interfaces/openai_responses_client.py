from typing import Any

from src.shared.interfaces.llm.openai_responses_interface import (
    OpenAIResponsesInterface,
)
from src.shared.logging.shared_logger import SharedLogger

ALLOWED_MODELS = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "o3",
    "o4-mini",
    "o3-mini",
]


class OpenAIResponsesClient:
    """
    Standards-compliant client for OpenAI Responses API.
    Enforces allowed models, structured output, and unified logging.
    """

    def __init__(self, api_key_env: str = "OPENAI_API_KEY"):
        self.logger = SharedLogger(name="openai_responses_client").get_logger()
        self.api = OpenAIResponsesInterface(api_key_env=api_key_env)

    def get_structured_response(
        self,
        prompt: str,
        model: str = "gpt-4.1",
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Get a structured (JSON) response from the OpenAI Responses API.
        Args:
            prompt: The user prompt.
            model: The model to use (must be in allowed list).
            tools: Optional tool definitions.
            kwargs: Additional parameters for the API.
        Returns:
            Dict with structured response fields.
        Raises:
            ValueError if model is not allowed.
        """
        if model not in ALLOWED_MODELS:
            self.logger.error(
                f"Model '{model}' is not allowed. Allowed: {ALLOWED_MODELS}"
            )
            raise ValueError(f"Model '{model}' is not allowed.")
        params = {
            "model": model,
            "input": prompt,
            "response_format": {"type": "json_object"},
        }
        if tools:
            params["tools"] = tools
        params.update(kwargs)
        self.logger.info(f"Requesting structured response: {params}")
        try:
            response = self.api.create_response(**params)
            structured = self.api.to_structured(response)
            self.logger.info(f"Structured response: {structured}")
            return {
                "id": structured.id,
                "status": structured.status,
                "output_text": structured.output_text,
                "tool_calls": structured.tool_calls,
                "function_results": structured.function_results,
            }
        except Exception as e:
            self.logger.error(f"OpenAIResponsesClient error: {e}")
            raise


# Usage example (remove or guard with __name__ == "__main__" in production)
if __name__ == "__main__":
    client = OpenAIResponsesClient()
    try:
        result = client.get_structured_response(
            prompt="What are the main differences between GPT-4 and GPT-3?",
            model="gpt-4.1",
        )
        print(result)
    except Exception as e:
        print("Error:", e)
