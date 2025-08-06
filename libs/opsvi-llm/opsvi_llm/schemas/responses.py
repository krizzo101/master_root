"""
Response schemas for OPSVI LLM Library.

Provides Pydantic V2 models for structured LLM responses and data validation.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class MessageRole(str, Enum):
    """Enumeration of message roles in chat conversations."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatMessage(BaseModel):
    """
    Structured chat message with role and content.

    Attributes:
        role: The role of the message sender
        content: The message content
        name: Optional name for the message sender
        function_call: Optional function call information
    """

    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    name: str | None = Field(None, description="Optional name for the message sender")
    function_call: Optional["FunctionCall"] = Field(
        None, description="Optional function call information"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_content(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate that content is provided for non-function messages."""
        if isinstance(values, dict):
            role = values.get("role")
            content = values.get("content")
            function_call = values.get("function_call")

            # Allow empty content only for function messages with function_call
            if role != MessageRole.FUNCTION and (not content or not content.strip()):
                if not function_call:
                    raise ValueError("Content is required for non-function messages")

        return values


class FunctionCall(BaseModel):
    """
    Function call information for structured outputs.

    Attributes:
        name: Name of the function to call
        arguments: JSON string containing function arguments
    """

    name: str = Field(..., description="Name of the function to call")
    arguments: str = Field(..., description="JSON string containing function arguments")

    @model_validator(mode="before")
    @classmethod
    def validate_arguments(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate that arguments is a valid JSON string."""
        if isinstance(values, dict):
            arguments = values.get("arguments")
            if arguments and not isinstance(arguments, str):
                raise ValueError("Arguments must be a JSON string")

        return values


class LLMResponse(BaseModel):
    """
    Structured schema for LLM responses with comprehensive metadata.

    Attributes:
        generated_text: The main generated text content
        messages: List of chat messages (for chat completions)
        function_calls: List of function calls made
        metadata: Additional response metadata
        reasoning: Optional reasoning or explanation
        usage: Token usage information
        model: Model used for generation
        finish_reason: Reason for completion
    """

    generated_text: str = Field(..., description="Main generated text content")
    messages: list[ChatMessage] | None = Field(
        default=None, description="List of chat messages"
    )
    function_calls: list[FunctionCall] | None = Field(
        default=None, description="List of function calls"
    )
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional response metadata"
    )
    reasoning: str | None = Field(None, description="Optional reasoning or explanation")
    usage: dict[str, Any] | None = Field(None, description="Token usage information")
    model: str | None = Field(None, description="Model used for generation")
    finish_reason: str | None = Field(None, description="Reason for completion")

    @model_validator(mode="before")
    @classmethod
    def validate_generated_text(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate that generated_text is a non-empty string."""
        if isinstance(values, dict):
            text = values.get("generated_text")
            if not text or not isinstance(text, str):
                raise ValueError("generated_text must be a non-empty string")

        return values

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return self.model_dump()

    def get_content(self) -> str:
        """Get the main content of the response."""
        return self.generated_text

    def has_function_calls(self) -> bool:
        """Check if the response contains function calls."""
        return bool(self.function_calls)

    def get_function_calls(self) -> list[FunctionCall]:
        """Get function calls from the response."""
        return self.function_calls or []


class GenerationConfig(BaseModel):
    """
    Configuration for LLM generation parameters.

    Attributes:
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (0.0 to 2.0)
        top_p: Nucleus sampling parameter (0.0 to 1.0)
        top_k: Top-k sampling parameter
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        presence_penalty: Presence penalty (-2.0 to 2.0)
        stop: Stop sequences
        stream: Whether to stream the response
    """

    max_tokens: int | None = Field(
        None, description="Maximum number of tokens to generate"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int | None = Field(None, ge=1, description="Top-k sampling parameter")
    frequency_penalty: float = Field(
        0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float = Field(
        0.0, ge=-2.0, le=2.0, description="Presence penalty"
    )
    stop: str | list[str] | None = Field(None, description="Stop sequences")
    stream: bool = Field(False, description="Whether to stream the response")

    @model_validator(mode="before")
    @classmethod
    def validate_stop_sequences(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate stop sequences."""
        if isinstance(values, dict):
            stop = values.get("stop")
            if stop is not None:
                if isinstance(stop, str):
                    values["stop"] = [stop]
                elif not isinstance(stop, list):
                    raise ValueError("Stop must be a string or list of strings")

        return values
