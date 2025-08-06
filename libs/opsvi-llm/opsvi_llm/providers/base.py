"""
Abstract base class for LLM providers.

Defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..schemas.responses import ChatMessage, GenerationConfig, LLMResponse
from ..utils.retry import retry_with_backoff


class BaseLLMProvider(ABC):
    """
    Abstract base class defining the interface for LLM providers.

    All LLM providers must implement these methods to ensure
    consistent behavior across different services.
    """

    def __init__(self, model: str, **kwargs: Any):
        """
        Initialize the LLM provider.

        Args:
            model: Model identifier for the LLM service
            **kwargs: Additional provider-specific configuration
        """
        self.model = model
        self.config = kwargs
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate provider-specific configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    async def generate(
        self, prompt: str, config: GenerationConfig | None = None, **kwargs: Any
    ) -> LLMResponse:
        """
        Generate completion based on prompt.

        Args:
            prompt: Input prompt for generation
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with generated content

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def generate_chat(
        self,
        messages: list[ChatMessage],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate chat completion based on message history.

        Args:
            messages: List of chat messages
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with generated content

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    async def generate_with_functions(
        self,
        messages: list[ChatMessage],
        functions: list[dict[str, Any]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate completion with function calling support.

        Args:
            messages: List of chat messages
            functions: List of function definitions
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with function calls

        Raises:
            Exception: If generation fails
        """
        pass

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def generate_with_retry(
        self, prompt: str, config: GenerationConfig | None = None, **kwargs: Any
    ) -> LLMResponse:
        """
        Generate completion with automatic retry logic.

        Args:
            prompt: Input prompt for generation
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with generated content
        """
        return await self.generate(prompt, config, **kwargs)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def generate_chat_with_retry(
        self,
        messages: list[ChatMessage],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate chat completion with automatic retry logic.

        Args:
            messages: List of chat messages
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with generated content
        """
        return await self.generate_chat(messages, config, **kwargs)

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "model": self.model,
            "provider": self.__class__.__name__,
            "config": self.config,
        }

    def supports_function_calling(self) -> bool:
        """
        Check if the provider supports function calling.

        Returns:
            bool: True if function calling is supported
        """
        return hasattr(self, "generate_with_functions")

    def supports_streaming(self) -> bool:
        """
        Check if the provider supports streaming responses.

        Returns:
            bool: True if streaming is supported
        """
        return hasattr(self, "generate_stream")

    async def health_check(self) -> bool:
        """
        Perform a health check on the provider.

        Returns:
            bool: True if provider is healthy
        """
        try:
            # Simple health check with minimal prompt
            response = await self.generate("test", max_tokens=1)
            return bool(response and response.generated_text)
        except Exception:
            return False
