from typing import Any, Dict, List

from src.shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIChatCompletionsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Chat Completions API.
    Reference: https://platform.openai.com/docs/api-reference/chat

    This interface provides both synchronous and asynchronous methods for all chat completions endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def create_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion for the provided conversation messages and parameters.
        POST /v1/chat/completions
        """
        try:
            response = self.client.chat.completions.create(messages=messages, **kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Dict[str, Any]:
        """
        Async: Create a chat completion for the provided conversation messages and parameters.
        POST /v1/chat/completions
        """
        try:
            response = await self.client.chat.completions.create(
                messages=messages, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)
