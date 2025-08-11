"""OpenAI Responses API client for autonomous software factory."""

import asyncio
import json
import logging
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Generator,
    List,
    Optional,
    Union,
    TypeVar,
)
from uuid import uuid4

import jsonschema
from openai import OpenAI, AsyncOpenAI
from openai.types.responses import Response, ResponseStreamEvent
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIResponsesClient:
    """OpenAI Responses API client with modern patterns."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._validate_model_constraints = self._create_model_validator()

    def _create_model_validator(self):
        """Create model constraint validator."""
        APPROVED_MODELS = {"o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"}

        def validate_model(model_name: str) -> bool:
            """Validate model is approved - MANDATORY check."""
            if model_name not in APPROVED_MODELS:
                raise ValueError(f"UNAUTHORIZED MODEL: {model_name}")
            return True

        return validate_model

    def create_text(
        self,
        model: str,
        input_text: str,
        instructions: Optional[str] = None,
        temperature: float = 0.1,
        stream: bool = False,
    ) -> Union[Response, Generator[ResponseStreamEvent, None, None]]:
        """Create a plain text response.

        Args:
            model: Model to use (must be approved)
            input_text: Input text for the model
            instructions: Optional system instructions
            temperature: Sampling temperature (0-2)
            stream: Whether to stream the response

        Returns:
            Response object or streaming generator
        """
        self._validate_model_constraints(model)

        params = {
            "model": model,
            "input": input_text,
            "temperature": temperature,
        }

        if instructions:
            params["instructions"] = instructions
        if stream:
            params["stream"] = True

        return self.client.responses.create(**params)

    def create_structured(
        self,
        model: str,
        schema: type[T],
        input_text: str,
        instructions: Optional[str] = None,
        temperature: float = 0.1,
        strict: bool = True,
        parallel_tool_calls: bool = False,
    ) -> T:
        """Create a structured response using Pydantic schema.

        Args:
            model: Model to use (must be approved)
            schema: Pydantic model for structured output
            input_text: Input text for the model
            instructions: Optional system instructions
            temperature: Sampling temperature (0-2)
            strict: Whether to enforce strict schema validation
            parallel_tool_calls: Whether to allow parallel tool calls

        Returns:
            Parsed Pydantic model instance
        """
        self._validate_model_constraints(model)

        # Create JSON schema from Pydantic model
        json_schema = schema.model_json_schema()

        # For Responses API, we need to include the schema in the instructions
        # since it doesn't support response_format parameter
        schema_instruction = f"""
        Your response must be a valid JSON object that conforms to this schema:
        {json_schema}

        Ensure the response is properly formatted as JSON and follows the schema exactly.
        """

        params = {
            "model": model,
            "input": input_text,
            "parallel_tool_calls": parallel_tool_calls,
        }

        # Only add temperature for models that support it (not o4 models)
        if not model.startswith("o4"):
            params["temperature"] = temperature

        if instructions:
            params["instructions"] = instructions + "\n\n" + schema_instruction
        else:
            params["instructions"] = schema_instruction

        response = self.client.responses.create(**params)

        try:
            # Parse the response using Pydantic
            if hasattr(response, "output_parsed"):
                return response.output_parsed
            else:
                # Fallback to manual parsing
                output_text = response.output_text.strip()

                # Handle markdown-formatted JSON (```json ... ```)
                if output_text.startswith("```json"):
                    output_text = output_text[7:]  # Remove ```json
                if output_text.endswith("```"):
                    output_text = output_text[:-3]  # Remove ```

                return schema.model_validate_json(output_text.strip())
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse structured response: {e}")
            raise ValueError(f"Invalid structured response: {e}")

    def create_with_tools(
        self,
        model: str,
        tools: List[Dict[str, Any]],
        input_text: str,
        instructions: Optional[str] = None,
        temperature: float = 0.1,
        stream: bool = False,
        strict_functions: bool = True,
    ) -> Union[Response, Generator[ResponseStreamEvent, None, None]]:
        """Create a response with tool integration.

        Args:
            model: Model to use (must be approved)
            tools: List of tool definitions
            input_text: Input text for the model
            instructions: Optional system instructions
            temperature: Sampling temperature (0-2)
            stream: Whether to stream the response
            strict_functions: Whether to enforce strict function schemas

        Returns:
            Response object or streaming generator
        """
        self._validate_model_constraints(model)

        # Process tools to ensure strict function schemas
        processed_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                # Ensure the function has a name field at the top level
                if "function" in tool and "name" in tool["function"]:
                    tool["name"] = tool["function"]["name"]
                tool["function"]["strict"] = strict_functions
            processed_tools.append(tool)

        params = {
            "model": model,
            "input": input_text,
            "tools": processed_tools,
            "temperature": temperature,
        }

        if instructions:
            params["instructions"] = instructions
        if stream:
            params["stream"] = True

        return self.client.responses.create(**params)

    def create_with_reasoning(
        self,
        model: str,
        input_text: str,
        instructions: Optional[str] = None,
        effort: str = "medium",
        summary: str = "auto",
        include_encrypted: bool = False,
        store: bool = True,
        temperature: float = 0.1,
    ) -> Response:
        """Create a response with reasoning (for o-series models).

        Args:
            model: Model to use (must be approved)
            input_text: Input text for the model
            instructions: Optional system instructions
            effort: Reasoning effort level (low, medium, high)
            summary: Summary type (auto, manual, none)
            include_encrypted: Whether to include encrypted reasoning
            store: Whether to store reasoning items
            temperature: Sampling temperature (0-2)

        Returns:
            Response object with reasoning
        """
        self._validate_model_constraints(model)

        # Validate o-series model for reasoning
        if not model.startswith(("o3", "o4")):
            raise ValueError(f"Reasoning requires o-series model, got: {model}")

        params = {
            "model": model,
            "input": input_text,
            "reasoning": {
                "effort": effort,
                "summary": summary,
            },
        }

        if instructions:
            params["instructions"] = instructions
        if include_encrypted:
            params["include"] = ["reasoning.encrypted_content"]
        if not store:
            params["store"] = False

        return self.client.responses.create(**params)

    def stream_response(
        self,
        model: str,
        input_text: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
    ) -> Generator[ResponseStreamEvent, None, None]:
        """Stream a response with SSE-safe events.

        Args:
            model: Model to use (must be approved)
            input_text: Input text for the model
            instructions: Optional system instructions
            tools: Optional list of tools
            temperature: Sampling temperature (0-2)

        Yields:
            Streaming events
        """
        self._validate_model_constraints(model)

        params = {
            "model": model,
            "input": input_text,
            "stream": True,
            "temperature": temperature,
        }

        if instructions:
            params["instructions"] = instructions
        if tools:
            params["tools"] = tools

        stream = self.client.responses.create(**params)

        for event in stream:
            yield event

    async def stream_response_async(
        self,
        model: str,
        input_text: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[ResponseStreamEvent, None]:
        """Stream a response asynchronously.

        Args:
            model: Model to use (must be approved)
            input_text: Input text for the model
            instructions: Optional system instructions
            tools: Optional list of tools
            temperature: Sampling temperature (0-2)

        Yields:
            Streaming events
        """
        self._validate_model_constraints(model)

        params = {
            "model": model,
            "input": input_text,
            "stream": True,
            "temperature": temperature,
        }

        if instructions:
            params["instructions"] = instructions
        if tools:
            params["tools"] = tools

        stream = await self.async_client.responses.create(**params)

        async for event in stream:
            yield event

    def create_background_task(
        self,
        model: str,
        input_text: str,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.1,
    ) -> Response:
        """Create a background task for long-running operations.

        Args:
            model: Model to use (must be approved)
            input_text: Input text for the model
            instructions: Optional system instructions
            tools: Optional list of tools
            temperature: Sampling temperature (0-2)

        Returns:
            Response object with background task ID
        """
        self._validate_model_constraints(model)

        params = {
            "model": model,
            "input": input_text,
            "background": True,
            "temperature": temperature,
        }

        if instructions:
            params["instructions"] = instructions
        if tools:
            params["tools"] = tools

        return self.client.responses.create(**params)

    def parse_with_pydantic(
        self,
        response: Response,
        schema: type[T],
    ) -> T:
        """Parse response using Pydantic model.

        Args:
            response: OpenAI response object
            schema: Pydantic model for parsing

        Returns:
            Parsed Pydantic model instance
        """
        try:
            if hasattr(response, "output_parsed"):
                return response.output_parsed
            else:
                output_text = response.output_text.strip()

                # Handle markdown-formatted JSON (```json ... ```)
                if output_text.startswith("```json"):
                    output_text = output_text[7:]  # Remove ```json
                if output_text.endswith("```"):
                    output_text = output_text[:-3]  # Remove ```

                return schema.model_validate_json(output_text.strip())
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse response with Pydantic: {e}")
            raise ValueError(f"Invalid response format: {e}")

    def validate_json_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> bool:
        """Validate data against JSON schema.

        Args:
            data: Data to validate
            schema: JSON schema definition

        Returns:
            True if valid, raises ValidationError if invalid
        """
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.error(f"JSON schema validation failed: {e}")
            raise ValueError(f"Schema validation failed: {e}")

    def get_request_id(self, response: Response) -> Optional[str]:
        """Get request ID for debugging.

        Args:
            response: OpenAI response object

        Returns:
            Request ID string or None
        """
        return getattr(response, "_request_id", None)

    def handle_api_error(self, error: Exception) -> None:
        """Handle OpenAI API errors with proper logging.

        Args:
            error: Exception from OpenAI API
        """
        if hasattr(error, "status_code"):
            logger.error(f"OpenAI API error {error.status_code}: {error}")
        else:
            logger.error(f"OpenAI API error: {error}")

        # Re-raise with context
        raise error

    def call_json(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_output_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call OpenAI with structured JSON output using Responses API."""
        self._validate_model_constraints(model)

        # Try Responses API with JSON Schema first
        try:
            response = self.client.responses.create(
                model=model,
                input=messages,
                response_format={"type": "json_schema", "json_schema": schema},
                max_output_tokens=max_output_tokens,
            )
            return json.loads(response.output_text)
        except Exception as e:
            logger.warning(f"Responses API with JSON Schema failed: {e}")

            # Fallback to Function Calling
            try:
                if tools is None:
                    tools = [
                        {
                            "type": "function",
                            "function": {"name": "output", "parameters": schema},
                        }
                    ]

                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": "output"}},
                    max_tokens=max_output_tokens,
                )

                # Extract function call arguments
                tool_call = response.choices[0].message.tool_calls[0]
                return json.loads(tool_call.function.arguments)
            except Exception as e2:
                logger.warning(f"Function calling failed: {e2}")

                # Final fallback to JSON mode
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages
                        + [
                            {"role": "user", "content": "Respond with valid JSON only."}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=max_output_tokens,
                    )
                    return json.loads(response.choices[0].message.content)
                except Exception as e3:
                    logger.error(f"All JSON output methods failed: {e3}")
                    raise

    def call_text(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_output_tokens: Optional[int] = None,
    ) -> str:
        """Call OpenAI for text output."""
        self._validate_model_constraints(model)

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_output_tokens,
        )
        return response.choices[0].message.content


# Convenience functions for common patterns
def create_text_response(model: str, input_text: str, **kwargs) -> Response:
    """Create a simple text response."""
    client = OpenAIResponsesClient()
    return client.create_text(model, input_text, **kwargs)


def create_structured_response(
    model: str, schema: type[T], input_text: str, **kwargs
) -> T:
    """Create a structured response."""
    client = OpenAIResponsesClient()
    return client.create_structured(model, schema, input_text, **kwargs)


def create_tool_response(
    model: str, tools: List[Dict[str, Any]], input_text: str, **kwargs
) -> Response:
    """Create a response with tools."""
    client = OpenAIResponsesClient()
    return client.create_with_tools(model, tools, input_text, **kwargs)


def stream_text_response(
    model: str, input_text: str, **kwargs
) -> Generator[ResponseStreamEvent, None, None]:
    """Stream a text response."""
    client = OpenAIResponsesClient()
    return client.stream_response(model, input_text, **kwargs)
