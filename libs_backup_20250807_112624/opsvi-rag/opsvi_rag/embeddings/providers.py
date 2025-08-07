"""
Base embedding provider interface and factory pattern.

Defines the common interface for all embedding providers and provides
a factory for creating provider instances based on configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Supported embedding provider types."""

    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class EmbeddingProviderError(ComponentError):
    """Base exception for embedding provider errors."""

    pass


class EmbeddingProviderConfig(BaseModel):
    """Base configuration for embedding providers."""

    provider_type: ProviderType = Field(..., description="Type of embedding provider")
    model: str = Field(..., description="Model name for embeddings")
    max_batch_size: int = Field(
        default=100, description="Maximum batch size for embeddings"
    )
    timeout: float = Field(default=30.0, description="Request timeout in seconds")

    class Config:
        extra = "allow"


class BaseEmbeddingProvider(BaseComponent, ABC):
    """
    Abstract base class for embedding providers.

    Provides a unified interface for generating embeddings from text
    using various underlying services and models.
    """

    def __init__(self, config: EmbeddingProviderConfig, **kwargs):
        """Initialize the embedding provider."""
        super().__init__(**kwargs)
        self.config = config
        self.logger = get_logger(__name__)

    @abstractmethod
    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            **kwargs: Additional provider-specific arguments

        Returns:
            List of embedding vectors (each vector is a list of floats)

        Raises:
            EmbeddingProviderError: If embedding generation fails
        """
        pass

    @abstractmethod
    async def get_dimensions(self) -> int:
        """
        Get the dimensionality of embeddings produced by this provider.

        Returns:
            Number of dimensions in the embedding vectors
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check on the embedding provider.

        Returns:
            True if the provider is healthy, False otherwise
        """
        pass

    async def embed_single(self, text: str, **kwargs) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed
            **kwargs: Additional provider-specific arguments

        Returns:
            Embedding vector as a list of floats
        """
        embeddings = await self.embed_texts([text], **kwargs)
        return embeddings[0]

    async def embed_batch(
        self, texts: list[str], batch_size: int | None = None, **kwargs
    ) -> list[list[float]]:
        """
        Generate embeddings for texts in batches.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size (uses config default if None)
            **kwargs: Additional provider-specific arguments

        Returns:
            List of embedding vectors
        """
        batch_size = batch_size or self.config.max_batch_size
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self.embed_texts(batch, **kwargs)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


class EmbeddingProviderFactory:
    """Factory for creating embedding provider instances."""

    _providers: dict[ProviderType, type[BaseEmbeddingProvider]] = {}

    @classmethod
    def register_provider(
        cls, provider_type: ProviderType, provider_class: type[BaseEmbeddingProvider]
    ) -> None:
        """Register a provider class for a provider type."""
        cls._providers[provider_type] = provider_class

    @classmethod
    def create_provider(cls, config: EmbeddingProviderConfig) -> BaseEmbeddingProvider:
        """
        Create an embedding provider instance.

        Args:
            config: Provider configuration

        Returns:
            Configured embedding provider instance

        Raises:
            EmbeddingProviderError: If provider type is not supported
        """
        if config.provider_type not in cls._providers:
            raise EmbeddingProviderError(
                f"Unsupported provider type: {config.provider_type}"
            )

        provider_class = cls._providers[config.provider_type]
        return provider_class(config)

    @classmethod
    def get_supported_providers(cls) -> list[ProviderType]:
        """Get list of supported provider types."""
        return list(cls._providers.keys())

    @classmethod
    def get_provider_capabilities(cls) -> dict[ProviderType, dict[str, Any]]:
        """Get capabilities of registered providers."""
        capabilities = {}
        for provider_type, provider_class in cls._providers.items():
            capabilities[provider_type] = {
                "class": provider_class.__name__,
                "supports_batching": hasattr(provider_class, "embed_batch"),
                "supports_health_check": hasattr(provider_class, "health_check"),
            }
        return capabilities
