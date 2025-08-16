"""Base provider interface for LLM providers.

Comprehensive LLM provider abstraction for the OPSVI ecosystem
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging
from pydantic import BaseModel, Field

from opsvi_foundation import BaseComponent, ComponentError, BaseSettings

logger = logging.getLogger(__name__)


class LLMError(ComponentError):
    """Base exception for LLM errors."""

    pass


class LLMProviderError(LLMError):
    """Provider-specific errors."""

    pass


class LLMConfigError(LLMError):
    """Configuration errors."""

    pass


class LLMRequestError(LLMError):
    """Request errors."""

    pass


class LLMResponseError(LLMError):
    """Response errors."""

    pass


class LLMConfig(BaseSettings):
    """Base configuration for LLM providers."""

    # Provider configuration
    provider_name: str = Field(description="Name of the LLM provider")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    base_url: Optional[str] = Field(
        default=None, description="Base URL for the provider"
    )

    # Request configuration
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    # Model configuration
    default_model: str = Field(description="Default model to use")
    max_tokens: int = Field(default=4096, description="Maximum tokens for responses")
    temperature: float = Field(default=0.7, description="Temperature for generation")

    class Config:
        env_prefix = "OPSVI_LLM_"


class Message(BaseModel):
    """Message in a conversation."""

    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    name: Optional[str] = Field(default=None, description="Name of the message sender")


class CompletionRequest(BaseModel):
    """Request for text completion."""

    prompt: str = Field(description="Input prompt")
    model: Optional[str] = Field(default=None, description="Model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    temperature: Optional[float] = Field(default=None, description="Temperature")
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatRequest(BaseModel):
    """Request for chat completion."""

    messages: List[Message] = Field(description="List of messages")
    model: Optional[str] = Field(default=None, description="Model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    temperature: Optional[float] = Field(default=None, description="Temperature")
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    stream: bool = Field(default=False, description="Whether to stream the response")


class EmbeddingRequest(BaseModel):
    """Request for text embedding."""

    input: Union[str, List[str]] = Field(description="Text to embed")
    model: Optional[str] = Field(default=None, description="Model to use")


class CompletionResponse(BaseModel):
    """Response from text completion."""

    text: str = Field(description="Generated text")
    model: str = Field(description="Model used")
    usage: Optional[Dict[str, Any]] = Field(
        default=None, description="Usage information"
    )
    finish_reason: Optional[str] = Field(default=None, description="Finish reason")


class ChatResponse(BaseModel):
    """Response from chat completion."""

    message: Message = Field(description="Generated message")
    model: str = Field(description="Model used")
    usage: Optional[Dict[str, Any]] = Field(
        default=None, description="Usage information"
    )
    finish_reason: Optional[str] = Field(default=None, description="Finish reason")


class EmbeddingResponse(BaseModel):
    """Response from text embedding."""

    embeddings: List[List[float]] = Field(description="Embedding vectors")
    model: str = Field(description="Model used")
    usage: Optional[Dict[str, Any]] = Field(
        default=None, description="Usage information"
    )


class BaseLLMProvider(BaseComponent):
    """Base class for LLM providers.

    Provides common functionality for all LLM providers in the OPSVI ecosystem.
    """

    def __init__(self, config: LLMConfig, **kwargs: Any) -> None:
        """Initialize LLM provider.

        Args:
            config: Provider configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(f"llm-provider-{config.provider_name}", config.model_dump())
        self.config = config
        self._client: Optional[Any] = None

    async def _initialize_impl(self) -> None:
        """Initialize the provider client."""
        try:
            self._client = await self._create_client()
            logger.info(f"Initialized {self.config.provider_name} provider")
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.config.provider_name} provider: {e}"
            )
            raise LLMProviderError(f"Provider initialization failed: {e}") from e

    async def _shutdown_impl(self) -> None:
        """Shutdown the provider client."""
        try:
            if self._client:
                await self._close_client()
            logger.info(f"Shutdown {self.config.provider_name} provider")
        except Exception as e:
            logger.error(
                f"Failed to shutdown {self.config.provider_name} provider: {e}"
            )
            raise LLMProviderError(f"Provider shutdown failed: {e}") from e

    async def _health_check_impl(self) -> bool:
        """Health check implementation."""
        try:
            return await self._check_health()
        except Exception as e:
            logger.error(f"Health check failed for {self.config.provider_name}: {e}")
            return False

    @abstractmethod
    async def _create_client(self) -> Any:
        """Create the provider client."""
        pass

    @abstractmethod
    async def _close_client(self) -> None:
        """Close the provider client."""
        pass

    @abstractmethod
    async def _check_health(self) -> bool:
        """Check provider health."""
        pass

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate text completion."""
        pass

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion."""
        pass

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate text embeddings."""
        pass

    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            return await self._list_models()
        except Exception as e:
            logger.error(f"Failed to list models for {self.config.provider_name}: {e}")
            raise LLMProviderError(f"Failed to list models: {e}") from e

    @abstractmethod
    async def _list_models(self) -> List[str]:
        """List available models (implementation specific)."""
        pass
