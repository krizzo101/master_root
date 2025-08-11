"""Tests for Perplexity provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from opsvi_llm import PerplexityProvider, PerplexityConfig, ChatRequest, Message


class TestPerplexityConfig:
    """Test Perplexity configuration."""

    def test_perplexity_config_defaults(self):
        """Test Perplexity config with default values."""
        config = PerplexityConfig(
            provider_name="perplexity",
            api_key="test-key",
            default_model="sonar-small-online",
        )

        assert config.provider_name == "perplexity"
        assert config.api_key == "test-key"
        assert config.default_model == "sonar-small-online"
        assert config.base_url == "https://api.perplexity.ai"
        assert config.search_mode == "web"
        assert config.reasoning_effort is None

    def test_perplexity_config_custom(self):
        """Test Perplexity config with custom values."""
        config = PerplexityConfig(
            provider_name="perplexity",
            api_key="test-key",
            default_model="sonar-medium-online",
            base_url="https://custom.api.perplexity.ai",
            search_mode="academic",
            reasoning_effort="high",
        )

        assert config.base_url == "https://custom.api.perplexity.ai"
        assert config.search_mode == "academic"
        assert config.reasoning_effort == "high"


class TestPerplexityProvider:
    """Test Perplexity provider."""

    @pytest.fixture
    def perplexity_config(self):
        """Create Perplexity config for testing."""
        return PerplexityConfig(
            provider_name="perplexity",
            api_key="test-key",
            default_model="sonar-pro",
        )

    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock(spec=aiohttp.ClientSession)
        return session

    @pytest.mark.asyncio
    async def test_perplexity_provider_initialization(self, perplexity_config):
        """Test Perplexity provider initialization."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            provider = PerplexityProvider(perplexity_config)
            await provider.initialize()

            assert provider.perplexity_config == perplexity_config
            assert provider._async_session is not None
            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_perplexity_provider_missing_api_key(self):
        """Test Perplexity provider with missing API key."""
        config = PerplexityConfig(
            provider_name="perplexity", api_key=None, default_model="sonar-pro"
        )

        provider = PerplexityProvider(config)

        with pytest.raises(Exception, match="Perplexity API key is required"):
            await provider.initialize()

    @pytest.mark.asyncio
    async def test_perplexity_chat_completion(self, perplexity_config, mock_session):
        """Test Perplexity chat completion."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = mock_session

            # Mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "This is a test response",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "model": "sonar-pro",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            }

            mock_session.post.return_value.__aenter__.return_value = mock_response

            provider = PerplexityProvider(perplexity_config)
            await provider.initialize()

            # Test chat completion
            chat_request = ChatRequest(
                messages=[Message(role="user", content="Hello")],
                model="sonar-pro",
            )

            response = await provider.chat(chat_request)

            assert response.message.content == "This is a test response"
            assert response.message.role == "assistant"
            assert response.model == "sonar-pro"

            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_perplexity_health_check(self, perplexity_config, mock_session):
        """Test Perplexity health check."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = mock_session

            # Mock health check response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "data": [{"id": "sonar"}, {"id": "sonar-pro"}]
            }

            mock_session.get.return_value.__aenter__.return_value = mock_response

            provider = PerplexityProvider(perplexity_config)
            await provider.initialize()

            # Test health check
            health_status = await provider.health_check()
            assert health_status is True

            await provider.shutdown()

    @pytest.mark.asyncio
    async def test_perplexity_list_models(self, perplexity_config, mock_session):
        """Test Perplexity list models."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session_class.return_value = mock_session

            # Mock models response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "data": [
                    {"id": "sonar"},
                    {"id": "sonar-pro"},
                    {"id": "text-embedding-ada-002"},
                ]
            }

            mock_session.get.return_value.__aenter__.return_value = mock_response

            provider = PerplexityProvider(perplexity_config)
            await provider.initialize()

            # Test list models
            models = await provider.list_models()
            assert "sonar" in models
            assert "sonar-pro" in models
            assert "text-embedding-ada-002" in models

            # Test list chat models
            chat_models = await provider.list_chat_models()
            assert "sonar" in chat_models
            assert "sonar-pro" in chat_models
            assert "text-embedding-ada-002" not in chat_models

            # Test list embedding models
            embedding_models = await provider.list_embedding_models()
            assert "text-embedding-ada-002" in embedding_models
            assert "sonar" not in embedding_models

            await provider.shutdown()
