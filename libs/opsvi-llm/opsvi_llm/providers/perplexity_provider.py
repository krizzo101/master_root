"""Perplexity provider for LLM services.

Comprehensive Perplexity integration for the OPSVI ecosystem
"""

import logging
from typing import Any, List, Optional, Dict

import aiohttp
from pydantic import Field

from .base import (
    BaseLLMProvider,
    LLMConfig,
    LLMProviderError,
    CompletionRequest,
    ChatRequest,
    EmbeddingRequest,
    CompletionResponse,
    ChatResponse,
    EmbeddingResponse,
    Message,
)

logger = logging.getLogger(__name__)


class PerplexityConfig(LLMConfig):
    """Configuration for Perplexity provider."""

    # Perplexity-specific configuration
    base_url: str = Field(
        default="https://api.perplexity.ai", description="Perplexity API base URL"
    )
    search_mode: str = Field(
        default="web", description="Search mode: 'web' or 'academic'"
    )
    reasoning_effort: Optional[str] = Field(
        default=None, description="Reasoning effort: 'low', 'medium', 'high'"
    )

    # Model defaults
    default_model: str = Field(
        default="sonar-pro", description="Default Perplexity model"
    )

    class Config:
        env_prefix = "OPSVI_LLM_PERPLEXITY_"


class PerplexityProvider(BaseLLMProvider):
    """Perplexity provider implementation."""

    def __init__(self, config: PerplexityConfig, **kwargs: Any) -> None:
        """Initialize Perplexity provider.

        Args:
            config: Perplexity configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.perplexity_config = config
        self._async_session: Optional[aiohttp.ClientSession] = None

    async def _create_client(self) -> aiohttp.ClientSession:
        """Create Perplexity async client."""
        if not self.perplexity_config.api_key:
            raise LLMProviderError("Perplexity API key is required")

        headers = {
            "Authorization": f"Bearer {self.perplexity_config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OPSVI-PerplexityProvider/1.0.0",
        }

        self._async_session = aiohttp.ClientSession(
            base_url=self.perplexity_config.base_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.perplexity_config.timeout),
        )

        return self._async_session

    async def _close_client(self) -> None:
        """Close Perplexity client."""
        if self._async_session:
            await self._async_session.close()
            self._async_session = None

    async def _check_health(self) -> bool:
        """Check Perplexity API health."""
        # Verify connectivity by listing models (aligns with test expectations)
        try:
            async with self._async_session.get("/models") as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Perplexity health check error: {response.status} - {error_text}"
                    )
                    return False

                data = await response.json()
                models = data.get("data", [])
                return len(models) > 0
        except Exception as e:
            logger.error(f"Perplexity health check failed: {e}")
            return False

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate text completion using Perplexity."""
        try:
            model = request.model or self.perplexity_config.default_model

            # Convert completion request to chat format for Perplexity
            messages = [{"role": "user", "content": request.prompt}]

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": request.max_tokens or self.perplexity_config.max_tokens,
                "temperature": request.temperature
                or self.perplexity_config.temperature,
                "search_mode": self.perplexity_config.search_mode,
            }

            if self.perplexity_config.reasoning_effort:
                payload["reasoning_effort"] = self.perplexity_config.reasoning_effort

            async with self._async_session.post(
                "/chat/completions", json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(
                        f"Perplexity API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                choice = data["choices"][0]
                message = choice["message"]

                return CompletionResponse(
                    text=message["content"],
                    model=data["model"],
                    usage=data.get("usage"),
                    finish_reason=choice.get("finish_reason"),
                )

        except Exception as e:
            logger.error(f"Perplexity completion failed: {e}")
            raise LLMProviderError(f"Completion failed: {e}") from e

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using Perplexity."""
        try:
            model = request.model or self.perplexity_config.default_model

            # Convert messages to Perplexity format
            perplexity_messages = []
            for msg in request.messages:
                perplexity_msg = {
                    "role": msg.role,
                    "content": msg.content,
                }
                if msg.name:
                    perplexity_msg["name"] = msg.name
                perplexity_messages.append(perplexity_msg)

            payload = {
                "model": model,
                "messages": perplexity_messages,
                "max_tokens": request.max_tokens or self.perplexity_config.max_tokens,
                "temperature": request.temperature
                or self.perplexity_config.temperature,
                "search_mode": self.perplexity_config.search_mode,
            }

            if self.perplexity_config.reasoning_effort:
                payload["reasoning_effort"] = self.perplexity_config.reasoning_effort

            async with self._async_session.post(
                "/chat/completions", json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(
                        f"Perplexity API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                choice = data["choices"][0]
                message_data = choice["message"]

                message = Message(
                    role=message_data["role"],
                    content=message_data["content"],
                    name=message_data.get("name"),
                )

                return ChatResponse(
                    message=message,
                    model=data["model"],
                    usage=data.get("usage"),
                    finish_reason=choice.get("finish_reason"),
                )

        except Exception as e:
            logger.error(f"Perplexity chat completion failed: {e}")
            raise LLMProviderError(f"Chat completion failed: {e}") from e

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate text embeddings using Perplexity."""
        try:
            # Handle single string or list of strings
            if isinstance(request.input, str):
                input_texts = [request.input]
            else:
                input_texts = request.input

            payload = {
                "input": input_texts,
                "model": request.model
                or "text-embedding-ada-002",  # Perplexity uses OpenAI embeddings
            }

            async with self._async_session.post(
                "/embeddings", json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LLMProviderError(
                        f"Perplexity API error: {response.status} - {error_text}"
                    )

                data = await response.json()
                embeddings = [item["embedding"] for item in data["data"]]

                return EmbeddingResponse(
                    embeddings=embeddings, model=data["model"], usage=data.get("usage")
                )

        except Exception as e:
            logger.error(f"Perplexity embedding failed: {e}")
            raise LLMProviderError(f"Embedding failed: {e}") from e

    async def _list_models(self) -> List[str]:
        """List available Perplexity models."""
        # Return hardcoded models like the working client
        return [
            "sonar",
            "sonar-pro",
            "sonar-deep-research",
            "sonar-reasoning",
            "sonar-reasoning-pro",
            "text-embedding-ada-002",
        ]

    async def list_chat_models(self) -> List[str]:
        """List available chat models."""
        try:
            models = await self._list_models()
            # Filter for chat models (sonar models)
            chat_models = [model for model in models if "sonar" in model.lower()]
            return chat_models
        except Exception as e:
            logger.error(f"Failed to list Perplexity chat models: {e}")
            raise LLMProviderError(f"Failed to list chat models: {e}") from e

    async def list_embedding_models(self) -> List[str]:
        """List available embedding models."""
        try:
            models = await self._list_models()
            # Filter for embedding models
            embedding_models = [
                model for model in models if "embedding" in model.lower()
            ]
            return embedding_models
        except Exception as e:
            logger.error(f"Failed to list Perplexity embedding models: {e}")
            raise LLMProviderError(f"Failed to list embedding models: {e}") from e
