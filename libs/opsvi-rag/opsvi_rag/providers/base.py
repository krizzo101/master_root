"""
Base embedding provider interface for OPSVI RAG system.

Provides abstract interface for embedding providers with async support,
batch processing capabilities, and integration with opsvi-core patterns.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from opsvi_core import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    texts: list[str] = Field(..., description="List of texts to embed")
    model: str | None = Field(None, description="Specific model to use")
    batch_size: int | None = Field(None, description="Batch size for processing")
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional metadata"
    )


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    embeddings: list[list[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used for embedding")
    dimensions: int = Field(..., description="Embedding dimensions")
    usage: dict[str, Any] | None = Field(None, description="Usage statistics")
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Response metadata"
    )


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    Provides interface for async embedding generation with support for:
    - Single text and batch processing
    - Rate limiting and error handling
    - Metrics and monitoring integration
    - Cross-provider compatibility
    """

    def __init__(self, model: str, **kwargs):
        """
        Initialize embedding provider.

        Args:
            model: The embedding model to use
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs
        self._lock = asyncio.Lock()

    @abstractmethod
    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    async def embed_text(self, text: str, **kwargs) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            **kwargs: Provider-specific parameters

        Returns:
            Embedding vector
        """
        embeddings = await self.embed_texts([text], **kwargs)
        return embeddings[0]

    async def embed_batch(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings using structured request/response models.

        Args:
            request: Embedding request with texts and configuration

        Returns:
            Structured embedding response with metadata
        """
        logger.debug(f"Processing embedding batch of {len(request.texts)} texts")

        try:
            embeddings = await self.embed_texts(
                request.texts,
                model=request.model or self.model,
                batch_size=request.batch_size,
            )

            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model or self.model,
                dimensions=len(embeddings[0]) if embeddings else 0,
                metadata=request.metadata,
            )

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    @abstractmethod
    async def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for this provider.

        Returns:
            Number of dimensions in embeddings
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the embedding provider is healthy and accessible.

        Returns:
            True if provider is healthy, False otherwise
        """
        pass

    def supports_batch(self) -> bool:
        """
        Check if provider supports batch processing.

        Returns:
            True if batch processing is supported
        """
        return True

    def get_max_batch_size(self) -> int:
        """
        Get maximum supported batch size.

        Returns:
            Maximum number of texts per batch
        """
        return 100  # Default conservative limit

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Default implementation - subclasses can override for cleanup
        return None
