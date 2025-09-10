"""
OpenAI Unified Interface - Supporting BOTH Chat Completions and Responses APIs

This interface provides access to both OpenAI APIs:
1. Chat Completions API - For standard chat-based interactions
2. Responses API - PREFERRED for new implementations with structured outputs

Based on 2025 OpenAI standards:
- Approved models: gpt-5, gpt-5-mini, gpt-5-nano, o3, o4-mini
- Forbidden models: gpt-4o series (all variants)

Usage Guidelines:
- Use Responses API for: New code, structured outputs, reasoning tasks
- Use Chat Completions API for: Legacy compatibility, simple text generation
"""

import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from .base import ChatRequest, ChatResponse, Message
from .openai_provider import OpenAIConfig, OpenAIProvider
from .openai_responses_interface import OpenAIResponsesInterface

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIUnifiedInterface:
    """
    Unified interface providing access to BOTH Chat Completions and Responses APIs.

    This is the recommended interface for all OpenAI interactions in the OPSVI ecosystem.
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        Initialize the unified interface with both API capabilities.

        Args:
            config: OpenAI configuration (uses defaults if not provided)
        """
        # Use provided config or create default
        self.config = config or OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            default_model="gpt-5-mini",
            enable_audit_logging=True,
            enable_sanitization=True,
        )

        # Initialize the main provider (has both APIs)
        self.provider = OpenAIProvider(self.config)

        # Initialize the specialized Responses interface
        self.responses_interface = OpenAIResponsesInterface()

        logger.info(
            f"OpenAI Unified Interface initialized with model: {self.config.default_model}"
        )

    # ============================================================================
    # RESPONSES API (PREFERRED FOR NEW CODE)
    # ============================================================================

    async def responses_create(
        self,
        input: Union[str, List[Dict[str, Any]]],
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ):
        """
        Create a response using the Responses API (PREFERRED).

        This is the recommended method for new implementations.

        Args:
            input: Text or message list input
            model: Model to use (auto-selected if None)
            instructions: System instructions
            reasoning_effort: For o3/o4-mini models - "low", "medium", "high"
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            tools: Tools/functions available
            stream: Enable streaming
            **kwargs: Additional parameters

        Returns:
            Response object

        Example:
            >>> response = await interface.responses_create(
            ...     input="Explain quantum computing",
            ...     model="o4-mini",
            ...     reasoning_effort="medium"
            ... )
        """
        return await self.provider.responses_create(
            input=input,
            model=model,
            instructions=instructions,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=stream,
            **kwargs,
        )

    async def responses_create_structured(
        self,
        input: Union[str, List[Dict[str, Any]]],
        response_model: Type[T],
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> T:
        """
        Create a structured response using the Responses API.

        Returns a validated Pydantic model instance.

        Args:
            input: Text or message list input
            response_model: Pydantic model for response structure
            model: Model to use (defaults to gpt-5 for structured outputs)
            instructions: System instructions
            reasoning_effort: For reasoning models
            temperature: Generation temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Instance of response_model

        Example:
            >>> class Analysis(BaseModel):
            ...     summary: str
            ...     sentiment: str
            ...     confidence: float
            ...
            >>> result = await interface.responses_create_structured(
            ...     input="Analyze this text...",
            ...     response_model=Analysis,
            ...     model="gpt-5"
            ... )
        """
        return await self.provider.responses_create_with_structured_output(
            input=input,
            response_model=response_model,
            model=model,
            instructions=instructions,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def responses_from_messages(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ):
        """
        Create a response from Message objects using Responses API.

        Convenience method for message-based interactions.

        Args:
            messages: List of Message objects
            model: Model to use
            instructions: System instructions
            reasoning_effort: For reasoning models
            temperature: Generation temperature
            max_tokens: Maximum tokens
            tools: Available tools
            stream: Enable streaming
            **kwargs: Additional parameters

        Returns:
            Response object
        """
        return await self.provider.responses_create_from_messages(
            messages=messages,
            model=model,
            instructions=instructions,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=stream,
            **kwargs,
        )

    # ============================================================================
    # CHAT COMPLETIONS API (FOR COMPATIBILITY)
    # ============================================================================

    async def chat_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse:
        """
        Create a chat completion using the Chat Completions API.

        Use this for backward compatibility or when Responses API features
        are not needed.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to gpt-5-mini)
            temperature: Generation temperature
            max_tokens: Maximum tokens
            stream: Enable streaming
            **kwargs: Additional parameters

        Returns:
            ChatResponse object

        Example:
            >>> response = await interface.chat_completion(
            ...     messages=[
            ...         Message(role="system", content="You are helpful"),
            ...         Message(role="user", content="Hello!")
            ...     ],
            ...     model="gpt-5-mini"
            ... )
        """
        request = ChatRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs,
        )
        return await self.provider.chat(request)

    async def chat_completion_structured(
        self,
        messages: List[Message],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> T:
        """
        Create a structured chat completion.

        Uses Chat Completions API with structured output parsing.

        Args:
            messages: List of chat messages
            response_model: Pydantic model for response
            model: Model to use
            temperature: Generation temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters

        Returns:
            Instance of response_model
        """
        return await self.provider.create_structured_response(
            messages=messages,
            response_model=response_model,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def select_api_for_task(self, task_type: str) -> str:
        """
        Recommend which API to use based on task type.

        Args:
            task_type: Type of task (reasoning, chat, structured, tool_use)

        Returns:
            "responses" or "chat_completions"

        Example:
            >>> api_type = interface.select_api_for_task("reasoning")
            >>> # Returns: "responses"
        """
        responses_preferred = [
            "reasoning",
            "structured",
            "tool_use",
            "function_calling",
            "complex_generation",
            "multi_step",
        ]

        if task_type.lower() in responses_preferred:
            return "responses"
        return "chat_completions"

    def select_model_for_task(
        self, task_type: str, complexity: str = "standard"
    ) -> str:
        """
        Select optimal model based on task type and complexity.

        Args:
            task_type: Type of task
            complexity: Task complexity (simple, standard, complex)

        Returns:
            Model name

        Example:
            >>> model = interface.select_model_for_task("reasoning", "complex")
            >>> # Returns: "o3"
        """
        return self.provider.select_model_for_task(task_type, complexity)

    async def compare_apis(
        self, input_text: str, model: str = "gpt-5-mini"
    ) -> Dict[str, Any]:
        """
        Compare responses from both APIs for the same input.

        Useful for testing and validation.

        Args:
            input_text: Input text to test
            model: Model to use for both APIs

        Returns:
            Dictionary with both responses and timing

        Example:
            >>> comparison = await interface.compare_apis(
            ...     "Explain the difference between APIs",
            ...     model="gpt-5-mini"
            ... )
        """
        import time

        # Test Responses API
        start_responses = time.time()
        try:
            responses_result = await self.responses_create(
                input=input_text, model=model
            )
            responses_time = time.time() - start_responses
            responses_output = responses_result
        except Exception as e:
            responses_output = f"Error: {e}"
            responses_time = -1

        # Test Chat Completions API
        start_chat = time.time()
        try:
            chat_result = await self.chat_completion(
                messages=[Message(role="user", content=input_text)], model=model
            )
            chat_time = time.time() - start_chat
            chat_output = chat_result.message.content
        except Exception as e:
            chat_output = f"Error: {e}"
            chat_time = -1

        return {
            "input": input_text,
            "model": model,
            "responses_api": {
                "output": responses_output,
                "time": responses_time,
            },
            "chat_completions_api": {
                "output": chat_output,
                "time": chat_time,
            },
            "recommendation": "responses" if responses_time > 0 else "chat_completions",
        }

    # ============================================================================
    # MODEL VALIDATION
    # ============================================================================

    def validate_model(self, model: str) -> bool:
        """
        Validate if a model is approved for use.

        Args:
            model: Model name to validate

        Returns:
            True if approved, raises ValueError if forbidden
        """
        from .openai_model_validator import OpenAIModelValidator

        return OpenAIModelValidator.validate_model(model)

    def get_approved_models(self) -> Dict[str, List[str]]:
        """
        Get list of approved models by category.

        Returns:
            Dictionary of model categories and their models
        """
        return {
            "reasoning": ["o4-mini", "o3"],
            "execution": ["gpt-5-mini", "gpt-5"],
            "fast": ["gpt-5-nano"],
            "structured": ["gpt-5", "gpt-5-mini"],
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================


async def example_usage():
    """
    Example usage demonstrating both APIs.
    """
    # Initialize interface
    interface = OpenAIUnifiedInterface()

    # Example 1: Responses API (Preferred)
    print("=" * 60)
    print("EXAMPLE 1: Responses API (Preferred)")
    print("=" * 60)

    response = await interface.responses_create(
        input="Explain the benefits of the Responses API",
        model="gpt-5-mini",
        instructions="Be concise and technical",
    )
    print(f"Responses API result: {response}")

    # Example 2: Chat Completions API (Compatibility)
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Chat Completions API (Compatibility)")
    print("=" * 60)

    chat_response = await interface.chat_completion(
        messages=[
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="What is the Chat Completions API?"),
        ],
        model="gpt-5-mini",
    )
    print(f"Chat API result: {chat_response.message.content}")

    # Example 3: Structured Output with Responses API
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Structured Output")
    print("=" * 60)

    class CodeAnalysis(BaseModel):
        language: str
        complexity: str
        suggestions: List[str]

    structured_result = await interface.responses_create_structured(
        input="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
        response_model=CodeAnalysis,
        model="gpt-5",
    )
    print(f"Structured result: {structured_result}")

    # Example 4: Reasoning with o4-mini
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Reasoning Model")
    print("=" * 60)

    reasoning_response = await interface.responses_create(
        input="Solve: If 3x + 7 = 22, what is x?",
        model="o4-mini",
        reasoning_effort="medium",
    )
    print(f"Reasoning result: {reasoning_response}")

    # Example 5: API Comparison
    print("\n" + "=" * 60)
    print("EXAMPLE 5: API Comparison")
    print("=" * 60)

    comparison = await interface.compare_apis(
        "Generate a haiku about programming", model="gpt-5-nano"
    )
    print(f"API Comparison:\n{comparison}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
