"""OpenAI provider for LLM services.

Comprehensive OpenAI integration for the OPSVI ecosystem
"""

import logging
from typing import Any, List, Optional

from openai import AsyncOpenAI
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


class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI provider."""

    # OpenAI-specific configuration
    organization: Optional[str] = Field(
        default=None, description="OpenAI organization ID"
    )

    # Model defaults
    default_model: str = Field(
        default="gpt-3.5-turbo", description="Default OpenAI model"
    )
    default_embedding_model: str = Field(
        default="text-embedding-ada-002", description="Default embedding model"
    )

    class Config:
        env_prefix = "OPSVI_LLM_OPENAI_"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, config: OpenAIConfig, **kwargs: Any) -> None:
        """Initialize OpenAI provider.

        Args:
            config: OpenAI configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.openai_config = config
        self._async_client: Optional[AsyncOpenAI] = None

    async def _create_client(self) -> AsyncOpenAI:
        """Create OpenAI async client."""
        if not self.openai_config.api_key:
            raise LLMProviderError("OpenAI API key is required")

        self._async_client = AsyncOpenAI(
            api_key=self.openai_config.api_key,
            organization=self.openai_config.organization,
            base_url=self.openai_config.base_url,
            timeout=self.openai_config.timeout,
        )

        return self._async_client

    async def _close_client(self) -> None:
        """Close OpenAI client."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None

    async def _check_health(self) -> bool:
        """Check OpenAI API health."""
        try:
            # Try to list models as a health check
            models = await self._async_client.models.list()
            return len(models.data) > 0
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Generate text completion using OpenAI."""
        try:
            model = request.model or self.openai_config.default_model

            response = await self._async_client.completions.create(
                model=model,
                prompt=request.prompt,
                max_tokens=request.max_tokens or self.openai_config.max_tokens,
                temperature=request.temperature or self.openai_config.temperature,
                stop=request.stop,
                stream=request.stream,
            )

            return CompletionResponse(
                text=response.choices[0].text,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            raise LLMProviderError(f"Completion failed: {e}") from e

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using OpenAI."""
        try:
            model = request.model or self.openai_config.default_model

            # Convert messages to OpenAI format
            openai_messages = []
            for msg in request.messages:
                openai_msg = {
                    "role": msg.role,
                    "content": msg.content,
                }
                if msg.name:
                    openai_msg["name"] = msg.name
                openai_messages.append(openai_msg)

            response = await self._async_client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=request.max_tokens or self.openai_config.max_tokens,
                temperature=request.temperature or self.openai_config.temperature,
                stop=request.stop,
                stream=request.stream,
            )

            choice = response.choices[0]
            message = Message(
                role=choice.message.role,
                content=choice.message.content,
                name=choice.message.name,
            )

            return ChatResponse(
                message=message,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}")
            raise LLMProviderError(f"Chat completion failed: {e}") from e

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate text embeddings using OpenAI."""
        try:
            model = request.model or self.openai_config.default_embedding_model

            # Handle single string or list of strings
            if isinstance(request.input, str):
                input_texts = [request.input]
            else:
                input_texts = request.input

            response = await self._async_client.embeddings.create(
                model=model,
                input=input_texts,
            )

            embeddings = [embedding.embedding for embedding in response.data]

            return EmbeddingResponse(
                embeddings=embeddings,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
            )
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise LLMProviderError(f"Embedding failed: {e}") from e

    async def _list_models(self) -> List[str]:
        """List available OpenAI models."""
        try:
            response = await self._async_client.models.list()
            return [model.id for model in response.data]
        except Exception as e:
            logger.error(f"Failed to list OpenAI models: {e}")
            raise LLMProviderError(f"Failed to list models: {e}") from e

    async def list_chat_models(self) -> List[str]:
        """List available chat models."""
        try:
            response = await self._async_client.models.list()
            # Filter for chat models (gpt models)
            chat_models = [
                model.id for model in response.data if model.id.startswith("gpt-")
            ]
            return chat_models
        except Exception as e:
            logger.error(f"Failed to list OpenAI chat models: {e}")
            raise LLMProviderError(f"Failed to list chat models: {e}") from e

    async def list_embedding_models(self) -> List[str]:
        """List available embedding models."""
        try:
            response = await self._async_client.models.list()
            # Filter for embedding models
            embedding_models = [
                model.id for model in response.data if "embedding" in model.id
            ]
            return embedding_models
        except Exception as e:
            logger.error(f"Failed to list OpenAI embedding models: {e}")
            raise LLMProviderError(f"Failed to list embedding models: {e}") from e
