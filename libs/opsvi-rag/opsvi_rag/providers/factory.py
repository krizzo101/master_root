"""
Embedding provider factory for OPSVI RAG system.

Provides dynamic provider selection and configuration based on
environment, requirements, and runtime constraints.
"""

from enum import Enum
from typing import Any

from opsvi_core import get_logger
from opsvi_core.exceptions import InitializationError, ValidationError
from pydantic import BaseModel, Field

from .base import BaseEmbeddingProvider
from .openai_provider import OpenAIEmbeddingConfig, OpenAIEmbeddingProvider
from .sentence_transformer_provider import (
    SentenceTransformerConfig,
    SentenceTransformerEmbeddingProvider,
)

logger = get_logger(__name__)


class ProviderType(str, Enum):
    """Supported embedding provider types."""

    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"


class EmbeddingProviderConfig(BaseModel):
    """Configuration for embedding provider factory."""

    provider_type: ProviderType = Field(..., description="Type of embedding provider")
    auto_fallback: bool = Field(
        default=False, description="Enable automatic fallback to alternative providers"
    )
    health_check_on_init: bool = Field(
        default=True, description="Perform health check during initialization"
    )
    provider_config: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )


class EmbeddingProviderFactory:
    """
    Factory for creating and managing embedding providers.

    Features:
    - Dynamic provider selection based on configuration
    - Automatic fallback between providers
    - Health checking and validation
    - Provider capability detection
    - Configuration validation and optimization
    """

    _PROVIDER_CLASSES: dict[ProviderType, type[BaseEmbeddingProvider]] = {
        ProviderType.OPENAI: OpenAIEmbeddingProvider,
        ProviderType.SENTENCE_TRANSFORMERS: SentenceTransformerEmbeddingProvider,
    }

    _CONFIG_CLASSES: dict[ProviderType, type[BaseModel]] = {
        ProviderType.OPENAI: OpenAIEmbeddingConfig,
        ProviderType.SENTENCE_TRANSFORMERS: SentenceTransformerConfig,
    }

    @classmethod
    async def create_provider(
        cls, config: EmbeddingProviderConfig
    ) -> BaseEmbeddingProvider:
        """
        Create an embedding provider based on configuration.

        Args:
            config: Provider configuration

        Returns:
            Configured embedding provider instance

        Raises:
            ValidationError: If configuration is invalid
            InitializationError: If provider initialization fails
        """
        logger.info(f"Creating embedding provider: {config.provider_type}")

        # Get provider class
        provider_class = cls._PROVIDER_CLASSES.get(config.provider_type)
        if not provider_class:
            raise ValidationError(f"Unsupported provider type: {config.provider_type}")

        # Get configuration class and validate
        config_class = cls._CONFIG_CLASSES.get(config.provider_type)
        if config_class:
            provider_config = config_class(**config.provider_config)
        else:
            provider_config = config.provider_config

        try:
            # Create provider instance
            if isinstance(provider_config, BaseModel):
                provider = provider_class(config=provider_config)
            else:
                provider = provider_class(**provider_config)

            # Perform health check if requested
            if config.health_check_on_init:
                logger.debug("Performing initial health check")
                is_healthy = await provider.health_check()
                if not is_healthy:
                    raise InitializationError(
                        f"Provider {config.provider_type} failed health check"
                    )
                logger.info("Provider health check passed")

            return provider

        except Exception as e:
            error_msg = f"Failed to create provider {config.provider_type}: {e}"
            logger.error(error_msg)
            raise InitializationError(error_msg) from e

    @classmethod
    async def create_provider_with_fallback(
        cls,
        primary_config: EmbeddingProviderConfig,
        fallback_configs: list[EmbeddingProviderConfig] | None = None,
    ) -> BaseEmbeddingProvider:
        """
        Create provider with automatic fallback to alternatives.

        Args:
            primary_config: Primary provider configuration
            fallback_configs: List of fallback configurations

        Returns:
            Working embedding provider instance

        Raises:
            InitializationError: If all providers fail
        """
        # Try primary provider
        try:
            return await cls.create_provider(primary_config)
        except Exception as e:
            logger.warning(
                f"Primary provider {primary_config.provider_type} failed: {e}"
            )

        # Try fallback providers
        if fallback_configs:
            for i, fallback_config in enumerate(fallback_configs):
                try:
                    logger.info(
                        f"Trying fallback provider {i+1}: {fallback_config.provider_type}"
                    )
                    return await cls.create_provider(fallback_config)
                except Exception as e:
                    logger.warning(
                        f"Fallback provider {fallback_config.provider_type} failed: {e}"
                    )

        raise InitializationError("All embedding providers failed to initialize")

    @classmethod
    def get_default_config(cls, provider_type: ProviderType) -> dict[str, Any]:
        """
        Get default configuration for a provider type.

        Args:
            provider_type: Type of provider

        Returns:
            Default configuration dictionary
        """
        defaults = {
            ProviderType.OPENAI: {
                "model": "text-embedding-3-small",
                "max_batch_size": 100,
                "timeout": 30,
                "max_retries": 3,
            },
            ProviderType.SENTENCE_TRANSFORMERS: {
                "model": "all-MiniLM-L6-v2",
                "max_batch_size": 32,
                "normalize_embeddings": True,
                "max_workers": 4,
            },
        }

        return defaults.get(provider_type, {})

    @classmethod
    def create_openai_config(
        cls,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        **kwargs,
    ) -> EmbeddingProviderConfig:
        """
        Create OpenAI provider configuration.

        Args:
            model: OpenAI embedding model
            api_key: OpenAI API key
            **kwargs: Additional configuration options

        Returns:
            OpenAI provider configuration
        """
        provider_config = cls.get_default_config(ProviderType.OPENAI)
        provider_config.update({"model": model, "api_key": api_key, **kwargs})

        return EmbeddingProviderConfig(
            provider_type=ProviderType.OPENAI, provider_config=provider_config
        )

    @classmethod
    def create_sentence_transformer_config(
        cls, model: str = "all-MiniLM-L6-v2", device: str | None = None, **kwargs
    ) -> EmbeddingProviderConfig:
        """
        Create Sentence Transformers provider configuration.

        Args:
            model: Sentence Transformers model
            device: Device to run on (cpu, cuda, mps)
            **kwargs: Additional configuration options

        Returns:
            Sentence Transformers provider configuration
        """
        provider_config = cls.get_default_config(ProviderType.SENTENCE_TRANSFORMERS)
        provider_config.update({"model": model, "device": device, **kwargs})

        return EmbeddingProviderConfig(
            provider_type=ProviderType.SENTENCE_TRANSFORMERS,
            provider_config=provider_config,
        )

    @classmethod
    def create_hybrid_config(
        cls, prefer_local: bool = False, openai_api_key: str | None = None
    ) -> tuple[EmbeddingProviderConfig, list[EmbeddingProviderConfig]]:
        """
        Create hybrid configuration with automatic fallback.

        Args:
            prefer_local: Whether to prefer local (Sentence Transformers) over cloud (OpenAI)
            openai_api_key: OpenAI API key for cloud fallback

        Returns:
            Tuple of (primary_config, fallback_configs)
        """
        openai_config = cls.create_openai_config(api_key=openai_api_key)
        local_config = cls.create_sentence_transformer_config()

        if prefer_local:
            primary = local_config
            fallbacks = [openai_config] if openai_api_key else []
        else:
            primary = openai_config if openai_api_key else local_config
            fallbacks = [local_config] if openai_api_key else []

        return primary, fallbacks

    @classmethod
    def get_provider_capabilities(cls, provider_type: ProviderType) -> dict[str, Any]:
        """
        Get capabilities and features of a provider type.

        Args:
            provider_type: Type of provider

        Returns:
            Dictionary describing provider capabilities
        """
        capabilities = {
            ProviderType.OPENAI: {
                "cloud_based": True,
                "requires_api_key": True,
                "supports_custom_dimensions": True,
                "max_input_tokens": 8191,
                "cost_per_use": True,
                "rate_limited": True,
                "models": [
                    "text-embedding-3-small",
                    "text-embedding-3-large",
                    "text-embedding-ada-002",
                ],
            },
            ProviderType.SENTENCE_TRANSFORMERS: {
                "cloud_based": False,
                "requires_api_key": False,
                "supports_custom_dimensions": False,
                "max_input_tokens": "model_dependent",
                "cost_per_use": False,
                "rate_limited": False,
                "models": "1000+ available on HuggingFace",
            },
        }

        return capabilities.get(provider_type, {})
