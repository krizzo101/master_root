"""
OpenAI LLM provider implementation.

Provides integration with OpenAI's GPT models including chat completions,
function calling, and streaming responses.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from opsvi_foundation import (
    CircuitBreaker,
    CircuitBreakerConfig,
    ComponentError,
    RetryConfig,
    get_logger,
    retry,
)
from pydantic import BaseModel, Field

from ..core.exceptions import LLMError, LLMValidationError
from ..schemas.requests import ChatRequest
from ..schemas.responses import ChatMessage, FunctionCall, LLMResponse
from .base import BaseLLMProvider

# 2025 MODEL CONSTRAINTS - IRONCLAD ENFORCEMENT
APPROVED_MODELS = {"o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"}

FORBIDDEN_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-2024-08-06",
    "claude-3",
    "claude-3.5",
    "claude-3.5-sonnet",
    "gemini",
    "gemini-pro",
    "gemini-flash",
    "llama",
    "llama-3",
    "llama-3.1",
    "mistral",
    "mixtral",
    "codellama",
}


def validate_model_constraints(model: str) -> None:
    """Validate model against approved list (MANDATORY)."""
    if model in FORBIDDEN_MODELS:
        raise LLMValidationError(
            f"🚨 UNAUTHORIZED MODEL: {model} is FORBIDDEN. Use approved models only: {list(APPROVED_MODELS)}"
        )

    if model not in APPROVED_MODELS:
        raise LLMValidationError(
            f"🚨 UNAUTHORIZED MODEL: {model} not in approved list. Use: {list(APPROVED_MODELS)}"
        )


logger = get_logger(__name__)


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI provider."""

    api_key: str = Field(..., description="OpenAI API key")
    base_url: str | None = Field(default=None, description="Custom base URL")
    organization: str | None = Field(default=None, description="OpenAI organization")
    project: str | None = Field(default=None, description="OpenAI project")
    default_model: str = Field(
        default="gpt-4.1-mini", description="Default model to use"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: float = Field(default=60.0, description="Request timeout in seconds")
    max_tokens: int = Field(default=4096, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Default temperature")
    rate_limit_rpm: int = Field(
        default=3500, description="Rate limit requests per minute"
    )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider with chat completions and function calling.

    Features:
    - Chat completions with GPT models
    - Function calling support
    - Streaming responses
    - Automatic retries with exponential backoff
    - Circuit breaker for fault tolerance
    - Rate limiting
    """

    def __init__(self, config: OpenAIConfig):
        super().__init__()
        self.config = config

        # MANDATORY: Validate default model
        validate_model_constraints(config.default_model)

        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            organization=config.organization,
            project=config.project,
            max_retries=config.max_retries,
            timeout=config.timeout,
        )

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=5, recovery_timeout=60, success_threshold=3
            )
        )

        # Supported models (2025 APPROVED MODELS ONLY)
        self.supported_models = {
            "o4-mini": {
                "max_tokens": 128000,
                "supports_functions": True,
                "use_case": "reasoning",
            },
            "o3": {
                "max_tokens": 200000,
                "supports_functions": True,
                "use_case": "complex_reasoning",
            },
            "gpt-4.1-mini": {
                "max_tokens": 128000,
                "supports_functions": True,
                "use_case": "agent_execution",
            },
            "gpt-4.1": {
                "max_tokens": 1000000,
                "supports_functions": True,
                "use_case": "structured_outputs",
            },
            "gpt-4.1-nano": {
                "max_tokens": 16384,
                "supports_functions": True,
                "use_case": "fast_responses",
            },
        }

        logger.info(
            "OpenAI provider initialized",
            default_model=config.default_model,
            supported_models=len(self.supported_models),
        )

    async def _initialize(self) -> None:
        """Initialize the provider."""
        try:
            # Test connection
            await self.health_check()
            logger.info("OpenAI provider connection verified")

        except Exception as e:
            logger.error("OpenAI provider initialization failed", error=str(e))
            raise ComponentError(f"OpenAI provider initialization failed: {e}")

    @retry(RetryConfig(max_attempts=3, exceptions=(Exception,)))
    async def generate_chat(self, request: ChatRequest) -> LLMResponse:
        """Generate chat completion.

        Args:
            request: Chat completion request

        Returns:
            LLM response with generated content

        Raises:
            LLMError: If generation fails
            LLMValidationError: If request validation fails
        """
        self._validate_request(request)

        try:
            async with self.circuit_breaker.call(
                self._create_chat_completion, request
            ) as result:
                return await result

        except Exception as e:
            logger.error(
                "Chat generation failed",
                model=request.model,
                messages=len(request.messages),
                error=str(e),
            )
            raise LLMError(f"Chat generation failed: {e}")

    async def generate_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Generate streaming chat completion.

        Args:
            request: Chat completion request

        Yields:
            Content chunks as they arrive

        Raises:
            LLMError: If streaming fails
        """
        self._validate_request(request)

        try:
            async with self.circuit_breaker.call(
                self._create_chat_stream, request
            ) as stream:
                async for chunk in await stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(
                "Streaming generation failed", model=request.model, error=str(e)
            )
            raise LLMError(f"Streaming generation failed: {e}")

    async def generate_with_functions(self, request: ChatRequest) -> LLMResponse:
        """Generate chat completion with function calling.

        Args:
            request: Chat completion request with functions

        Returns:
            LLM response with function calls if any

        Raises:
            LLMError: If generation fails
            LLMValidationError: If functions are not supported
        """
        if not request.functions:
            return await self.generate_chat(request)

        model_info = self.supported_models.get(
            request.model or self.config.default_model
        )
        if not model_info or not model_info.get("supports_functions"):
            raise LLMValidationError(
                f"Model {request.model} does not support function calling"
            )

        return await self.generate_chat(request)

    async def _create_chat_completion(self, request: ChatRequest) -> LLMResponse:
        """Create chat completion using OpenAI API.

        Args:
            request: Chat completion request

        Returns:
            LLM response
        """
        # Build API request
        api_request = self._build_api_request(request)

        logger.debug(
            "Creating chat completion",
            model=api_request["model"],
            messages=len(api_request["messages"]),
            functions=len(api_request.get("functions", [])),
        )

        # Make API call
        response: ChatCompletion = await self.client.chat.completions.create(
            **api_request
        )

        # Convert to LLM response
        return self._convert_response(response)

    async def _create_chat_stream(
        self, request: ChatRequest
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Create streaming chat completion.

        Args:
            request: Chat completion request

        Yields:
            Chat completion chunks
        """
        # Build API request with streaming
        api_request = self._build_api_request(request)
        api_request["stream"] = True

        logger.debug(
            "Creating streaming chat completion",
            model=api_request["model"],
            messages=len(api_request["messages"]),
        )

        # Make streaming API call
        async for chunk in await self.client.chat.completions.create(**api_request):
            yield chunk

    def _build_api_request(self, request: ChatRequest) -> dict[str, Any]:
        """Build OpenAI API request from chat request.

        Args:
            request: Chat completion request

        Returns:
            OpenAI API request parameters
        """
        api_request = {
            "model": request.model or self.config.default_model,
            "messages": [msg.model_dump() for msg in request.messages],
            "max_tokens": request.max_tokens or self.config.max_tokens,
            "temperature": request.temperature
            if request.temperature is not None
            else self.config.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stop": request.stop,
            "user": request.user,
        }

        # Remove None values
        api_request = {k: v for k, v in api_request.items() if v is not None}

        # Add functions if provided
        if request.functions:
            api_request["functions"] = [func.model_dump() for func in request.functions]
            if request.function_call:
                api_request["function_call"] = request.function_call

        return api_request

    def _convert_response(self, response: ChatCompletion) -> LLMResponse:
        """Convert OpenAI response to LLM response.

        Args:
            response: OpenAI chat completion response

        Returns:
            LLM response
        """
        choice = response.choices[0]
        message = choice.message

        # Convert message
        chat_message = ChatMessage(
            role=message.role,
            content=message.content or "",
            name=getattr(message, "name", None),
        )

        # Convert function calls if any
        function_calls = []
        if hasattr(message, "function_call") and message.function_call:
            function_calls.append(
                FunctionCall(
                    name=message.function_call.name,
                    arguments=message.function_call.arguments,
                )
            )

        # Extract usage information
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            generated_text=message.content or "",
            messages=[chat_message],
            function_calls=function_calls,
            model=response.model,
            usage=usage,
            finish_reason=choice.finish_reason,
            metadata={
                "response_id": response.id,
                "created": response.created,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
            },
        )

    def _validate_request(self, request: ChatRequest) -> None:
        """Validate chat request.

        Args:
            request: Chat completion request

        Raises:
            LLMValidationError: If request is invalid
        """
        if not request.messages:
            raise LLMValidationError("Messages cannot be empty")

        model = request.model or self.config.default_model

        # MANDATORY: Validate model constraints
        validate_model_constraints(model)

        if model not in self.supported_models:
            raise LLMValidationError(f"Unsupported model: {model}")

        # Check token limits
        model_info = self.supported_models[model]
        max_tokens = request.max_tokens or self.config.max_tokens
        if max_tokens > model_info["max_tokens"]:
            raise LLMValidationError(
                f"Max tokens {max_tokens} exceeds model limit {model_info['max_tokens']}"
            )

    def get_supported_models(self) -> list[str]:
        """Get list of supported models.

        Returns:
            List of supported model names
        """
        return list(self.supported_models.keys())

    def supports_function_calling(self, model: str | None = None) -> bool:
        """Check if model supports function calling.

        Args:
            model: Model name, uses default if None

        Returns:
            True if model supports function calling
        """
        model = model or self.config.default_model
        model_info = self.supported_models.get(model, {})
        return model_info.get("supports_functions", False)

    def supports_streaming(self, model: str | None = None) -> bool:
        """Check if model supports streaming.

        Args:
            model: Model name, uses default if None

        Returns:
            True if model supports streaming (all OpenAI models do)
        """
        model = model or self.config.default_model
        return model in self.supported_models

    async def health_check(self) -> dict[str, Any]:
        """Perform health check.

        Returns:
            Health status information

        Raises:
            ComponentError: If health check fails
        """
        try:
            # Simple API test
            test_request = ChatRequest(
                messages=[ChatMessage(role="user", content="Hello")],
                model=self.config.default_model,
                max_tokens=1,
            )

            await self._create_chat_completion(test_request)

            return {
                "status": "healthy",
                "provider": "openai",
                "default_model": self.config.default_model,
                "supported_models": len(self.supported_models),
                "circuit_breaker_state": self.circuit_breaker.get_state(),
            }

        except Exception as e:
            logger.error("OpenAI health check failed", error=str(e))
            raise ComponentError(f"OpenAI health check failed: {e}")
