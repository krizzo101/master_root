"""
Base LLM provider interface.

Defines the abstract interface that all LLM providers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List

from opsvi_foundation import BaseComponent

from ..schemas.requests import ChatRequest, CompletionRequest
from ..schemas.responses import LLMResponse


class BaseLLMProvider(BaseComponent, ABC):
    """Abstract base class for all LLM providers.

    Defines the interface that all LLM providers must implement,
    including chat completions, streaming, and function calling.
    """

    @abstractmethod
    async def generate_chat(self, request: ChatRequest) -> LLMResponse:
        """Generate chat completion.

        Args:
            request: Chat completion request

        Returns:
            LLM response with generated content

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(self, request: ChatRequest) -> AsyncIterator[str]:
        """Generate streaming chat completion.

        Args:
            request: Chat completion request

        Yields:
            Content chunks as they arrive

        Raises:
            LLMError: If streaming fails
        """
        pass

    @abstractmethod
    async def generate_with_functions(self, request: ChatRequest) -> LLMResponse:
        """Generate chat completion with function calling.

        Args:
            request: Chat completion request with functions

        Returns:
            LLM response with function calls if any

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported models.

        Returns:
            List of supported model names
        """
        pass

    @abstractmethod
    def supports_function_calling(self, model: str | None = None) -> bool:
        """Check if model supports function calling.

        Args:
            model: Model name, uses default if None

        Returns:
            True if model supports function calling
        """
        pass

    @abstractmethod
    def supports_streaming(self, model: str | None = None) -> bool:
        """Check if model supports streaming.

        Args:
            model: Model name, uses default if None

        Returns:
            True if model supports streaming
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status information

        Raises:
            ComponentError: If health check fails
        """
        pass
