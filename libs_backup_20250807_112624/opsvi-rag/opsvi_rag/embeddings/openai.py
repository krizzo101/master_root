"""
OpenAI embedding provider implementation.

Provides embedding generation using OpenAI's text-embedding models
with proper error handling, rate limiting, and batching support.
"""

from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI
from opsvi_foundation import CircuitBreaker, RetryExecutor, get_logger
from pydantic import Field

from .providers import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
    ProviderType,
)


class OpenAIEmbeddingConfig(EmbeddingProviderConfig):
    """Configuration for OpenAI embedding provider."""

    provider_type: ProviderType = Field(
        default=ProviderType.OPENAI, description="OpenAI provider"
    )
    api_key: str = Field(..., description="OpenAI API key")
    base_url: str | None = Field(default=None, description="OpenAI API base URL")
    organization: str | None = Field(default=None, description="OpenAI organization ID")
    model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )
    max_batch_size: int = Field(
        default=100, description="Maximum batch size for OpenAI API"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    # OpenAI-specific settings
    user: str | None = Field(
        default=None, description="User identifier for API requests"
    )
    encoding_format: str = Field(
        default="float", description="Encoding format (float or base64)"
    )

    class Config:
        extra = "allow"


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider implementation.

    Generates embeddings using OpenAI's text-embedding models with
    proper error handling, rate limiting, and batching support.
    """

    def __init__(self, config: OpenAIEmbeddingConfig, **kwargs):
        """Initialize the OpenAI embedding provider."""
        super().__init__(config, **kwargs)
        self.config = config
        self.logger = get_logger(__name__)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            organization=config.organization,
        )

        # Initialize resilience components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception,
        )

        self.retry_executor = RetryExecutor(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
        )

        # Model dimension mapping
        self._model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

        self._dimensions = self._model_dimensions.get(config.model, 1536)

    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using OpenAI API.

        Args:
            texts: List of text strings to embed
            **kwargs: Additional arguments (ignored for OpenAI)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingProviderError: If embedding generation fails
        """
        if not texts:
            return []

        # Validate batch size
        if len(texts) > self.config.max_batch_size:
            raise EmbeddingProviderError(
                f"Batch size {len(texts)} exceeds maximum {self.config.max_batch_size}"
            )

        try:
            # Use circuit breaker and retry logic
            async with self.circuit_breaker:
                embeddings = await self.retry_executor.execute(
                    self._call_openai_api,
                    texts,
                )

            return embeddings

        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise EmbeddingProviderError(f"OpenAI embedding failed: {e}") from e

    async def _call_openai_api(self, texts: list[str]) -> list[list[float]]:
        """Make the actual API call to OpenAI."""
        try:
            response = await asyncio.wait_for(
                self.client.embeddings.create(
                    model=self.config.model,
                    input=texts,
                    encoding_format=self.config.encoding_format,
                    user=self.config.user,
                ),
                timeout=self.config.timeout,
            )

            # Extract embeddings from response
            embeddings = []
            for embedding_data in response.data:
                if hasattr(embedding_data, "embedding"):
                    embeddings.append(embedding_data.embedding)
                else:
                    raise EmbeddingProviderError("Invalid response format from OpenAI")

            return embeddings

        except TimeoutError:
            raise EmbeddingProviderError(
                f"OpenAI API request timed out after {self.config.timeout}s"
            )
        except Exception as e:
            raise EmbeddingProviderError(f"OpenAI API error: {e}") from e

    async def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this provider."""
        return self._dimensions

    async def health_check(self) -> bool:
        """
        Perform a health check on the OpenAI embedding provider.

        Returns:
            True if the provider is healthy, False otherwise
        """
        try:
            # Try to generate a simple embedding
            test_embedding = await self.embed_single("test")
            return len(test_embedding) == self._dimensions
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.config.model,
            "dimensions": self._dimensions,
            "max_batch_size": self.config.max_batch_size,
            "encoding_format": self.config.encoding_format,
        }

    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Get list of supported OpenAI embedding models."""
        return [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
        ]
