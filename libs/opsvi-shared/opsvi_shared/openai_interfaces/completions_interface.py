from typing import Any, Dict

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAICompletionsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Completions API (legacy).
    Reference: https://platform.openai.com/docs/api-reference/completions

    This interface provides both synchronous and asynchronous methods for all completions endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def create_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Create a completion for the provided prompt and parameters.
        POST /v1/completions
        """
        try:
            response = self.client.completions.create(prompt=prompt, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a completion for the provided prompt and parameters.
        POST /v1/completions
        """
        try:
            response = await self.client.completions.create(prompt=prompt, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
