"""Tests for opsvi-llm library."""

import pytest
from typing import List

from opsvi_llm import (
    BaseLLMProvider,
    LLMConfig,
    LLMError,
    LLMProviderError,
    LLMConfigError,
    LLMRequestError,
    LLMResponseError,
    Message,
    CompletionRequest,
    ChatRequest,
    EmbeddingRequest,
    CompletionResponse,
    ChatResponse,
    EmbeddingResponse,
    OpenAIProvider,
    OpenAIConfig,
)
from opsvi_foundation import ComponentError


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._mock_client = None

    async def _create_client(self):
        """Create mock client."""
        self._mock_client = {"status": "connected"}
        return self._mock_client

    async def _close_client(self):
        """Close mock client."""
        self._mock_client = None

    async def _check_health(self) -> bool:
        """Check mock health."""
        return self._mock_client is not None

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Mock completion."""
        return CompletionResponse(
            text="Mock completion response",
            model=request.model or self.config.default_model,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Mock chat completion."""
        return ChatResponse(
            message=Message(
                role="assistant",
                content="Mock chat response",
            ),
            model=request.model or self.config.default_model,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Mock embedding."""
        if isinstance(request.input, str):
            embeddings = [[0.1, 0.2, 0.3]]
        else:
            embeddings = [[0.1, 0.2, 0.3]] * len(request.input)

        return EmbeddingResponse(
            embeddings=embeddings,
            model=request.model or "mock-embedding-model",
            usage={"prompt_tokens": 10},
        )

    async def _list_models(self) -> List[str]:
        """List mock models."""
        return ["mock-model-1", "mock-model-2"]


@pytest.fixture
def llm_config():
    """Create a test LLM configuration."""
    return LLMConfig(
        provider_name="mock-provider",
        api_key="test-api-key",
        default_model="mock-model",
        max_tokens=100,
        temperature=0.5,
    )


@pytest.fixture
def openai_config():
    """Create a test OpenAI configuration."""
    return OpenAIConfig(
        provider_name="openai",
        api_key="test-openai-key",
        default_model="gpt-3.5-turbo",
        default_embedding_model="text-embedding-ada-002",
    )


class TestLLMConfig:
    """Test LLM configuration."""

    def test_llm_config_defaults(self):
        """Test LLM config default values."""
        config = LLMConfig(provider_name="test", default_model="test-model")

        assert config.provider_name == "test"
        assert config.default_model == "test-model"
        assert config.api_key is None
        assert config.base_url is None
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_llm_config_custom_values(self):
        """Test LLM config with custom values."""
        config = LLMConfig(
            provider_name="test",
            default_model="test-model",
            api_key="test-key",
            base_url="https://api.test.com",
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            max_tokens=2048,
            temperature=0.5,
        )

        assert config.provider_name == "test"
        assert config.default_model == "test-model"
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.test.com"
        assert config.timeout == 60.0
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.max_tokens == 2048
        assert config.temperature == 0.5


class TestOpenAIConfig:
    """Test OpenAI configuration."""

    def test_openai_config_defaults(self):
        """Test OpenAI config default values."""
        config = OpenAIConfig(
            provider_name="openai",
            api_key="test-key",
        )

        assert config.provider_name == "openai"
        assert config.api_key == "test-key"
        assert config.organization is None
        assert config.default_model == "gpt-3.5-turbo"
        assert config.default_embedding_model == "text-embedding-ada-002"

    def test_openai_config_custom_values(self):
        """Test OpenAI config with custom values."""
        config = OpenAIConfig(
            provider_name="openai",
            api_key="test-key",
            organization="test-org",
            default_model="gpt-4",
            default_embedding_model="text-embedding-3-small",
        )

        assert config.provider_name == "openai"
        assert config.api_key == "test-key"
        assert config.organization == "test-org"
        assert config.default_model == "gpt-4"
        assert config.default_embedding_model == "text-embedding-3-small"


class TestMessage:
    """Test Message model."""

    def test_message_creation(self):
        """Test Message creation."""
        message = Message(
            role="user",
            content="Hello, world!",
            name="test-user",
        )

        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.name == "test-user"

    def test_message_defaults(self):
        """Test Message default values."""
        message = Message(
            role="assistant",
            content="Hello, world!",
        )

        assert message.role == "assistant"
        assert message.content == "Hello, world!"
        assert message.name is None


class TestCompletionRequest:
    """Test CompletionRequest model."""

    def test_completion_request_creation(self):
        """Test CompletionRequest creation."""
        request = CompletionRequest(
            prompt="Test prompt",
            model="test-model",
            max_tokens=100,
            temperature=0.5,
            stop=["\n", "END"],
            stream=True,
        )

        assert request.prompt == "Test prompt"
        assert request.model == "test-model"
        assert request.max_tokens == 100
        assert request.temperature == 0.5
        assert request.stop == ["\n", "END"]
        assert request.stream is True

    def test_completion_request_defaults(self):
        """Test CompletionRequest default values."""
        request = CompletionRequest(prompt="Test prompt")

        assert request.prompt == "Test prompt"
        assert request.model is None
        assert request.max_tokens is None
        assert request.temperature is None
        assert request.stop is None
        assert request.stream is False


class TestChatRequest:
    """Test ChatRequest model."""

    def test_chat_request_creation(self):
        """Test ChatRequest creation."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]

        request = ChatRequest(
            messages=messages,
            model="test-model",
            max_tokens=100,
            temperature=0.5,
            stop=["\n", "END"],
            stream=True,
        )

        assert len(request.messages) == 2
        assert request.messages[0].role == "user"
        assert request.messages[1].role == "assistant"
        assert request.model == "test-model"
        assert request.max_tokens == 100
        assert request.temperature == 0.5
        assert request.stop == ["\n", "END"]
        assert request.stream is True


class TestEmbeddingRequest:
    """Test EmbeddingRequest model."""

    def test_embedding_request_single_string(self):
        """Test EmbeddingRequest with single string."""
        request = EmbeddingRequest(
            input="Test text",
            model="test-embedding-model",
        )

        assert request.input == "Test text"
        assert request.model == "test-embedding-model"

    def test_embedding_request_list_strings(self):
        """Test EmbeddingRequest with list of strings."""
        request = EmbeddingRequest(
            input=["Text 1", "Text 2", "Text 3"],
            model="test-embedding-model",
        )

        assert request.input == ["Text 1", "Text 2", "Text 3"]
        assert request.model == "test-embedding-model"


class TestCompletionResponse:
    """Test CompletionResponse model."""

    def test_completion_response_creation(self):
        """Test CompletionResponse creation."""
        response = CompletionResponse(
            text="Generated text",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )

        assert response.text == "Generated text"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}
        assert response.finish_reason == "stop"

    def test_completion_response_defaults(self):
        """Test CompletionResponse default values."""
        response = CompletionResponse(
            text="Generated text",
            model="test-model",
        )

        assert response.text == "Generated text"
        assert response.model == "test-model"
        assert response.usage is None
        assert response.finish_reason is None


class TestChatResponse:
    """Test ChatResponse model."""

    def test_chat_response_creation(self):
        """Test ChatResponse creation."""
        message = Message(role="assistant", content="Generated response")
        response = ChatResponse(
            message=message,
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )

        assert response.message.role == "assistant"
        assert response.message.content == "Generated response"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}
        assert response.finish_reason == "stop"

    def test_chat_response_defaults(self):
        """Test ChatResponse default values."""
        message = Message(role="assistant", content="Generated response")
        response = ChatResponse(
            message=message,
            model="test-model",
        )

        assert response.message.role == "assistant"
        assert response.message.content == "Generated response"
        assert response.model == "test-model"
        assert response.usage is None
        assert response.finish_reason is None


class TestEmbeddingResponse:
    """Test EmbeddingResponse model."""

    def test_embedding_response_creation(self):
        """Test EmbeddingResponse creation."""
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        response = EmbeddingResponse(
            embeddings=embeddings,
            model="test-embedding-model",
            usage={"prompt_tokens": 10},
        )

        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.embeddings[1] == [0.4, 0.5, 0.6]
        assert response.model == "test-embedding-model"
        assert response.usage == {"prompt_tokens": 10}

    def test_embedding_response_defaults(self):
        """Test EmbeddingResponse default values."""
        embeddings = [[0.1, 0.2, 0.3]]
        response = EmbeddingResponse(
            embeddings=embeddings,
            model="test-embedding-model",
        )

        assert len(response.embeddings) == 1
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.model == "test-embedding-model"
        assert response.usage is None


class TestMockLLMProvider:
    """Test MockLLMProvider functionality."""

    @pytest.mark.asyncio
    async def test_mock_provider_initialization(self, llm_config):
        """Test MockLLMProvider initialization."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()
        assert provider._initialized
        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_completion(self, llm_config):
        """Test MockLLMProvider completion."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()

        request = CompletionRequest(prompt="Test prompt")
        response = await provider.complete(request)

        assert response.text == "Mock completion response"
        assert response.model == "mock-model"
        assert response.usage is not None
        assert response.finish_reason == "stop"

        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_chat(self, llm_config):
        """Test MockLLMProvider chat."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()

        messages = [Message(role="user", content="Hello")]
        request = ChatRequest(messages=messages)
        response = await provider.chat(request)

        assert response.message.role == "assistant"
        assert response.message.content == "Mock chat response"
        assert response.model == "mock-model"
        assert response.usage is not None
        assert response.finish_reason == "stop"

        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_embedding_single(self, llm_config):
        """Test MockLLMProvider embedding with single string."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()

        request = EmbeddingRequest(input="Test text")
        response = await provider.embed(request)

        assert len(response.embeddings) == 1
        assert len(response.embeddings[0]) == 3
        assert response.model == "mock-embedding-model"
        assert response.usage is not None

        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_embedding_multiple(self, llm_config):
        """Test MockLLMProvider embedding with multiple strings."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()

        request = EmbeddingRequest(input=["Text 1", "Text 2", "Text 3"])
        response = await provider.embed(request)

        assert len(response.embeddings) == 3
        for embedding in response.embeddings:
            assert len(embedding) == 3
        assert response.model == "mock-embedding-model"
        assert response.usage is not None

        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_list_models(self, llm_config):
        """Test MockLLMProvider list models."""
        provider = MockLLMProvider(llm_config)
        await provider.initialize()

        models = await provider.list_models()
        assert models == ["mock-model-1", "mock-model-2"]

        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_mock_provider_health_check(self, llm_config):
        """Test MockLLMProvider health check."""
        provider = MockLLMProvider(llm_config)

        # Health check should fail when not initialized
        assert not await provider.health_check()

        # Health check should pass when initialized
        await provider.initialize()
        assert await provider.health_check()

        await provider.shutdown()


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""

    @pytest.mark.asyncio
    async def test_openai_provider_initialization(self, openai_config):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(openai_config)
        await provider.initialize()
        assert provider._initialized
        await provider.shutdown()

    @pytest.mark.asyncio
    async def test_openai_provider_missing_api_key(self):
        """Test OpenAI provider with missing API key."""
        config = OpenAIConfig(
            provider_name="openai",
            api_key=None,  # Missing API key
        )
        provider = OpenAIProvider(config)

        with pytest.raises(
            ComponentError,
            match="Initialization failed: Provider initialization failed: OpenAI API key is required",
        ):
            await provider.initialize()

    @pytest.mark.asyncio
    async def test_openai_provider_health_check_failure(
        self, openai_config, monkeypatch
    ):
        """Test OpenAI provider health check failure."""
        provider = OpenAIProvider(openai_config)

        # Mock the client to raise an exception
        async def mock_list_models():
            raise Exception("API error")

        provider._async_client = type(
            "MockClient",
            (),
            {"models": type("MockModels", (), {"list": mock_list_models})()},
        )()

        # Health check should return False when API fails
        assert not await provider._check_health()

    @pytest.mark.asyncio
    async def test_openai_provider_list_models_failure(
        self, openai_config, monkeypatch
    ):
        """Test OpenAI provider list models failure."""
        provider = OpenAIProvider(openai_config)

        # Mock the client to raise an exception
        async def mock_list_models():
            raise Exception("API error")

        provider._async_client = type(
            "MockClient",
            (),
            {"models": type("MockModels", (), {"list": mock_list_models})()},
        )()

        with pytest.raises(LLMProviderError, match="Failed to list models"):
            await provider._list_models()

    @pytest.mark.asyncio
    async def test_openai_provider_list_chat_models(self, openai_config, monkeypatch):
        """Test OpenAI provider list chat models."""
        provider = OpenAIProvider(openai_config)

        # Mock the client response
        mock_models = [
            type("MockModel", (), {"id": "gpt-3.5-turbo"})(),
            type("MockModel", (), {"id": "gpt-4"})(),
            type("MockModel", (), {"id": "text-embedding-ada-002"})(),
        ]

        async def mock_list_models(*args, **kwargs):
            return type("MockResponse", (), {"data": mock_models})()

        provider._async_client = type(
            "MockClient",
            (),
            {"models": type("MockModels", (), {"list": mock_list_models})()},
        )()

        chat_models = await provider.list_chat_models()
        assert chat_models == ["gpt-3.5-turbo", "gpt-4"]

    @pytest.mark.asyncio
    async def test_openai_provider_list_embedding_models(
        self, openai_config, monkeypatch
    ):
        """Test OpenAI provider list embedding models."""
        provider = OpenAIProvider(openai_config)

        # Mock the client response
        mock_models = [
            type("MockModel", (), {"id": "gpt-3.5-turbo"})(),
            type("MockModel", (), {"id": "text-embedding-ada-002"})(),
            type("MockModel", (), {"id": "text-embedding-3-small"})(),
        ]

        async def mock_list_models(*args, **kwargs):
            return type("MockResponse", (), {"data": mock_models})()

        provider._async_client = type(
            "MockClient",
            (),
            {"models": type("MockModels", (), {"list": mock_list_models})()},
        )()

        embedding_models = await provider.list_embedding_models()
        assert embedding_models == ["text-embedding-ada-002", "text-embedding-3-small"]


class TestExceptions:
    """Test exception classes."""

    def test_llm_error_inheritance(self):
        """Test LLMError inheritance."""
        error = LLMError("Test error")
        assert isinstance(error, LLMError)
        assert str(error) == "Test error"

    def test_llm_provider_error_inheritance(self):
        """Test LLMProviderError inheritance."""
        error = LLMProviderError("Provider error")
        assert isinstance(error, LLMError)
        assert str(error) == "Provider error"

    def test_llm_config_error_inheritance(self):
        """Test LLMConfigError inheritance."""
        error = LLMConfigError("Config error")
        assert isinstance(error, LLMError)
        assert str(error) == "Config error"

    def test_llm_request_error_inheritance(self):
        """Test LLMRequestError inheritance."""
        error = LLMRequestError("Request error")
        assert isinstance(error, LLMError)
        assert str(error) == "Request error"

    def test_llm_response_error_inheritance(self):
        """Test LLMResponseError inheritance."""
        error = LLMResponseError("Response error")
        assert isinstance(error, LLMError)
        assert str(error) == "Response error"
