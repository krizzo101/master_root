from typing import List

from shared.openai_interfaces.base import OpenAIBaseInterface
from shared.openai_interfaces.types import ModelInfo


class OpenAIModelsInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Models API.
    Reference: https://platform.openai.com/docs/api-reference/models

    This interface provides both synchronous and asynchronous methods for all models endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def list_models(self) -> List[ModelInfo]:
        """
        List all available models.
        GET /v1/models
        """
        try:
            models = self.client.models.list()
            return [ModelInfo(**m) for m in models["data"]]
        except Exception as e:
            self._handle_error(e)

    def retrieve_model(self, model_id: str) -> ModelInfo:
        """
        Retrieve a specific model by ID.
        GET /v1/models/{model}
        """
        try:
            model = self.client.models.retrieve(model_id)
            return ModelInfo(**model)
        except Exception as e:
            self._handle_error(e)

    async def alist_models(self) -> List[ModelInfo]:
        """
        Async: List all available models.
        GET /v1/models
        """
        try:
            models = await self.client.models.alist()
            return [ModelInfo(**m) for m in models["data"]]
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_model(self, model_id: str) -> ModelInfo:
        """
        Async: Retrieve a specific model by ID.
        GET /v1/models/{model}
        """
        try:
            model = await self.client.models.aretrieve(model_id)
            return ModelInfo(**model)
        except Exception as e:
            self._handle_error(e)
