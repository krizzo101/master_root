"""
Anthropic provider implementation for OPSVI LLM Library.

Provides integration with Anthropic's Claude API.
"""

import logging
from typing import Any

from anthropic import AsyncAnthropic

from ..schemas.responses import (
    ChatMessage,
    GenerationConfig,
    LLMResponse,
    MessageRole,
)
from ..utils.rate_limiting import RateLimitConfig, add_global_rate_limiter
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider implementation.

    Provides integration with Anthropic's Claude models including:
    - Chat completions
    - Streaming responses
    - Rate limiting
    - Retry logic
    """

    def __init__(
        self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs: Any
    ):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model identifier (e.g., "claude-3-sonnet-20240229")
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key

        # Initialize Anthropic client
        self.client = AsyncAnthropic(api_key=api_key)

        # Setup rate limiting
        self._setup_rate_limiting()

        logger.info("Anthropic provider initialized with model: %s", model)

    def _validate_config(self) -> None:
        """Validate Anthropic-specific configuration."""
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        if not self.model:
            raise ValueError("Model identifier is required")

    def _setup_rate_limiting(self) -> None:
        """Setup rate limiting for Anthropic API."""
        # Default rate limits for Anthropic
        rate_limit_config = RateLimitConfig(
            requests_per_minute=50, requests_per_hour=500, burst_size=5
        )
        add_global_rate_limiter("anthropic", rate_limit_config)

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
        """
        # Convert prompt to chat message
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        return await self.generate_chat(messages, config, **kwargs)

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
        """
        # Apply rate limiting
        from ..utils.rate_limiting import acquire_global_rate_limit

        await acquire_global_rate_limit("anthropic", timeout=30.0)

        # Prepare request parameters
        request_params = self._prepare_request_params(messages, config, **kwargs)

        try:
            logger.info("Sending chat completion request to Anthropic")

            # Make API call
            response = await self.client.messages.create(**request_params)

            # Parse response
            return self._parse_chat_response(response, messages)

        except Exception as e:
            logger.exception("Error during Anthropic chat completion: %s", e)
            raise

    async def generate_with_functions(
        self,
        messages: list[ChatMessage],
        functions: list[dict[str, Any]],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate completion with function calling support.

        Note: Anthropic's function calling support may differ from OpenAI's.
        This is a placeholder implementation.

        Args:
            messages: List of chat messages
            functions: List of function definitions
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with function calls
        """
        # For now, fall back to regular chat completion
        logger.warning("Function calling not yet implemented for Anthropic")
        return await self.generate_chat(messages, config, **kwargs)

    def _prepare_request_params(
        self,
        messages: list[ChatMessage],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare request parameters for Anthropic API."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            anthropic_msg = {"role": msg.role.value, "content": msg.content}
            anthropic_messages.append(anthropic_msg)

        # Base parameters
        params = {
            "model": self.model,
            "messages": anthropic_messages,
        }

        # Apply configuration
        if config:
            if config.max_tokens:
                params["max_tokens"] = config.max_tokens
            params["temperature"] = config.temperature
            if config.stop:
                params["stop_sequences"] = config.stop

        # Apply additional kwargs
        params.update(kwargs)

        return params

    def _parse_chat_response(
        self, response: Any, original_messages: list[ChatMessage]
    ) -> LLMResponse:
        """Parse Anthropic chat completion response."""
        # Extract content from response
        content = ""
        if response.content:
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    content += content_block.text

        # Build response
        llm_response = LLMResponse(
            generated_text=content,
            messages=original_messages
            + [ChatMessage(role=MessageRole.ASSISTANT, content=content)],
            metadata={
                "model": self.model,
                "usage": (
                    {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    }
                    if response.usage
                    else None
                ),
            },
            model=self.model,
            usage=(
                {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
                if response.usage
                else None
            ),
        )

        logger.info(
            "Received Anthropic response with %d output tokens",
            response.usage.output_tokens if response.usage else 0,
        )

        return llm_response

    def supports_function_calling(self) -> bool:
        """Check if the provider supports function calling."""
        return False  # Not yet implemented

    def supports_streaming(self) -> bool:
        """Check if the provider supports streaming responses."""
        return True

    async def health_check(self) -> bool:
        """Perform a health check on the provider."""
        try:
            response = await self.generate("test", max_tokens=1)
            return bool(response and response.generated_text)
        except Exception as e:
            logger.warning("Anthropic health check failed: %s", e)
            return False
