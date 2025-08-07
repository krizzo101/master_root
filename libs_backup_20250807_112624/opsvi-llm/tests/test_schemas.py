"""
Tests for response schemas in OPSVI LLM Library.
"""

import pytest
from pydantic import ValidationError

from opsvi_llm.schemas.responses import (
    ChatMessage,
    FunctionCall,
    GenerationConfig,
    LLMResponse,
    MessageRole,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_message_roles(self):
        """Test all message roles are defined."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.FUNCTION == "function"


class TestChatMessage:
    """Test ChatMessage schema."""

    def test_valid_chat_message(self):
        """Test creating a valid chat message."""
        message = ChatMessage(role=MessageRole.USER, content="Hello, world!")
        assert message.role == MessageRole.USER
        assert message.content == "Hello, world!"
        assert message.name is None
        assert message.function_call is None

    def test_chat_message_with_name(self):
        """Test chat message with name."""
        message = ChatMessage(
            role=MessageRole.ASSISTANT, content="Response", name="test_assistant"
        )
        assert message.name == "test_assistant"

    def test_chat_message_with_function_call(self):
        """Test chat message with function call."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param": "value"}'
        )
        message = ChatMessage(
            role=MessageRole.ASSISTANT, content="", function_call=function_call
        )
        assert message.function_call == function_call

    def test_invalid_empty_content(self):
        """Test that empty content is rejected for non-function messages."""
        with pytest.raises(ValidationError):
            ChatMessage(role=MessageRole.USER, content="")

    def test_function_message_empty_content(self):
        """Test that function messages can have empty content."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param": "value"}'
        )
        message = ChatMessage(
            role=MessageRole.FUNCTION, content="", function_call=function_call
        )
        assert message.content == ""


class TestFunctionCall:
    """Test FunctionCall schema."""

    def test_valid_function_call(self):
        """Test creating a valid function call."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param": "value"}'
        )
        assert function_call.name == "test_function"
        assert function_call.arguments == '{"param": "value"}'

    def test_invalid_arguments_type(self):
        """Test that arguments must be a string."""
        with pytest.raises(ValidationError):
            FunctionCall(
                name="test_function", arguments={"param": "value"}  # Should be string
            )


class TestLLMResponse:
    """Test LLMResponse schema."""

    def test_valid_llm_response(self):
        """Test creating a valid LLM response."""
        response = LLMResponse(generated_text="Generated content")
        assert response.generated_text == "Generated content"
        assert response.messages is None
        assert response.function_calls is None
        assert response.metadata == {}
        assert response.reasoning is None

    def test_llm_response_with_messages(self):
        """Test LLM response with messages."""
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello"),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]
        response = LLMResponse(generated_text="Hi there!", messages=messages)
        assert response.messages == messages

    def test_llm_response_with_function_calls(self):
        """Test LLM response with function calls."""
        function_calls = [
            FunctionCall(name="func1", arguments='{"a": 1}'),
            FunctionCall(name="func2", arguments='{"b": 2}'),
        ]
        response = LLMResponse(
            generated_text="Function response", function_calls=function_calls
        )
        assert response.function_calls == function_calls

    def test_llm_response_with_metadata(self):
        """Test LLM response with metadata."""
        metadata = {"model": "gpt-4", "tokens": 100}
        response = LLMResponse(generated_text="Content", metadata=metadata)
        assert response.metadata == metadata

    def test_invalid_empty_generated_text(self):
        """Test that empty generated_text is rejected."""
        with pytest.raises(ValidationError):
            LLMResponse(generated_text="")

    def test_invalid_generated_text_type(self):
        """Test that generated_text must be a string."""
        with pytest.raises(ValidationError):
            LLMResponse(generated_text=123)  # Should be string

    def test_llm_response_methods(self):
        """Test LLM response utility methods."""
        response = LLMResponse(
            generated_text="Test content",
            function_calls=[FunctionCall(name="test_func", arguments='{"a": 1}')],
        )

        assert response.get_content() == "Test content"
        assert response.has_function_calls() is True
        assert len(response.get_function_calls()) == 1
        assert response.get_function_calls()[0].name == "test_func"

    def test_llm_response_to_dict(self):
        """Test converting LLM response to dictionary."""
        response = LLMResponse(generated_text="Test content", model="gpt-4")
        response_dict = response.to_dict()
        assert response_dict["generated_text"] == "Test content"
        assert response_dict["model"] == "gpt-4"


class TestGenerationConfig:
    """Test GenerationConfig schema."""

    def test_valid_generation_config(self):
        """Test creating a valid generation config."""
        config = GenerationConfig()
        assert config.max_tokens is None
        assert config.temperature == 0.7
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0
        assert config.stream is False

    def test_generation_config_with_values(self):
        """Test generation config with custom values."""
        config = GenerationConfig(
            max_tokens=100,
            temperature=0.5,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.2,
            stream=True,
        )
        assert config.max_tokens == 100
        assert config.temperature == 0.5
        assert config.top_p == 0.9
        assert config.frequency_penalty == 0.1
        assert config.presence_penalty == 0.2
        assert config.stream is True

    def test_generation_config_validation(self):
        """Test generation config validation."""
        # Test temperature bounds
        with pytest.raises(ValidationError):
            GenerationConfig(temperature=3.0)  # Should be <= 2.0

        with pytest.raises(ValidationError):
            GenerationConfig(temperature=-1.0)  # Should be >= 0.0

        # Test top_p bounds
        with pytest.raises(ValidationError):
            GenerationConfig(top_p=1.5)  # Should be <= 1.0

        with pytest.raises(ValidationError):
            GenerationConfig(top_p=-0.1)  # Should be >= 0.0

        # Test penalty bounds
        with pytest.raises(ValidationError):
            GenerationConfig(frequency_penalty=3.0)  # Should be <= 2.0

        with pytest.raises(ValidationError):
            GenerationConfig(presence_penalty=-3.0)  # Should be >= -2.0

    def test_stop_sequences_validation(self):
        """Test stop sequences validation."""
        # String should be converted to list
        config = GenerationConfig(stop="END")
        assert config.stop == ["END"]

        # List should remain as list
        config = GenerationConfig(stop=["END", "STOP"])
        assert config.stop == ["END", "STOP"]

        # Invalid type should raise error
        with pytest.raises(ValidationError):
            GenerationConfig(stop=123)  # Should be string or list
