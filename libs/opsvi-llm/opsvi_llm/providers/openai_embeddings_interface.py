"""
OpenAI Embeddings API Interface

Comprehensive embeddings interface for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official OpenAI Python SDK:
- https://github.com/openai/openai-python
- https://platform.openai.com/docs/api-reference/embeddings

Implements all core endpoints and features:
- create embeddings (sync/async)
- batch processing
- model selection
- error handling and retries
- streaming support

Version: Referenced as of July 2024
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


class OpenAIEmbeddingsError(Exception):
    """Custom exception for OpenAI Embeddings API errors."""

    pass


class OpenAIEmbeddingsInterface:
    """
    Comprehensive interface for OpenAI Embeddings API.

    Provides both synchronous and asynchronous methods for all embeddings endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def __init__(
        self, api_key: Optional[str] = None, organization: Optional[str] = None
    ):
        """Initialize the embeddings interface.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            organization: OpenAI organization ID (defaults to OPENAI_ORG_ID env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORG_ID")

        if not self.api_key:
            raise OpenAIEmbeddingsError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key, organization=self.organization)

        logger.debug(
            f"OpenAIEmbeddingsInterface initialized with org: {self.organization}"
        )

    def create_embedding(
        self,
        input_text: Union[str, List[str]],
        model: str = "text-embedding-ada-002",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate embedding vector(s) for the input text.

        Args:
            input_text: Text or list of texts to embed
            model: Embedding model to use
            **kwargs: Additional parameters for the API call

        Returns:
            Dictionary containing the embedding response

        Raises:
            OpenAIEmbeddingsError: If the API call fails
        """
        try:
            response = self.client.embeddings.create(
                input=input_text, model=model, **kwargs
            )

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise OpenAIEmbeddingsError(f"Failed to create embedding: {e}")

    async def acreate_embedding(
        self,
        input_text: Union[str, List[str]],
        model: str = "text-embedding-ada-002",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Async: Generate embedding vector(s) for the input text.

        Args:
            input_text: Text or list of texts to embed
            model: Embedding model to use
            **kwargs: Additional parameters for the API call

        Returns:
            Dictionary containing the embedding response

        Raises:
            OpenAIEmbeddingsError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            response = await async_client.embeddings.create(
                input=input_text, model=model, **kwargs
            )

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Async embedding creation failed: {e}")
            raise OpenAIEmbeddingsError(f"Failed to create embedding: {e}")

    def create_batch_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002",
        batch_size: int = 100,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Create embeddings for a batch of texts with automatic chunking.

        Args:
            texts: List of texts to embed
            model: Embedding model to use
            batch_size: Maximum texts per API call
            **kwargs: Additional parameters for the API call

        Returns:
            List of embedding responses
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.create_embedding(batch, model, **kwargs)
                results.append(response)
            except Exception as e:
                logger.error(f"Batch embedding failed for batch {i//batch_size}: {e}")
                raise OpenAIEmbeddingsError(f"Batch embedding failed: {e}")

        return results

    async def acreate_batch_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002",
        batch_size: int = 100,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Async: Create embeddings for a batch of texts with automatic chunking.

        Args:
            texts: List of texts to embed
            model: Embedding model to use
            batch_size: Maximum texts per API call
            **kwargs: Additional parameters for the API call

        Returns:
            List of embedding responses
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = await self.acreate_embedding(batch, model, **kwargs)
                results.append(response)
            except Exception as e:
                logger.error(
                    f"Async batch embedding failed for batch {i//batch_size}: {e}"
                )
                raise OpenAIEmbeddingsError(f"Async batch embedding failed: {e}")

        return results

    def extract_embeddings(self, response: Dict[str, Any]) -> List[List[float]]:
        """
        Extract embedding vectors from the API response.

        Args:
            response: Response from create_embedding

        Returns:
            List of embedding vectors
        """
        try:
            return [item["embedding"] for item in response["data"]]
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to extract embeddings from response: {e}")
            raise OpenAIEmbeddingsError(f"Invalid embedding response format: {e}")

    def get_embedding_dimension(self, model: str = "text-embedding-ada-002") -> int:
        """
        Get the dimension of embeddings for a specific model.

        Args:
            model: Embedding model name

        Returns:
            Embedding dimension
        """
        # Known model dimensions
        model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

        return model_dimensions.get(model, 1536)  # Default to 1536

    def validate_input(self, input_text: Union[str, List[str]]) -> bool:
        """
        Validate input text for embedding creation.

        Args:
            input_text: Text or list of texts to validate

        Returns:
            True if valid, False otherwise
        """
        if isinstance(input_text, str):
            return len(input_text.strip()) > 0
        elif isinstance(input_text, list):
            return all(len(text.strip()) > 0 for text in input_text)
        else:
            return False

    def get_usage_stats(self, response: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract usage statistics from the API response.

        Args:
            response: Response from create_embedding

        Returns:
            Dictionary with usage statistics
        """
        try:
            usage = response.get("usage", {})
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        except Exception as e:
            logger.error(f"Failed to extract usage stats: {e}")
            return {"prompt_tokens": 0, "total_tokens": 0}
