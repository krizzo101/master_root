"""
Sentence Transformers embedding provider for OPSVI RAG system.

Provides on-premise embedding capabilities using Sentence Transformers library.
Supports local model execution with async wrappers for pipeline integration.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from opsvi_core import get_logger
from opsvi_core.exceptions import InitializationError, ValidationError
from pydantic import BaseModel, Field

from .base import BaseEmbeddingProvider

logger = get_logger(__name__)

# Optional import - graceful degradation if not available
try:
    import torch
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning(
        "sentence-transformers not available. Install with: pip install sentence-transformers"
    )
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class SentenceTransformerConfig(BaseModel):
    """Configuration for Sentence Transformers embedding provider."""

    model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformers model"
    )
    device: str | None = Field(
        None, description="Device to run model on (cpu, cuda, mps)"
    )
    cache_folder: str | None = Field(None, description="Model cache directory")
    max_batch_size: int = Field(default=32, description="Maximum texts per batch")
    normalize_embeddings: bool = Field(
        default=True, description="Normalize embeddings to unit length"
    )
    max_workers: int = Field(
        default=4, description="Maximum worker threads for processing"
    )
    model_kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Additional model arguments"
    )


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Sentence Transformers embedding provider with async wrapper.

    Features:
    - Local on-premise embedding generation
    - Support for 1000+ pre-trained models
    - Automatic device detection (CPU/GPU/MPS)
    - Async processing with thread pool execution
    - Batch processing optimization
    - Model caching and reuse
    """

    RECOMMENDED_MODELS = {
        "all-MiniLM-L6-v2": {
            "dimensions": 384,
            "description": "Fast, good quality, lightweight",
        },
        "all-mpnet-base-v2": {"dimensions": 768, "description": "Best quality, slower"},
        "all-MiniLM-L12-v2": {
            "dimensions": 384,
            "description": "Better quality than L6, still fast",
        },
        "paraphrase-MiniLM-L6-v2": {
            "dimensions": 384,
            "description": "Good for paraphrase detection",
        },
        "multi-qa-MiniLM-L6-cos-v1": {
            "dimensions": 384,
            "description": "Optimized for Q&A",
        },
    }

    def __init__(self, config: SentenceTransformerConfig | None = None, **kwargs):
        """
        Initialize Sentence Transformers embedding provider.

        Args:
            config: Sentence Transformers configuration
            **kwargs: Additional configuration options
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise InitializationError(
                "sentence-transformers library not available. "
                "Install with: pip install sentence-transformers torch"
            )

        self.config = config or SentenceTransformerConfig(**kwargs)
        super().__init__(self.config.model, **kwargs)

        # Initialize model
        self.model = None
        self._dimensions = None
        self._thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._model_lock = threading.Lock()

        logger.info(
            f"Initializing Sentence Transformers provider with model: {self.config.model}"
        )

    async def _load_model(self) -> None:
        """Load the Sentence Transformers model asynchronously."""
        if self.model is not None:
            return

        def _load_sync():
            with self._model_lock:
                if self.model is not None:
                    return

                try:
                    # Determine device
                    device = self.config.device
                    if device is None:
                        if torch.cuda.is_available():
                            device = "cuda"
                        elif (
                            hasattr(torch.backends, "mps")
                            and torch.backends.mps.is_available()
                        ):
                            device = "mps"
                        else:
                            device = "cpu"

                    logger.info(
                        f"Loading model {self.config.model} on device: {device}"
                    )

                    # Load model
                    model_kwargs = {
                        "device": device,
                        "cache_folder": self.config.cache_folder,
                        **self.config.model_kwargs,
                    }

                    self.model = SentenceTransformer(self.config.model, **model_kwargs)
                    self._dimensions = self.model.get_sentence_embedding_dimension()

                    logger.info(
                        f"Model loaded successfully. Dimensions: {self._dimensions}"
                    )

                except Exception as e:
                    raise InitializationError(
                        f"Failed to load model {self.config.model}: {e}"
                    ) from e

        # Run model loading in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(self._thread_pool, _load_sync)

    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts using Sentence Transformers.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters (batch_size, normalize_embeddings)

        Returns:
            List of embedding vectors

        Raises:
            ValidationError: If input validation fails
            InitializationError: If model loading fails
        """
        if not texts:
            return []

        # Ensure model is loaded
        await self._load_model()

        # Validate input
        if len(texts) > self.config.max_batch_size:
            logger.warning(
                f"Batch size {len(texts)} exceeds recommended maximum {self.config.max_batch_size}"
            )

        # Get parameters
        normalize = kwargs.get("normalize_embeddings", self.config.normalize_embeddings)
        batch_size = kwargs.get("batch_size", self.config.max_batch_size)

        logger.debug(f"Generating embeddings for {len(texts)} texts")

        def _embed_sync():
            try:
                # Generate embeddings
                embeddings = self.model.encode(
                    texts,
                    batch_size=min(batch_size, len(texts)),
                    normalize_embeddings=normalize,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )

                # Convert to list of lists
                return embeddings.tolist()

            except Exception as e:
                raise ValidationError(f"Embedding generation failed: {e}") from e

        # Run embedding generation in thread pool
        embeddings = await asyncio.get_event_loop().run_in_executor(
            self._thread_pool, _embed_sync
        )

        logger.debug(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings

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

        batch_size = batch_size or self.config.max_batch_size

        if len(texts) <= batch_size:
            return await self.embed_texts(texts, batch_size=batch_size)

        logger.info(f"Processing {len(texts)} texts in batches of {batch_size}")

        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self.embed_texts(batch, batch_size=batch_size)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for the current model.

        Returns:
            Number of dimensions in embeddings
        """
        await self._load_model()
        return self._dimensions

    async def health_check(self) -> bool:
        """
        Check if the Sentence Transformers model is loaded and functional.

        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Ensure model is loaded
            await self._load_model()

            # Test with minimal input
            test_embeddings = await self.embed_texts(["health check"])
            return len(test_embeddings) == 1 and len(test_embeddings[0]) > 0

        except Exception as e:
            logger.warning(f"Sentence Transformers provider health check failed: {e}")
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
        model_info = self.RECOMMENDED_MODELS.get(self.config.model, {})

        return {
            "model": self.config.model,
            "dimensions": self._dimensions,
            "device": getattr(self.model, "device", None) if self.model else None,
            "description": model_info.get("description", "Custom model"),
            "normalize_embeddings": self.config.normalize_embeddings,
            "local_execution": True,
        }

    def list_available_models(self) -> dict[str, dict[str, Any]]:
        """
        Get list of recommended models with their information.

        Returns:
            Dictionary mapping model names to their information
        """
        return self.RECOMMENDED_MODELS.copy()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources on exit."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        await super().__aexit__(exc_type, exc_val, exc_tb)
