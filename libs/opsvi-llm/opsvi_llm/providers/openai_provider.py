"""
OpenAI provider implementation for OPSVI LLM Library.

Provides integration with OpenAI's API using the modern Python SDK.
"""

import logging
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..schemas.responses import (
    ChatMessage,
    FunctionCall,
    GenerationConfig,
    LLMResponse,
    MessageRole,
)
from ..utils.rate_limiting import RateLimitConfig, add_global_rate_limiter
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI SDK-based LLM provider supporting async generation with modern patterns.

    Provides comprehensive integration with OpenAI's API including:
    - Chat completions
    - Function calling
    - Streaming responses
    - Rate limiting
    - Retry logic
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        organization: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model identifier (e.g., "gpt-4", "gpt-3.5-turbo")
            organization: OpenAI organization ID (optional)
            base_url: Custom base URL for API calls (optional)
            **kwargs: Additional configuration options
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.organization = organization
        self.base_url = base_url

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key, organization=organization, base_url=base_url
        )

        # Setup rate limiting
        self._setup_rate_limiting()

        logger.info("OpenAI provider initialized with model: %s", model)

    def _validate_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        if not self.model:
            raise ValueError("Model identifier is required")

    def _setup_rate_limiting(self) -> None:
        """Setup rate limiting for OpenAI API."""
        # Default rate limits for OpenAI
        rate_limit_config = RateLimitConfig(
            requests_per_minute=60, requests_per_hour=1000, burst_size=10
        )
        add_global_rate_limiter("openai", rate_limit_config)

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

        await acquire_global_rate_limit("openai", timeout=30.0)

        # Prepare request parameters
        request_params = self._prepare_request_params(messages, config, **kwargs)

        try:
            logger.info("Sending chat completion request to OpenAI")

            # Make API call
            response = await self.client.chat.completions.create(**request_params)

            # Parse response
            return self._parse_chat_response(response, messages)

        except Exception as e:
            logger.exception("Error during OpenAI chat completion: %s", e)
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

        Args:
            messages: List of chat messages
            functions: List of function definitions
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Returns:
            LLMResponse: Structured response with function calls
        """
        # Apply rate limiting
        from ..utils.rate_limiting import acquire_global_rate_limit

        await acquire_global_rate_limit("openai", timeout=30.0)

        # Prepare request parameters
        request_params = self._prepare_request_params(messages, config, **kwargs)
        request_params["tools"] = [
            {"type": "function", "function": func} for func in functions
        ]
        request_params["tool_choice"] = "auto"

        try:
            logger.info("Sending function calling request to OpenAI")

            # Make API call
            response = await self.client.chat.completions.create(**request_params)

            # Parse response
            return self._parse_chat_response(response, messages)

        except Exception as e:
            logger.exception("Error during OpenAI function calling: %s", e)
            raise

    def _prepare_request_params(
        self,
        messages: list[ChatMessage],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Prepare request parameters for OpenAI API."""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}
            if msg.name:
                openai_msg["name"] = msg.name
            if msg.function_call:
                openai_msg["function_call"] = {
                    "name": msg.function_call.name,
                    "arguments": msg.function_call.arguments,
                }
            openai_messages.append(openai_msg)

        # Base parameters
        params = {
            "model": self.model,
            "messages": openai_messages,
        }

        # Apply configuration
        if config:
            if config.max_tokens:
                params["max_tokens"] = config.max_tokens
            params["temperature"] = config.temperature
            params["top_p"] = config.top_p
            if config.top_k:
                params["top_k"] = config.top_k
            params["frequency_penalty"] = config.frequency_penalty
            params["presence_penalty"] = config.presence_penalty
            if config.stop:
                params["stop"] = config.stop
            params["stream"] = config.stream

        # Apply additional kwargs
        params.update(kwargs)

        return params

    def _parse_chat_response(
        self, response: ChatCompletion, original_messages: list[ChatMessage]
    ) -> LLMResponse:
        """Parse OpenAI chat completion response."""
        if not response.choices:
            raise ValueError("No choices returned from OpenAI API")

        choice = response.choices[0]
        message = choice.message

        # Extract function calls
        function_calls = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    function_calls.append(
                        FunctionCall(
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )

        # Build response
        llm_response = LLMResponse(
            generated_text=message.content or "",
            messages=original_messages
            + [
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=message.content or "",
                    function_call=function_calls[0] if function_calls else None,
                )
            ],
            function_calls=function_calls if function_calls else None,
            metadata={
                "model": self.model,
                "finish_reason": choice.finish_reason,
                "usage": response.usage.model_dump() if response.usage else None,
            },
            model=self.model,
            finish_reason=choice.finish_reason,
            usage=response.usage.model_dump() if response.usage else None,
        )

        logger.info(
            "Received OpenAI response with %d tokens",
            response.usage.total_tokens if response.usage else 0,
        )

        return llm_response

    async def generate_stream(
        self,
        messages: list[ChatMessage],
        config: GenerationConfig | None = None,
        **kwargs: Any,
    ):
        """
        Generate streaming chat completion.

        Args:
            messages: List of chat messages
            config: Generation configuration parameters
            **kwargs: Additional generation parameters

        Yields:
            LLMResponse: Partial responses as they arrive
        """
        # Apply rate limiting
        from ..utils.rate_limiting import acquire_global_rate_limit

        await acquire_global_rate_limit("openai", timeout=30.0)

        # Prepare request parameters
        request_params = self._prepare_request_params(messages, config, **kwargs)
        request_params["stream"] = True

        try:
            logger.info("Starting streaming chat completion")

            async with self.client.chat.completions.create(**request_params) as stream:
                async for chunk in stream:
                    if chunk.choices:
                        choice = chunk.choices[0]
                        if choice.delta.content:
                            # Create partial response
                            partial_response = LLMResponse(
                                generated_text=choice.delta.content,
                                model=self.model,
                                metadata={"streaming": True},
                            )
                            yield partial_response

        except Exception as e:
            logger.exception("Error during OpenAI streaming: %s", e)
            raise

    def supports_function_calling(self) -> bool:
        """Check if the provider supports function calling."""
        return True

    def supports_streaming(self) -> bool:
        """Check if the provider supports streaming responses."""
        return True

    async def health_check(self) -> bool:
        """Perform a health check on the provider."""
        try:
            response = await self.generate("test", max_tokens=1)
            return bool(response and response.generated_text)
        except Exception as e:
            logger.warning("OpenAI health check failed: %s", e)
            return False
