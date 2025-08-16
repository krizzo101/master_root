# Knowledge Update: OpenAI API (Generated 2025-08-05)

## Current State (Last 12+ Months)

OpenAI API has undergone significant evolution in 2025 with major architectural improvements:

- **GPT-4.1 Series**: New model family with 1M token context, improved coding and instruction following
- **Responses API**: Preferred API for structured responses and agentic applications
- **O3 and O4 Series**: Advanced reasoning models with tool integration
- **Enhanced Tool Integration**: Remote MCP servers, image generation, Code Interpreter
- **Background Mode**: Asynchronous processing for long-running tasks
- **Reasoning Summaries**: Natural language summaries of model reasoning
- **Structured Outputs**: Guaranteed JSON schema compliance with Pydantic integration
- **Real-time Streaming**: Enhanced streaming capabilities with event handlers
- **Production-Ready SDK**: Version 1.98.0 with comprehensive type safety

## Best Practices & Patterns

### Model Selection Strategy (2025)

#### Approved Models Only (MANDATORY)
```python
APPROVED_MODELS = {
    "o4-mini": "Advanced reasoning and planning",
    "o3": "Complex reasoning and tool integration",
    "gpt-4.1-mini": "Fast agent execution and responses",
    "gpt-4.1": "Structured outputs and complex tasks",
    "gpt-4.1-nano": "Ultra-fast responses and simple tasks"
}

FORBIDDEN_MODELS = {
    "gpt-4o", "gpt-4o-mini", "gpt-4o-2024-08-06",  # GPT-4O series
    "claude-3", "claude-3.5", "claude-3.5-sonnet",  # Anthropic models
    "gemini", "gemini-pro", "gemini-flash",  # Google models
    "llama", "llama-3", "llama-3.1",  # Meta models
    "mistral", "mixtral", "codellama"  # Other models
}
```

#### Task-Based Model Selection
```python
def select_model_for_task(task_type: str) -> str:
    """Select appropriate model based on task requirements."""
    model_mapping = {
        "reasoning": "o4-mini",  # MANDATORY for reasoning
        "planning": "o4-mini",   # MANDATORY for planning
        "agent_execution": "gpt-4.1-mini",  # MANDATORY for agents
        "structured_outputs": "gpt-4.1",    # Required for JSON schema
        "complex_reasoning": "gpt-4.1",
        "fast_responses": "gpt-4.1-nano",
        "tool_integration": "o3"
    }
    return model_mapping.get(task_type, "gpt-4.1-mini")
```

### Responses API Implementation (PREFERRED)

#### Basic Responses API Usage
```python
import os
from openai import OpenAI
from typing import Dict, Any, Optional

class OpenAIResponsesClient:
    """Updated client using Responses API with approved models only"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url
        )

    def create_response(
        self,
        input_data: str,
        model: Optional[str] = None,
        task_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured response using Responses API."""

        # Validate model
        selected_model = model or self._select_model_for_task(task_type)
        validate_model_constraints(selected_model)

        # Sanitize input
        sanitized_input = DataSanitizer.sanitize_input(input_data)

        try:
            response = self.client.responses.create(
                model=selected_model,
                input=sanitized_input,
                **kwargs
            )

            return {
                "success": True,
                "output": response.output_text,
                "usage": response.usage,
                "id": response.id
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": selected_model
            }

    def _select_model_for_task(self, task_type: str) -> str:
        """Get model-specific instructions for task type."""
        base_instructions = "You are a helpful AI assistant."

        if task_type in ["reasoning", "planning"]:
            return f"{base_instructions} Provide clear, logical reasoning."
        elif task_type == "agent_execution":
            return f"{base_instructions} Execute tasks efficiently and accurately."
        elif task_type == "structured_outputs":
            return f"{base_instructions} Provide structured, well-formatted responses."
        else:
            return base_instructions
```

#### Streaming Responses with Real-time Validation
```python
def stream_structured_response(
    self,
    input_data: str,
    model: Optional[str] = None,
    task_type: str = "general",
    **kwargs
):
    """Stream structured response with real-time validation."""

    selected_model = model or self._select_model_for_task(task_type)
    validate_model_constraints(selected_model)
    sanitized_input = DataSanitizer.sanitize_input(input_data)

    return self.client.responses.stream(
        model=selected_model,
        input=sanitized_input,
        stream=True,
        **kwargs
    )
```

### Structured Outputs with Pydantic (2025)

#### Advanced Structured Outputs Implementation
```python
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

class Step(BaseModel):
    explanation: str = Field(description="Detailed explanation of the step")
    output: str = Field(description="Mathematical output or result")

class MathResponse(BaseModel):
    steps: List[Step] = Field(description="Step-by-step solution")
    final_answer: str = Field(description="Final answer to the problem")

class ArticleSummary(BaseModel):
    invented_year: int = Field(description="Year of invention")
    summary: str = Field(description="One sentence summary")
    inventors: List[str] = Field(description="List of inventors")
    description: str = Field(description="Detailed description")

    class Concept(BaseModel):
        title: str = Field(description="Concept title")
        description: str = Field(description="Concept description")

    concepts: List[Concept] = Field(description="Key concepts")

def create_structured_response_with_pydantic(
    input_text: str,
    response_model: BaseModel,
    model: str = "gpt-4.1",
    task_type: str = "structured_outputs"
) -> BaseModel:
    """Create structured response using Pydantic models."""

    validate_model_constraints(model)

    client = OpenAI()
    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides structured responses."},
            {"role": "user", "content": input_text}
        ],
        response_format=response_model,
    )

    message = completion.choices[0].message
    if message.parsed:
        return message.parsed
    else:
        raise ValueError(f"Failed to parse response: {message.refusal}")
```

### Advanced Tool Integration (2025)

#### MCP Server Integration
```python
from openai import OpenAI
from openai.types.responses import ResponseMcpCallCompletedEvent

def create_mcp_tool_call(
    input_text: str,
    mcp_server_url: str,
    model: str = "o3"
) -> Dict[str, Any]:
    """Create MCP tool call for external service integration."""

    validate_model_constraints(model)

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=input_text,
        tools=[{
            "type": "mcp",
            "mcp": {
                "server_url": mcp_server_url,
                "tools": ["web_search", "file_search", "code_interpreter"]
            }
        }]
    )

    return {
        "response_id": response.id,
        "status": response.status,
        "output": response.output_text
    }
```

#### Background Task Processing
```python
def create_background_task(task_description: str, model: str = "o3"):
    """Create background task for long-running operations"""

    validate_model_constraints(model)

    response = client.responses.create(
        model=model,
        input=task_description,
        background=True  # Enable background mode
    )

    return {
        "task_id": response.id,
        "status": response.status,
        "estimated_completion": response.estimated_completion
    }

def poll_background_task(task_id: str):
    """Poll background task for completion"""

    response = client.responses.retrieve(task_id)

    if response.status == "completed":
        return {
            "success": True,
            "output": response.output_text,
            "usage": response.usage
        }
    elif response.status == "failed":
        return {
            "success": False,
            "error": response.error
        }
    else:
        return {
            "success": False,
            "status": response.status,
            "estimated_completion": response.estimated_completion
        }
```

### Reasoning and Planning (2025)

#### Advanced Reasoning with Summaries
```python
def create_reasoning_summary(task_description: str, model: str = "o4-mini"):
    """Create response with reasoning summary"""

    validate_model_constraints(model)

    response = client.responses.create(
        model=model,
        input=task_description,
        reasoning=True,  # Enable reasoning mode
        tools=[{"type": "code_interpreter"}]
    )

    return {
        "output": response.output_parsed,
        "reasoning_summary": response.reasoning_summary,
        "confidence": response.confidence_score
    }
```

## Tools & Frameworks

### Core SDK Components (v1.98.0)

#### Installation and Setup
```python
# Latest version installation
pip install openai==1.98.0

# With optional dependencies
pip install "openai[aiohttp]"  # For improved async performance
pip install "openai[realtime]"  # For real-time API features
```

#### Client Configuration
```python
from openai import OpenAI, AsyncOpenAI
import os

# Synchronous client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1",
    timeout=60.0,
    max_retries=2
)

# Asynchronous client with aiohttp
from openai import DefaultAioHttpClient

async_client = AsyncOpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    http_client=DefaultAioHttpClient(),
    timeout=60.0
)
```

### Advanced Streaming Patterns

#### Event-Driven Streaming
```python
from openai import AssistantEventHandler
from openai.types.beta.threads import Text, TextDelta
from openai.types.beta.threads.runs import ToolCall, ToolCallDelta

class CustomEventHandler(AssistantEventHandler):
    def on_text_created(self, text: Text) -> None:
        print(f"\nAssistant: ", end="", flush=True)

    def on_text_delta(self, delta: TextDelta, snapshot: Text):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call: ToolCall):
        print(f"\n[Tool Call: {tool_call.type}]", flush=True)

    def on_tool_call_delta(self, delta: ToolCallDelta, snapshot: ToolCall):
        if delta.type == "code_interpreter" and delta.code_interpreter:
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)

# Usage
with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=assistant.id,
    event_handler=CustomEventHandler(),
) as stream:
    stream.until_done()
```

#### Real-time API Integration
```python
import asyncio
from openai import AsyncOpenAI

async def realtime_conversation():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(
        model="gpt-4o-realtime-preview"
    ) as connection:
        await connection.session.update(session={'modalities': ['text']})

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello!"}],
            }
        )
        await connection.response.create()

        async for event in connection:
            if event.type == 'response.text.delta':
                print(event.delta, flush=True, end="")
            elif event.type == 'response.text.done':
                print()
            elif event.type == "response.done":
                break

asyncio.run(realtime_conversation())
```

## Implementation Guidance

### Security and Validation

#### Model Validation Function
```python
def validate_model_constraints(model: str) -> None:
    """Validate model against approved list (MANDATORY)."""
    if model in FORBIDDEN_MODELS:
        raise ValueError(f"Model {model} is FORBIDDEN. Use approved models only.")

    if model not in APPROVED_MODELS:
        raise ValueError(f"Model {model} not in approved list. Use: {list(APPROVED_MODELS.keys())}")
```

#### Input Sanitization
```python
import re
from typing import Any

class DataSanitizer:
    """Sanitize input data for security."""

    @staticmethod
    def sanitize_input(input_data: Any) -> str:
        """Sanitize input to prevent injection attacks."""
        if isinstance(input_data, str):
            # Remove potentially dangerous patterns
            sanitized = re.sub(r'<script.*?</script>', '', input_data, flags=re.IGNORECASE)
            sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r'data:text/html', '', sanitized, flags=re.IGNORECASE)
            return sanitized.strip()
        return str(input_data)

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format."""
        return bool(api_key and api_key.startswith('sk-') and len(api_key) > 20)
```

### Error Handling and Retry Logic

#### Comprehensive Error Handling
```python
import openai
from typing import Dict, Any, Optional

class OpenAIErrorHandler:
    """Handle OpenAI API errors with retry logic."""

    @staticmethod
    def handle_api_error(error: Exception) -> Dict[str, Any]:
        """Handle different types of OpenAI API errors."""

        if isinstance(error, openai.APIConnectionError):
            return {
                "error_type": "connection_error",
                "message": "Network connection failed",
                "retryable": True,
                "retry_delay": 5
            }
        elif isinstance(error, openai.RateLimitError):
            return {
                "error_type": "rate_limit",
                "message": "Rate limit exceeded",
                "retryable": True,
                "retry_delay": 60
            }
        elif isinstance(error, openai.APIStatusError):
            return {
                "error_type": "api_error",
                "message": f"API error: {error.status_code}",
                "retryable": error.status_code >= 500,
                "retry_delay": 10
            }
        else:
            return {
                "error_type": "unknown_error",
                "message": str(error),
                "retryable": False,
                "retry_delay": 0
            }

    @staticmethod
    async def retry_with_backoff(
        func,
        max_retries: int = 3,
        base_delay: float = 1.0
    ):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                error_info = OpenAIErrorHandler.handle_api_error(e)

                if not error_info["retryable"] or attempt == max_retries - 1:
                    raise e

                delay = base_delay * (2 ** attempt) + error_info["retry_delay"]
                await asyncio.sleep(delay)
```

### Production Deployment

#### Environment Configuration
```python
# .env file
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3
OPENAI_LOG=info  # Enable logging

# Production configuration
PRODUCTION_CONFIG = {
    "timeout": 60.0,
    "max_retries": 3,
    "request_id_header": True,
    "log_level": "info"
}
```

#### Monitoring and Observability
```python
import logging
from typing import Dict, Any

class OpenAIMonitor:
    """Monitor OpenAI API usage and performance."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "total_tokens": 0,
            "response_times": []
        }

    def log_request(self, model: str, input_tokens: int, output_tokens: int, response_time: float):
        """Log API request metrics."""
        self.metrics["requests"] += 1
        self.metrics["total_tokens"] += input_tokens + output_tokens
        self.metrics["response_times"].append(response_time)

        self.logger.info(
            f"OpenAI API Request - Model: {model}, "
            f"Tokens: {input_tokens}+{output_tokens}, "
            f"Time: {response_time:.2f}s"
        )

    def log_error(self, error: Exception, model: str):
        """Log API errors."""
        self.metrics["errors"] += 1
        self.logger.error(f"OpenAI API Error - Model: {model}, Error: {str(error)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        avg_response_time = (
            sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            if self.metrics["response_times"] else 0
        )

        return {
            **self.metrics,
            "avg_response_time": avg_response_time,
            "error_rate": self.metrics["errors"] / max(self.metrics["requests"], 1)
        }
```

## Limitations & Considerations

### Current Limitations (2025)

1. **Model Availability**: Only approved models can be used (enforced by 953-openai-api-standards)
2. **Rate Limits**: Different models have different rate limits
3. **Context Length**: GPT-4.1 has 1M token context, others vary
4. **Tool Integration**: Some tools require specific model capabilities
5. **Background Processing**: Limited to certain model types
6. **Real-time Features**: Only available with specific models

### Performance Considerations

1. **Model Selection**: Choose appropriate model for task complexity
2. **Token Optimization**: Minimize input tokens for cost efficiency
3. **Caching**: Implement response caching for repeated queries
4. **Streaming**: Use streaming for long responses to improve UX
5. **Batch Processing**: Use background mode for long-running tasks

### Security Best Practices

1. **API Key Management**: Use environment variables, never hardcode
2. **Input Validation**: Always sanitize user inputs
3. **Model Validation**: Enforce approved model usage
4. **Error Handling**: Don't expose sensitive information in errors
5. **Rate Limiting**: Implement client-side rate limiting
6. **Monitoring**: Log all API interactions for audit trails

## Recent Updates (2024-2025)

### SDK Version 1.98.0 Features

1. **Enhanced Structured Outputs**: Improved Pydantic integration
2. **Background Processing**: Support for long-running tasks
3. **Real-time API**: WebSocket-based real-time communication
4. **Advanced Streaming**: Event-driven streaming with custom handlers
5. **MCP Integration**: Model Context Protocol server support
6. **Reasoning Summaries**: Natural language reasoning explanations
7. **Enhanced Error Handling**: Better error classification and retry logic
8. **Performance Improvements**: Faster response times and better caching

### API Enhancements

1. **Responses API**: New preferred API for structured responses
2. **Tool Integration**: Enhanced tool calling with MCP servers
3. **Background Mode**: Asynchronous processing capabilities
4. **Reasoning Mode**: Explicit reasoning with summaries
5. **Enhanced Streaming**: Real-time event streaming
6. **Better Type Safety**: Comprehensive type definitions

### Breaking Changes

1. **Model Restrictions**: Enforced approved model usage
2. **API Versioning**: Responses API becomes preferred over Chat Completions
3. **Tool Schema**: Stricter tool schema validation
4. **Error Handling**: New error types and handling patterns
5. **Streaming**: Updated streaming event structure

## Best Practices Summary

### Development Workflow

1. **Model Selection**: Always use approved models for specific tasks
2. **API Choice**: Prefer Responses API over Chat Completions
3. **Structured Outputs**: Use Pydantic models for type safety
4. **Error Handling**: Implement comprehensive error handling
5. **Monitoring**: Add logging and metrics for production
6. **Security**: Validate inputs and protect API keys
7. **Performance**: Optimize for token usage and response times

### Production Checklist

- [ ] Approved models only used
- [ ] Responses API implemented
- [ ] Structured outputs with Pydantic
- [ ] Comprehensive error handling
- [ ] Input sanitization implemented
- [ ] API key security measures
- [ ] Monitoring and logging configured
- [ ] Rate limiting implemented
- [ ] Retry logic with backoff
- [ ] Performance optimization applied