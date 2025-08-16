"""
OpenAI Models API Interface

Comprehensive models interface for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official OpenAI Python SDK:
- https://github.com/openai/openai-python
- https://platform.openai.com/docs/api-reference/models

Implements all core endpoints and features:
- list models (sync/async)
- retrieve model details
- model filtering and categorization
- error handling and retries

Version: Referenced as of July 2024
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


class OpenAIModelsError(Exception):
    """Custom exception for OpenAI Models API errors."""

    pass


@dataclass
class ModelInfo:
    """Model information structure."""

    id: str
    object: str
    created: Optional[int] = None
    owned_by: Optional[str] = None
    permission: Optional[List[Dict[str, Any]]] = None
    root: Optional[str] = None
    parent: Optional[str] = None
    context_length: Optional[int] = None
    description: Optional[str] = None


class OpenAIModelsInterface:
    """
    Comprehensive interface for OpenAI Models API.

    Provides both synchronous and asynchronous methods for all models endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def __init__(
        self, api_key: Optional[str] = None, organization: Optional[str] = None
    ):
        """Initialize the models interface.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            organization: OpenAI organization ID (defaults to OPENAI_ORG_ID env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORG_ID")

        if not self.api_key:
            raise OpenAIModelsError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key, organization=self.organization)

        logger.debug(f"OpenAIModelsInterface initialized with org: {self.organization}")

    def list_models(self) -> List[ModelInfo]:
        """
        List all available models.

        Returns:
            List of ModelInfo objects

        Raises:
            OpenAIModelsError: If the API call fails
        """
        try:
            response = self.client.models.list()

            models = []
            for model_data in response.data:
                model_info = ModelInfo(
                    id=model_data.id,
                    object=model_data.object,
                    created=getattr(model_data, "created", None),
                    owned_by=getattr(model_data, "owned_by", None),
                    permission=getattr(model_data, "permission", None),
                    root=getattr(model_data, "root", None),
                    parent=getattr(model_data, "parent", None),
                    context_length=getattr(model_data, "context_length", None),
                    description=getattr(model_data, "description", None),
                )
                models.append(model_info)

            return models

        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise OpenAIModelsError(f"Failed to list models: {e}")

    def retrieve_model(self, model_id: str) -> ModelInfo:
        """
        Retrieve a specific model by ID.

        Args:
            model_id: The model ID to retrieve

        Returns:
            ModelInfo object for the specified model

        Raises:
            OpenAIModelsError: If the API call fails
        """
        try:
            model_data = self.client.models.retrieve(model_id)

            return ModelInfo(
                id=model_data.id,
                object=model_data.object,
                created=getattr(model_data, "created", None),
                owned_by=getattr(model_data, "owned_by", None),
                permission=getattr(model_data, "permission", None),
                root=getattr(model_data, "root", None),
                parent=getattr(model_data, "parent", None),
                context_length=getattr(model_data, "context_length", None),
                description=getattr(model_data, "description", None),
            )

        except Exception as e:
            logger.error(f"Failed to retrieve model {model_id}: {e}")
            raise OpenAIModelsError(f"Failed to retrieve model {model_id}: {e}")

    async def alist_models(self) -> List[ModelInfo]:
        """
        Async: List all available models.

        Returns:
            List of ModelInfo objects

        Raises:
            OpenAIModelsError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            response = await async_client.models.list()

            models = []
            for model_data in response.data:
                model_info = ModelInfo(
                    id=model_data.id,
                    object=model_data.object,
                    created=getattr(model_data, "created", None),
                    owned_by=getattr(model_data, "owned_by", None),
                    permission=getattr(model_data, "permission", None),
                    root=getattr(model_data, "root", None),
                    parent=getattr(model_data, "parent", None),
                    context_length=getattr(model_data, "context_length", None),
                    description=getattr(model_data, "description", None),
                )
                models.append(model_info)

            return models

        except Exception as e:
            logger.error(f"Failed to list models (async): {e}")
            raise OpenAIModelsError(f"Failed to list models (async): {e}")

    async def aretrieve_model(self, model_id: str) -> ModelInfo:
        """
        Async: Retrieve a specific model by ID.

        Args:
            model_id: The model ID to retrieve

        Returns:
            ModelInfo object for the specified model

        Raises:
            OpenAIModelsError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            model_data = await async_client.models.retrieve(model_id)

            return ModelInfo(
                id=model_data.id,
                object=model_data.object,
                created=getattr(model_data, "created", None),
                owned_by=getattr(model_data, "owned_by", None),
                permission=getattr(model_data, "permission", None),
                root=getattr(model_data, "root", None),
                parent=getattr(model_data, "parent", None),
                context_length=getattr(model_data, "context_length", None),
                description=getattr(model_data, "description", None),
            )

        except Exception as e:
            logger.error(f"Failed to retrieve model {model_id} (async): {e}")
            raise OpenAIModelsError(f"Failed to retrieve model {model_id} (async): {e}")

    def get_chat_models(self) -> List[ModelInfo]:
        """
        Get only chat completion models.

        Returns:
            List of chat model ModelInfo objects
        """
        try:
            all_models = self.list_models()
            chat_models = []

            for model in all_models:
                if self._is_chat_model(model.id):
                    chat_models.append(model)

            return chat_models

        except Exception as e:
            logger.error(f"Failed to get chat models: {e}")
            raise OpenAIModelsError(f"Failed to get chat models: {e}")

    def get_embedding_models(self) -> List[ModelInfo]:
        """
        Get only embedding models.

        Returns:
            List of embedding model ModelInfo objects
        """
        try:
            all_models = self.list_models()
            embedding_models = []

            for model in all_models:
                if self._is_embedding_model(model.id):
                    embedding_models.append(model)

            return embedding_models

        except Exception as e:
            logger.error(f"Failed to get embedding models: {e}")
            raise OpenAIModelsError(f"Failed to get embedding models: {e}")

    def get_models_by_owner(self, owner: str) -> List[ModelInfo]:
        """
        Get models by owner.

        Args:
            owner: The owner to filter by

        Returns:
            List of ModelInfo objects owned by the specified owner
        """
        try:
            all_models = self.list_models()
            owned_models = []

            for model in all_models:
                if model.owned_by == owner:
                    owned_models.append(model)

            return owned_models

        except Exception as e:
            logger.error(f"Failed to get models by owner {owner}: {e}")
            raise OpenAIModelsError(f"Failed to get models by owner {owner}: {e}")

    def get_model_names(self) -> List[str]:
        """
        Get list of model names/IDs.

        Returns:
            List of model IDs
        """
        try:
            models = self.list_models()
            return [model.id for model in models]

        except Exception as e:
            logger.error(f"Failed to get model names: {e}")
            raise OpenAIModelsError(f"Failed to get model names: {e}")

    def model_exists(self, model_id: str) -> bool:
        """
        Check if a model exists.

        Args:
            model_id: The model ID to check

        Returns:
            True if the model exists, False otherwise
        """
        try:
            self.retrieve_model(model_id)
            return True
        except OpenAIModelsError:
            return False

    def _is_chat_model(self, model_id: str) -> bool:
        """
        Check if a model is a chat completion model.

        Args:
            model_id: The model ID to check

        Returns:
            True if it's a chat model, False otherwise
        """
        chat_model_prefixes = [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-vision",
            "claude",
            "o1",
            "o1-preview",
            "o3",
            "o4",
        ]

        return any(model_id.startswith(prefix) for prefix in chat_model_prefixes)

    def _is_embedding_model(self, model_id: str) -> bool:
        """
        Check if a model is an embedding model.

        Args:
            model_id: The model ID to check

        Returns:
            True if it's an embedding model, False otherwise
        """
        embedding_model_prefixes = [
            "text-embedding-",
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
        ]

        return any(model_id.startswith(prefix) for prefix in embedding_model_prefixes)

    def get_model_context_length(self, model_id: str) -> Optional[int]:
        """
        Get the context length for a specific model.

        Args:
            model_id: The model ID

        Returns:
            Context length if available, None otherwise
        """
        try:
            model_info = self.retrieve_model(model_id)
            return model_info.context_length
        except OpenAIModelsError:
            return None

    def get_available_models_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available models by category.

        Returns:
            Dictionary with model categories and counts
        """
        try:
            all_models = self.list_models()

            summary = {
                "total_models": len(all_models),
                "chat_models": len(
                    [m for m in all_models if self._is_chat_model(m.id)]
                ),
                "embedding_models": len(
                    [m for m in all_models if self._is_embedding_model(m.id)]
                ),
                "models_by_owner": {},
            }

            # Group by owner
            for model in all_models:
                owner = model.owned_by or "unknown"
                if owner not in summary["models_by_owner"]:
                    summary["models_by_owner"][owner] = 0
                summary["models_by_owner"][owner] += 1

            return summary

        except Exception as e:
            logger.error(f"Failed to get models summary: {e}")
            raise OpenAIModelsError(f"Failed to get models summary: {e}")
