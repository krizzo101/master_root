"""
OpenAI embedding provider for OPSVI RAG system.

Integrates with opsvi-llm for consistent API management, rate limiting,
and token usage tracking. Supports all OpenAI embedding models with
intelligent batching and error handling.
"""

import asyncio
from typing import Any

from opsvi_core import get_logger
from opsvi_core.exceptions import ExternalServiceError, ValidationError
from opsvi_llm.providers.openai_provider import OpenAIProvider
from pydantic import BaseModel, Field

from .base import BaseEmbeddingProvider

logger = get_logger(__name__)


class OpenAIEmbeddingConfig(BaseModel):
    """Configuration for OpenAI embedding provider."""

    model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )
    api_key: str | None = Field(None, description="OpenAI API key")
    max_batch_size: int = Field(default=100, description="Maximum texts per batch")
    dimensions: int | None = Field(
        None, description="Embedding dimensions (for v3 models)"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider using opsvi-llm integration.

    Features:
    - Leverages opsvi-llm for consistent API management
    - Automatic rate limiting and retry logic
    - Token usage tracking and optimization
    - Support for all OpenAI embedding models
    - Intelligent batching for large datasets
    """

    SUPPORTED_MODELS = {
        "text-embedding-3-small": {"dimensions": 1536, "max_tokens": 8191},
        "text-embedding-3-large": {"dimensions": 3072, "max_tokens": 8191},
        "text-embedding-ada-002": {"dimensions": 1536, "max_tokens": 8191},
    }

    def __init__(self, config: OpenAIEmbeddingConfig | None = None, **kwargs):
        """
        Initialize OpenAI embedding provider.

        Args:
            config: OpenAI embedding configuration
            **kwargs: Additional configuration options
        """
        self.config = config or OpenAIEmbeddingConfig(**kwargs)

        # Validate model support
        if self.config.model not in self.SUPPORTED_MODELS:
            raise ValidationError(f"Unsupported model: {self.config.model}")

        # Initialize with model info
        model_info = self.SUPPORTED_MODELS[self.config.model]
        super().__init__(self.config.model, **kwargs)

        # Initialize OpenAI provider from opsvi-llm
        self.openai_provider = OpenAIProvider(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        self._model_info = model_info
        logger.info(
            f"Initialized OpenAI embedding provider with model: {self.config.model}"
        )

    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using OpenAI API.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters (model, dimensions)

        Returns:
            List of embedding vectors

        Raises:
            ExternalServiceError: If OpenAI API call fails
            ValidationError: If input validation fails
        """
        if not texts:
            return []

        # Validate input
        if len(texts) > self.config.max_batch_size:
            raise ValidationError(
                f"Batch size {len(texts)} exceeds maximum {self.config.max_batch_size}"
            )

        # Get model and dimensions from kwargs or config
        model = kwargs.get("model", self.config.model)
        dimensions = kwargs.get("dimensions", self.config.dimensions)

        logger.debug(
            f"Generating embeddings for {len(texts)} texts using model: {model}"
        )

        try:
            # Prepare embedding request
            embedding_params = {
                "input": texts,
                "model": model,
            }

            # Add dimensions for v3 models
            if dimensions and model.startswith("text-embedding-3"):
                embedding_params["dimensions"] = dimensions

            # Use opsvi-llm OpenAI provider for the API call
            async with self.openai_provider.client.with_options(
                timeout=self.config.timeout
            ) as client:
                response = await client.embeddings.create(**embedding_params)

            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]

            logger.debug(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            error_msg = f"OpenAI embedding generation failed: {e}"
            logger.error(error_msg)
            raise ExternalServiceError(error_msg) from e

    async def embed_texts_batched(
        self, texts: list[str], batch_size: int | None = None
    ) -> list[list[float]]:
        """
        Generate embeddings with automatic batching for large datasets.

        Args:
            texts: List of texts to embed
            batch_size: Custom batch size (defaults to config max_batch_size)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        batch_size = min(
            batch_size or self.config.max_batch_size, self.config.max_batch_size
        )

        if len(texts) <= batch_size:
            return await self.embed_texts(texts)

        logger.info(f"Processing {len(texts)} texts in batches of {batch_size}")

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self.embed_texts(batch)
            all_embeddings.extend(batch_embeddings)

            # Add small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    async def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for the current model.

        Returns:
            Number of dimensions in embeddings
        """
        if self.config.dimensions and self.config.model.startswith("text-embedding-3"):
            return self.config.dimensions
        return self._model_info["dimensions"]

    async def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible and the model is available.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Test with minimal input
            test_embeddings = await self.embed_texts(["health check"])
            return len(test_embeddings) == 1 and len(test_embeddings[0]) > 0

        except Exception as e:
            logger.warning(f"OpenAI embedding provider health check failed: {e}")
            return False

    def get_max_batch_size(self) -> int:
        """
        Get maximum supported batch size for this provider.

        Returns:
            Maximum number of texts per batch
        """
        return self.config.max_batch_size

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the current embedding model.

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.config.model,
            "dimensions": self._model_info["dimensions"],
            "max_tokens": self._model_info["max_tokens"],
            "configurable_dimensions": self.config.model.startswith("text-embedding-3"),
            "current_dimensions": self.config.dimensions
            or self._model_info["dimensions"],
        }

    async def estimate_cost(self, texts: list[str]) -> dict[str, Any]:
        """
        Estimate the cost for embedding the given texts.

        Args:
            texts: List of texts to estimate cost for

        Returns:
            Dictionary with cost estimation
        """
        # Rough token estimation (actual tokenization would be more accurate)
        total_chars = sum(len(text) for text in texts)
        estimated_tokens = total_chars // 4  # Rough approximation

        # OpenAI pricing (as of 2025) - should be configurable
        pricing_per_1k_tokens = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.00010,
        }

        price_per_1k = pricing_per_1k_tokens.get(self.config.model, 0.0001)
        estimated_cost = (estimated_tokens / 1000) * price_per_1k

        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
            "model": self.config.model,
            "text_count": len(texts),
        }
