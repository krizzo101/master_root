# OPSVI LLM Library

Unified LLM integration library for the OPSVI ecosystem. Provides interfaces for OpenAI, Anthropic, and other LLM providers with structured outputs and modern async patterns.

## Features

- **Multi-Provider Support**: Unified interface for OpenAI, Anthropic, and other LLM providers
- **Structured Outputs**: Pydantic V2 models for type-safe responses and validation
- **Async Support**: Full async/await support throughout the library
- **Function Calling**: Support for structured function calling and tool use
- **Rate Limiting**: Built-in rate limiting to prevent API quota exhaustion
- **Retry Logic**: Exponential backoff retry for handling transient failures
- **Streaming**: Support for streaming responses
- **Production Ready**: Comprehensive error handling, logging, and testing

## Installation

```bash
# Install from local development
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with documentation dependencies
pip install -e ".[docs]"
```

## Quick Start

### Basic Usage

```python
import asyncio
from opsvi_llm import OpenAIProvider, ChatMessage, MessageRole

async def main():
    # Initialize provider
    provider = OpenAIProvider(
        api_key="your-openai-api-key",
        model="gpt-4"
    )

    # Simple text generation
    response = await provider.generate("Explain quantum computing in simple terms")
    print(response.generated_text)

    # Chat completion
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=MessageRole.USER, content="What is the capital of France?")
    ]

    chat_response = await provider.generate_chat(messages)
    print(chat_response.generated_text)

asyncio.run(main())
```

### Function Calling

```python
import asyncio
from opsvi_llm import OpenAIProvider, ChatMessage, MessageRole

async def main():
    provider = OpenAIProvider(api_key="your-api-key", model="gpt-4")

    # Define functions
    functions = [
        {
            "name": "get_weather",
            "description": "Get weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    ]

    messages = [
        ChatMessage(role=MessageRole.USER, content="What's the weather in Paris?")
    ]

    response = await provider.generate_with_functions(messages, functions)

    if response.has_function_calls():
        for func_call in response.get_function_calls():
            print(f"Function: {func_call.name}")
            print(f"Arguments: {func_call.arguments}")

asyncio.run(main())
```

### Streaming Responses

```python
import asyncio
from opsvi_llm import OpenAIProvider, ChatMessage, MessageRole

async def main():
    provider = OpenAIProvider(api_key="your-api-key", model="gpt-4")

    messages = [
        ChatMessage(role=MessageRole.USER, content="Write a short story about a robot.")
    ]

    async for chunk in provider.generate_stream(messages):
        print(chunk.generated_text, end="", flush=True)

asyncio.run(main())
```

### Rate Limiting and Retry

```python
import asyncio
from opsvi_llm import OpenAIProvider, GenerationConfig

async def main():
    provider = OpenAIProvider(api_key="your-api-key", model="gpt-4")

    # Configure generation parameters
    config = GenerationConfig(
        max_tokens=100,
        temperature=0.7,
        top_p=0.9
    )

    # Use retry logic
    response = await provider.generate_with_retry(
        "Explain machine learning",
        config=config
    )

    print(response.generated_text)

asyncio.run(main())
```

## Architecture

### Core Components

- **Schemas**: Pydantic V2 models for structured data validation
- **Providers**: Abstract base classes and concrete implementations for LLM services
- **Utilities**: Retry logic, rate limiting, and other common utilities

### Provider Interface

All providers implement the `BaseLLMProvider` interface:

```python
class BaseLLMProvider(ABC):
    async def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> LLMResponse
    async def generate_chat(self, messages: List[ChatMessage], config: Optional[GenerationConfig] = None) -> LLMResponse
    async def generate_with_functions(self, messages: List[ChatMessage], functions: List[Dict], config: Optional[GenerationConfig] = None) -> LLMResponse
```

### Response Schema

All responses use the `LLMResponse` schema:

```python
class LLMResponse(BaseModel):
    generated_text: str
    messages: Optional[List[ChatMessage]]
    function_calls: Optional[List[FunctionCall]]
    metadata: Optional[Dict[str, Any]]
    reasoning: Optional[str]
    usage: Optional[Dict[str, Any]]
    model: Optional[str]
    finish_reason: Optional[str]
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd opsvi-llm

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opsvi_llm

# Run specific test file
pytest tests/test_schemas.py

# Run async tests
pytest -m asyncio

# Run integration tests (requires API keys)
pytest -m integration
```

### Code Quality

```bash
# Format code
black opsvi_llm tests

# Lint code
ruff check opsvi_llm tests

# Type checking
mypy opsvi_llm

# Run all quality checks
pre-commit run --all-files
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
make html
```

## Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_ORGANIZATION=your-organization-id

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Rate Limiting

```python
from opsvi_llm.utils.rate_limiting import RateLimitConfig, add_global_rate_limiter

# Configure rate limiting for a service
config = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)
add_global_rate_limiter("my_service", config)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the OPSVI team.