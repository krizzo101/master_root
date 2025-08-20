"""
Anthropic Claude provider for opsvi-llm
Provides integration with Anthropic's Claude models
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

try:
    from anthropic import Anthropic, AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import (
    BaseLLMProvider,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    LLMConfig,
    LLMProviderError,
    LLMRequestError,
    Message,
)


@dataclass
class AnthropicConfig(LLMConfig):
    """Configuration for Anthropic provider"""

    api_key: Optional[str] = None
    model: str = "claude-3-5-sonnet-20241022"  # Latest Claude 3.5 Sonnet
    max_tokens: int = 8192  # Increased default
    temperature: float = 0.7
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    timeout: Optional[float] = 600.0
    max_retries: int = 2
    base_url: Optional[str] = None

    def __post_init__(self):
        """Initialize with environment variables if not provided"""
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMProviderError(
                "Anthropic API key not provided and ANTHROPIC_API_KEY not set"
            )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation"""

    def __init__(self, config: Optional[AnthropicConfig] = None, **kwargs):
        """Initialize Anthropic provider

        Args:
            config: AnthropicConfig object or None
            **kwargs: Additional config parameters
        """
        if not ANTHROPIC_AVAILABLE:
            raise LLMProviderError(
                "Anthropic library not installed. Install with: pip install anthropic"
            )

        # Create config from kwargs if not provided
        if config is None:
            config = AnthropicConfig(**kwargs)

        super().__init__(config)

        # Initialize Anthropic clients
        self.client = Anthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        self.async_client = AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Convert Message objects to Anthropic format

        Args:
            messages: List of Message objects

        Returns:
            List of message dicts for Anthropic API
        """
        anthropic_messages = []

        for msg in messages:
            # Handle Message object or dict
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                role = msg.role
                content = msg.content

            # Anthropic uses 'user' and 'assistant' roles
            # Convert 'system' to user with prefix
            if role == "system":
                anthropic_messages.append(
                    {"role": "user", "content": f"System: {content}"}
                )
            else:
                anthropic_messages.append({"role": role, "content": content})

        return anthropic_messages

    def _extract_system_prompt(self, messages: List[Message]) -> Optional[str]:
        """Extract system prompt from messages

        Args:
            messages: List of Message objects

        Returns:
            System prompt string or None
        """
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "system":
                    return msg.get("content")
            elif msg.role == "system":
                return msg.content
        return None

    def chat(self, request: Union[ChatRequest, Dict[str, Any]]) -> ChatResponse:
        """Synchronous chat completion

        Args:
            request: ChatRequest object or dict with messages

        Returns:
            ChatResponse object
        """
        try:
            # Handle dict or ChatRequest
            if isinstance(request, dict):
                messages = request.get("messages", [])
                model = request.get("model", self.config.model)
                max_tokens = request.get("max_tokens", self.config.max_tokens)
                temperature = request.get("temperature", self.config.temperature)
                top_p = request.get("top_p", self.config.top_p)
                top_k = request.get("top_k", self.config.top_k)
                stop_sequences = request.get(
                    "stop_sequences", self.config.stop_sequences
                )
            else:
                messages = request.messages
                model = request.model or self.config.model
                max_tokens = request.max_tokens or self.config.max_tokens
                temperature = request.temperature or self.config.temperature
                top_p = getattr(request, "top_p", self.config.top_p)
                top_k = getattr(request, "top_k", self.config.top_k)
                stop_sequences = getattr(
                    request, "stop_sequences", self.config.stop_sequences
                )

            # Extract system prompt if present
            system_prompt = self._extract_system_prompt(messages)

            # Convert messages to Anthropic format (skip system messages)
            anthropic_messages = [
                msg
                for msg in self._convert_messages(messages)
                if msg["role"] != "user" or not msg["content"].startswith("System:")
            ]

            # Build request parameters
            request_params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if system_prompt:
                request_params["system"] = system_prompt
            if top_p is not None:
                request_params["top_p"] = top_p
            if top_k is not None:
                request_params["top_k"] = top_k
            if stop_sequences:
                request_params["stop_sequences"] = stop_sequences

            # Make API call
            response = self.client.messages.create(**request_params)

            # Convert to ChatResponse
            return ChatResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            raise LLMRequestError(f"Anthropic chat request failed: {str(e)}")

    async def chat_async(
        self, request: Union[ChatRequest, Dict[str, Any]]
    ) -> ChatResponse:
        """Asynchronous chat completion

        Args:
            request: ChatRequest object or dict with messages

        Returns:
            ChatResponse object
        """
        try:
            # Handle dict or ChatRequest
            if isinstance(request, dict):
                messages = request.get("messages", [])
                model = request.get("model", self.config.model)
                max_tokens = request.get("max_tokens", self.config.max_tokens)
                temperature = request.get("temperature", self.config.temperature)
                top_p = request.get("top_p", self.config.top_p)
                top_k = request.get("top_k", self.config.top_k)
                stop_sequences = request.get(
                    "stop_sequences", self.config.stop_sequences
                )
            else:
                messages = request.messages
                model = request.model or self.config.model
                max_tokens = request.max_tokens or self.config.max_tokens
                temperature = request.temperature or self.config.temperature
                top_p = getattr(request, "top_p", self.config.top_p)
                top_k = getattr(request, "top_k", self.config.top_k)
                stop_sequences = getattr(
                    request, "stop_sequences", self.config.stop_sequences
                )

            # Extract system prompt if present
            system_prompt = self._extract_system_prompt(messages)

            # Convert messages to Anthropic format
            anthropic_messages = [
                msg
                for msg in self._convert_messages(messages)
                if msg["role"] != "user" or not msg["content"].startswith("System:")
            ]

            # Build request parameters
            request_params = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            if system_prompt:
                request_params["system"] = system_prompt
            if top_p is not None:
                request_params["top_p"] = top_p
            if top_k is not None:
                request_params["top_k"] = top_k
            if stop_sequences:
                request_params["stop_sequences"] = stop_sequences

            # Make async API call
            response = await self.async_client.messages.create(**request_params)

            # Convert to ChatResponse
            return ChatResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            raise LLMRequestError(f"Anthropic async chat request failed: {str(e)}")

    def complete(
        self, request: Union[CompletionRequest, Dict[str, Any]]
    ) -> CompletionResponse:
        """Synchronous text completion (uses chat under the hood)

        Args:
            request: CompletionRequest object or dict with prompt

        Returns:
            CompletionResponse object
        """
        # Convert completion to chat format
        if isinstance(request, dict):
            prompt = request.get("prompt", "")
            messages = [{"role": "user", "content": prompt}]
            chat_request = {
                "messages": messages,
                "model": request.get("model", self.config.model),
                "max_tokens": request.get("max_tokens", self.config.max_tokens),
                "temperature": request.get("temperature", self.config.temperature),
            }
        else:
            messages = [Message(role="user", content=request.prompt)]
            chat_request = ChatRequest(
                messages=messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

        # Use chat completion
        chat_response = self.chat(chat_request)

        # Convert to CompletionResponse
        return CompletionResponse(
            text=chat_response.content,
            model=chat_response.model,
            usage=chat_response.usage,
            finish_reason=chat_response.finish_reason,
            raw_response=chat_response.raw_response,
        )

    async def complete_async(
        self, request: Union[CompletionRequest, Dict[str, Any]]
    ) -> CompletionResponse:
        """Asynchronous text completion (uses chat under the hood)

        Args:
            request: CompletionRequest object or dict with prompt

        Returns:
            CompletionResponse object
        """
        # Convert completion to chat format
        if isinstance(request, dict):
            prompt = request.get("prompt", "")
            messages = [{"role": "user", "content": prompt}]
            chat_request = {
                "messages": messages,
                "model": request.get("model", self.config.model),
                "max_tokens": request.get("max_tokens", self.config.max_tokens),
                "temperature": request.get("temperature", self.config.temperature),
            }
        else:
            messages = [Message(role="user", content=request.prompt)]
            chat_request = ChatRequest(
                messages=messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

        # Use async chat completion
        chat_response = await self.chat_async(chat_request)

        # Convert to CompletionResponse
        return CompletionResponse(
            text=chat_response.content,
            model=chat_response.model,
            usage=chat_response.usage,
            finish_reason=chat_response.finish_reason,
            raw_response=chat_response.raw_response,
        )

    def list_models(self) -> List[str]:
        """List available Anthropic models

        Returns:
            List of model names
        """
        return [
            # Claude Opus 4.1 (Latest generation)
            "claude-opus-4-1-20250805",
            # Claude Sonnet 4 (Latest generation)
            "claude-sonnet-4-20250514",
            # Claude 3.5 models
            "claude-3-5-sonnet-20241022",  # Latest 3.5 Sonnet
            "claude-3-5-sonnet-20240620",  # Previous 3.5 Sonnet
            "claude-3-5-haiku-20241022",  # Latest 3.5 Haiku
            # Claude 3 models
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            # Legacy models
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model

        Args:
            model: Model name

        Returns:
            Dict with model information
        """
        model_info = {
            # Claude Opus 4.1
            "claude-opus-4-1-20250805": {
                "max_tokens": 8192,
                "context_window": 200000,
                "description": "Most capable and intelligent model, sets new standards in complex reasoning",
            },
            # Claude Sonnet 4
            "claude-sonnet-4-20250514": {
                "max_tokens": 8192,
                "context_window": 200000,
                "description": "High-performance model with exceptional reasoning and efficiency",
            },
            # Claude 3.5 models
            "claude-3-5-sonnet-20241022": {
                "max_tokens": 8192,
                "context_window": 200000,
                "description": "Latest Claude 3.5 Sonnet with computer use capabilities",
            },
            "claude-3-5-sonnet-20240620": {
                "max_tokens": 8192,
                "context_window": 200000,
                "description": "Previous Claude 3.5 Sonnet, strong vision and reasoning",
            },
            "claude-3-5-haiku-20241022": {
                "max_tokens": 8192,
                "context_window": 200000,
                "description": "Fast and affordable Claude 3.5 model",
            },
            # Claude 3 models
            "claude-3-opus-20240229": {
                "max_tokens": 4096,
                "context_window": 200000,
                "description": "Most capable Claude 3 model",
            },
            "claude-3-sonnet-20240229": {
                "max_tokens": 4096,
                "context_window": 200000,
                "description": "Balanced Claude 3 model",
            },
            "claude-3-haiku-20240307": {
                "max_tokens": 4096,
                "context_window": 200000,
                "description": "Fastest Claude 3 model",
            },
            # Legacy models
            "claude-2.1": {
                "max_tokens": 4096,
                "context_window": 200000,
                "description": "Claude 2.1 with 200k context",
            },
            "claude-2.0": {
                "max_tokens": 4096,
                "context_window": 100000,
                "description": "Claude 2.0 with 100k context",
            },
            "claude-instant-1.2": {
                "max_tokens": 4096,
                "context_window": 100000,
                "description": "Fast, affordable Claude model",
            },
        }

        return model_info.get(
            model,
            {
                "error": f"Unknown model: {model}",
                "available_models": list(model_info.keys()),
            },
        )
