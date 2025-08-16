from typing import Any, Dict

from openai import OpenAI

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIEmbeddingsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Embeddings API (openai>=1.0.0).
    Reference: https://platform.openai.com/docs/api-reference/embeddings

    This interface provides both synchronous and asynchronous methods for all embeddings endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = OpenAI()

    def create_embedding(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Generate an embedding vector for the input text.
        POST /v1/embeddings
        """
        try:
            response = self.client.embeddings.create(input=input_text, **kwargs)
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else dict(response)
            )
        except Exception as e:
            self._handle_error(e)

    async def acreate_embedding(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Async: Generate an embedding vector for the input text.
        POST /v1/embeddings
        """
        try:
            response = await self.client.embeddings.create(input=input_text, **kwargs)
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else dict(response)
            )
        except Exception as e:
            self._handle_error(e)
