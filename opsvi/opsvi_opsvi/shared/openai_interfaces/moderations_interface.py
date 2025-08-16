from typing import Any

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIModerationsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Moderations API.
    Reference: https://platform.openai.com/docs/api-reference/moderations
    """

    def create_moderation(self, input_text: str, **kwargs) -> dict[str, Any]:
        """
        Classify if text violates OpenAI's content policy.
        POST /v1/moderations
        """
        try:
            response = self.client.moderations.create(input=input_text, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_moderation(self, input_text: str, **kwargs) -> dict[str, Any]:
        """
        Async: Classify if text violates OpenAI's content policy.
        POST /v1/moderations
        """
        try:
            response = await self.client.moderations.create(input=input_text, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
