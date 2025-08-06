"""
Sentence Transformers embedding provider implementation.

Provides local embedding generation using Sentence Transformers models
with proper batching, caching, and performance optimization.
"""

from __future__ import annotations

import asyncio
from typing import Any

from opsvi_foundation import get_logger
from pydantic import Field

from .providers import (
    BaseEmbeddingProvider,
    EmbeddingProviderConfig,
    EmbeddingProviderError,
    ProviderType,
)


class SentenceTransformerConfig(EmbeddingProviderConfig):
    """Configuration for Sentence Transformers embedding provider."""

    provider_type: ProviderType = Field(
        default=ProviderType.SENTENCE_TRANSFORMERS,
        description="Sentence Transformers provider",
    )
    model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformers model name"
    )
    max_batch_size: int = Field(
        default=32, description="Maximum batch size for local processing"
    )
    device: str | None = Field(
        default=None, description="Device to use (cpu, cuda, mps)"
    )
    normalize_embeddings: bool = Field(
        default=True, description="Whether to normalize embeddings"
    )
    show_progress_bar: bool = Field(
        default=False, description="Show progress bar during embedding"
    )

    class Config:
        extra = "allow"


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Sentence Transformers embedding provider implementation.

    Generates embeddings using local Sentence Transformers models with
    proper batching, device management, and performance optimization.
    """

    def __init__(self, config: SentenceTransformerConfig, **kwargs):
        """Initialize the Sentence Transformers embedding provider."""
        super().__init__(config, **kwargs)
        self.config = config
        self.logger = get_logger(__name__)

        # Initialize the model
        self._model = None
        self._dimensions = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the Sentence Transformers model is initialized."""
        if self._initialized:
            return

        try:
            # Import here to avoid dependency issues
            from sentence_transformers import SentenceTransformer

            self.logger.info(
                f"Loading Sentence Transformers model: {self.config.model}"
            )

            # Initialize the model
            self._model = SentenceTransformer(
                self.config.model,
                device=self.config.device,
            )

            # Get model dimensions
            self._dimensions = self._model.get_sentence_embedding_dimension()

            self._initialized = True
            self.logger.info(
                f"Model loaded successfully. Dimensions: {self._dimensions}"
            )

        except ImportError:
            raise EmbeddingProviderError(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
        except Exception as e:
            raise EmbeddingProviderError(
                f"Failed to initialize Sentence Transformers model: {e}"
            ) from e

    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using Sentence Transformers.

        Args:
            texts: List of text strings to embed
            **kwargs: Additional arguments (normalize_embeddings, show_progress_bar)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingProviderError: If embedding generation fails
        """
        if not texts:
            return []

        await self._ensure_initialized()

        try:
            # Extract kwargs
            normalize = kwargs.get(
                "normalize_embeddings", self.config.normalize_embeddings
            )
            show_progress = kwargs.get(
                "show_progress_bar", self.config.show_progress_bar
            )

            # Run embedding in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self._model.encode,
                texts,
                batch_size=self.config.max_batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=False,  # Return as list
            )

            # Convert to list of lists if needed
            if isinstance(embeddings, list):
                return embeddings
            else:
                return embeddings.tolist()

        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise EmbeddingProviderError(
                f"Sentence Transformers embedding failed: {e}"
            ) from e

    async def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this provider."""
        await self._ensure_initialized()
        return self._dimensions

    async def health_check(self) -> bool:
        """
        Perform a health check on the Sentence Transformers provider.

        Returns:
            True if the provider is healthy, False otherwise
        """
        try:
            await self._ensure_initialized()
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
            "device": self.config.device,
            "normalize_embeddings": self.config.normalize_embeddings,
            "max_batch_size": self.config.max_batch_size,
        }

    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Get list of commonly used Sentence Transformers models."""
        return [
            "all-MiniLM-L6-v2",  # 384 dimensions, fast
            "all-MiniLM-L12-v2",  # 384 dimensions, balanced
            "all-mpnet-base-v2",  # 768 dimensions, high quality
            "all-mpnet-base-v2",  # 768 dimensions, high quality
            "multi-qa-MiniLM-L6-v2",  # 384 dimensions, QA optimized
            "paraphrase-MiniLM-L6-v2",  # 384 dimensions, paraphrase optimized
        ]

    @classmethod
    def list_available_models(cls) -> list[str]:
        """List available Sentence Transformers models (requires internet connection)."""
        try:
            from sentence_transformers import SentenceTransformer

            # This would require additional logic to fetch from HuggingFace
            # For now, return the commonly used models
            return cls.get_supported_models()
        except ImportError:
            return []
