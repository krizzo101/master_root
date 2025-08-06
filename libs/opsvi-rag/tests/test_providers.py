"""
Tests for embedding providers in OPSVI RAG system.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from opsvi_core.exceptions import InitializationError, ValidationError

from opsvi_rag.providers import (
    BaseEmbeddingProvider,
    EmbeddingProviderFactory,
    OpenAIEmbeddingProvider,
    ProviderType,
    SentenceTransformerEmbeddingProvider,
)
from opsvi_rag.providers.base import EmbeddingRequest, EmbeddingResponse
from opsvi_rag.providers.openai_provider import OpenAIEmbeddingConfig
from opsvi_rag.providers.sentence_transformer_provider import SentenceTransformerConfig


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Mock implementation for testing abstract base class."""

    def __init__(self, model: str = "mock-model", **kwargs):
        super().__init__(model, **kwargs)
        self.dimensions = 384

    async def embed_texts(self, texts: list[str], **kwargs) -> list[list[float]]:
        # Return mock embeddings
        return [[0.1] * self.dimensions for _ in texts]

    async def get_dimensions(self) -> int:
        return self.dimensions

    async def health_check(self) -> bool:
        return True


class TestBaseEmbeddingProvider:
    """Tests for BaseEmbeddingProvider abstract class."""

    @pytest.fixture
    def provider(self):
        return MockEmbeddingProvider()

    @pytest.mark.asyncio
    async def test_embed_text_single(self, provider):
        """Test embedding a single text."""
        text = "Hello world"
        embedding = await provider.embed_text(text)

        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_embed_batch_structured(self, provider):
        """Test structured batch embedding."""
        request = EmbeddingRequest(
            texts=["text1", "text2"], metadata={"source": "test"}
        )

        response = await provider.embed_batch(request)

        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2
        assert response.dimensions == 384
        assert response.model == "mock-model"
        assert response.metadata["source"] == "test"

    def test_context_manager_protocol(self, provider):
        """Test async context manager protocol."""
        assert hasattr(provider, "__aenter__")
        assert hasattr(provider, "__aexit__")


class TestOpenAIEmbeddingProvider:
    """Tests for OpenAI embedding provider."""

    @pytest.fixture
    def config(self):
        return OpenAIEmbeddingConfig(
            model="text-embedding-3-small", api_key="test-key", max_batch_size=10
        )

    @pytest.fixture
    def mock_openai_provider(self):
        with patch("opsvi_rag.providers.openai_provider.OpenAIProvider") as mock:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock()
            mock.return_value.client.with_options.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock.return_value.client.with_options.return_value.__aexit__ = AsyncMock(
                return_value=None
            )
            yield mock

    def test_initialization_valid_model(self, config):
        """Test initialization with valid model."""
        provider = OpenAIEmbeddingProvider(config)
        assert provider.config.model == "text-embedding-3-small"
        assert provider.config.api_key == "test-key"

    def test_initialization_invalid_model(self):
        """Test initialization with invalid model."""
        config = OpenAIEmbeddingConfig(model="invalid-model")

        with pytest.raises(ValidationError, match="Unsupported model"):
            OpenAIEmbeddingProvider(config)

    @pytest.mark.asyncio
    async def test_embed_texts_success(self, config, mock_openai_provider):
        """Test successful text embedding."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
        ]

        mock_client = (
            mock_openai_provider.return_value.client.with_options.return_value.__aenter__.return_value
        )
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)

        provider = OpenAIEmbeddingProvider(config)
        texts = ["hello", "world"]

        embeddings = await provider.embed_texts(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_texts_batch_size_exceeded(self, config):
        """Test batch size validation."""
        provider = OpenAIEmbeddingProvider(config)
        texts = ["text"] * 20  # Exceeds max_batch_size of 10

        with pytest.raises(ValidationError, match="Batch size .* exceeds maximum"):
            await provider.embed_texts(texts)

    @pytest.mark.asyncio
    async def test_get_dimensions(self, config):
        """Test getting embedding dimensions."""
        provider = OpenAIEmbeddingProvider(config)
        dimensions = await provider.get_dimensions()
        assert dimensions == 1536  # text-embedding-3-small default

    def test_get_model_info(self, config):
        """Test getting model information."""
        provider = OpenAIEmbeddingProvider(config)
        info = provider.get_model_info()

        assert info["model"] == "text-embedding-3-small"
        assert info["dimensions"] == 1536
        assert info["configurable_dimensions"] is True


@pytest.mark.skipif(
    not hasattr(pytest, "_sentence_transformers_available"),
    reason="sentence-transformers not available",
)
class TestSentenceTransformerEmbeddingProvider:
    """Tests for Sentence Transformers embedding provider."""

    @pytest.fixture
    def config(self):
        return SentenceTransformerConfig(
            model="all-MiniLM-L6-v2", device="cpu", max_batch_size=8
        )

    @pytest.fixture
    def mock_sentence_transformer(self):
        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SentenceTransformer"
        ) as mock:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384]
            mock.return_value = mock_model
            yield mock

    def test_initialization(self, config, mock_sentence_transformer):
        """Test provider initialization."""
        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SENTENCE_TRANSFORMERS_AVAILABLE",
            True,
        ):
            provider = SentenceTransformerEmbeddingProvider(config)
            assert provider.config.model == "all-MiniLM-L6-v2"
            assert provider.config.device == "cpu"

    def test_initialization_no_library(self):
        """Test initialization when sentence-transformers not available."""
        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SENTENCE_TRANSFORMERS_AVAILABLE",
            False,
        ):
            with pytest.raises(
                InitializationError, match="sentence-transformers library not available"
            ):
                SentenceTransformerEmbeddingProvider()

    @pytest.mark.asyncio
    async def test_embed_texts_success(self, config, mock_sentence_transformer):
        """Test successful text embedding."""
        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SENTENCE_TRANSFORMERS_AVAILABLE",
            True,
        ):
            provider = SentenceTransformerEmbeddingProvider(config)

            # Mock the model loading
            with patch.object(provider, "_load_model", AsyncMock()):
                provider.model = mock_sentence_transformer.return_value
                provider._dimensions = 384

                texts = ["hello", "world"]
                embeddings = await provider.embed_texts(texts)

                assert len(embeddings) == 2
                assert len(embeddings[0]) == 384

    def test_list_available_models(self, config, mock_sentence_transformer):
        """Test listing available models."""
        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SENTENCE_TRANSFORMERS_AVAILABLE",
            True,
        ):
            provider = SentenceTransformerEmbeddingProvider(config)
            models = provider.list_available_models()

            assert "all-MiniLM-L6-v2" in models
            assert "description" in models["all-MiniLM-L6-v2"]


class TestEmbeddingProviderFactory:
    """Tests for embedding provider factory."""

    @pytest.mark.asyncio
    async def test_create_openai_provider(self):
        """Test creating OpenAI provider through factory."""
        config = EmbeddingProviderFactory.create_openai_config(
            model="text-embedding-3-small", api_key="test-key"
        )

        with patch("opsvi_rag.providers.openai_provider.OpenAIProvider"):
            provider = await EmbeddingProviderFactory.create_provider(config)
            assert isinstance(provider, OpenAIEmbeddingProvider)

    @pytest.mark.asyncio
    async def test_create_sentence_transformer_provider(self):
        """Test creating Sentence Transformers provider through factory."""
        config = EmbeddingProviderFactory.create_sentence_transformer_config(
            model="all-MiniLM-L6-v2"
        )

        with patch(
            "opsvi_rag.providers.sentence_transformer_provider.SENTENCE_TRANSFORMERS_AVAILABLE",
            True,
        ):
            with patch(
                "opsvi_rag.providers.sentence_transformer_provider.SentenceTransformer"
            ):
                provider = await EmbeddingProviderFactory.create_provider(config)
                assert isinstance(provider, SentenceTransformerEmbeddingProvider)

    def test_get_default_config(self):
        """Test getting default configuration."""
        openai_defaults = EmbeddingProviderFactory.get_default_config(
            ProviderType.OPENAI
        )
        assert openai_defaults["model"] == "text-embedding-3-small"
        assert openai_defaults["max_batch_size"] == 100

        st_defaults = EmbeddingProviderFactory.get_default_config(
            ProviderType.SENTENCE_TRANSFORMERS
        )
        assert st_defaults["model"] == "all-MiniLM-L6-v2"
        assert st_defaults["normalize_embeddings"] is True

    def test_get_provider_capabilities(self):
        """Test getting provider capabilities."""
        openai_caps = EmbeddingProviderFactory.get_provider_capabilities(
            ProviderType.OPENAI
        )
        assert openai_caps["cloud_based"] is True
        assert openai_caps["requires_api_key"] is True

        st_caps = EmbeddingProviderFactory.get_provider_capabilities(
            ProviderType.SENTENCE_TRANSFORMERS
        )
        assert st_caps["cloud_based"] is False
        assert st_caps["requires_api_key"] is False

    def test_create_hybrid_config(self):
        """Test creating hybrid configuration with fallback."""
        primary, fallbacks = EmbeddingProviderFactory.create_hybrid_config(
            prefer_local=True, openai_api_key="test-key"
        )

        assert primary.provider_type == ProviderType.SENTENCE_TRANSFORMERS
        assert len(fallbacks) == 1
        assert fallbacks[0].provider_type == ProviderType.OPENAI
