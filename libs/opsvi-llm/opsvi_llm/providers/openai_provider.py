"""OpenAI provider for LLM services.

Comprehensive OpenAI integration for the OPSVI ecosystem
Enforces 2025 OpenAI API standards with strict model validation
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from openai import AsyncOpenAI
from openai.types.responses import Response as OpenAIResponse
from pydantic import BaseModel, Field

from .base import (
    BaseLLMProvider,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    LLMConfig,
    LLMProviderError,
    Message,
)
from .openai_model_validator import ModelType, OpenAIModelValidator
from .openai_security import AuditLogger, DataSanitizer, SecurityEnforcer

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIConfig(LLMConfig):
    """Configuration for OpenAI provider."""

    # OpenAI-specific configuration
    organization: Optional[str] = Field(
        default=None, description="OpenAI organization ID"
    )

    # Model defaults - Using approved 2025 models only
    default_model: str = Field(
        default="gpt-5-mini", description="Default OpenAI model (2025 approved)"
    )
    default_embedding_model: str = Field(
        default="text-embedding-3-large", description="Default embedding model"
    )

    # Security configuration
    enable_audit_logging: bool = Field(
        default=True, description="Enable comprehensive audit logging"
    )
    enable_sanitization: bool = Field(
        default=True, description="Enable PII/secret sanitization"
    )
    audit_log_dir: Optional[str] = Field(
        default=None, description="Directory for audit logs"
    )

    class Config:
        env_prefix = "OPSVI_LLM_OPENAI_"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation with 2025 standards compliance."""

    def __init__(self, config: OpenAIConfig, **kwargs: Any) -> None:
        """Initialize OpenAI provider with 2025 compliance.

        Args:
            config: OpenAI configuration
            **kwargs: Additional configuration parameters
        """
        super().__init__(config, **kwargs)
        self.openai_config = config
        self._async_client: Optional[AsyncOpenAI] = None

        # Initialize security components
        self.sanitizer = DataSanitizer()
        self.audit_logger = (
            AuditLogger(config.audit_log_dir) if config.enable_audit_logging else None
        )
        self.security_enforcer = (
            SecurityEnforcer(self.sanitizer, self.audit_logger)
            if self.audit_logger
            else None
        )

        # Validate default models
        try:
            OpenAIModelValidator.validate_model(config.default_model)
            logger.info(f"✅ Default model '{config.default_model}' validated")
        except ValueError as e:
            logger.error(f"Invalid default model: {e}")
            # Fall back to approved model
            config.default_model = "gpt-5-mini"
            logger.warning(f"Using fallback approved model: {config.default_model}")

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

    def select_model_for_task(
        self, task_type: str, complexity: str = "standard"
    ) -> str:
        """
        Dynamically select optimal model based on task type.

        Args:
            task_type: Type of task (reasoning, execution, fast_response, structured_output)
            complexity: Task complexity (simple, standard, complex)

        Returns:
            Approved model name for the task
        """
        # Map string task types to ModelType enum
        task_map = {
            "reasoning": ModelType.REASONING,
            "execution": ModelType.EXECUTION,
            "fast_response": ModelType.FAST_RESPONSE,
            "structured_output": ModelType.STRUCTURED_OUTPUT,
        }

        model_type = task_map.get(task_type, ModelType.EXECUTION)
        selected_model = OpenAIModelValidator.select_model_for_task(
            model_type, complexity
        )

        logger.info(
            f"Selected model '{selected_model}' for task '{task_type}' "
            f"with complexity '{complexity}'"
        )
        return selected_model

    def _convert_messages_to_input(
        self, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """Convert Message objects to Responses API input format.

        Args:
            messages: List of Message objects

        Returns:
            List of message dictionaries for Responses API
        """
        input_messages = []
        for msg in messages:
            # Map role names if needed
            role = msg.role
            if role == "system":
                # In Responses API, system messages become developer messages
                role = "developer"

            message_dict = {
                "role": role,
                "content": msg.content,
            }

            if msg.name:
                message_dict["name"] = msg.name

            input_messages.append(message_dict)

        return input_messages

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
        """Generate chat completion using OpenAI with 2025 compliance."""
        try:
            model = request.model or self.openai_config.default_model

            # Validate model compliance
            OpenAIModelValidator.validate_model(model)

            # Sanitize messages if security is enabled
            openai_messages = []
            for msg in request.messages:
                content = msg.content
                if self.openai_config.enable_sanitization:
                    content = self.sanitizer.sanitize_input(content)

                openai_msg = {
                    "role": msg.role,
                    "content": content,
                }
                if msg.name:
                    openai_msg["name"] = msg.name
                openai_messages.append(openai_msg)

            # Log request if audit logging is enabled
            request_id = None
            if self.audit_logger:
                request_id = self.audit_logger.log_request(
                    model=model,
                    input_data=request.messages,
                    sanitized_input=openai_messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

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
                name=getattr(choice.message, "name", None),
            )

            # Log successful response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id, success=True, response_data=response
                )

            return ChatResponse(
                message=message,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            # Log failed response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id, success=False, error=str(e)
                )
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

    async def create_structured_response(
        self,
        messages: List[Message],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> T:
        """Create a structured response using OpenAI Chat Completions API.

        NOTE: For new implementations, prefer responses_create_with_structured_output().
        This method is maintained for backward compatibility.

        Args:
            messages: List of chat messages
            response_model: Pydantic model class for response structure
            model: Model to use (defaults to gpt-5-mini, uses o4-mini for reasoning)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API

        Returns:
            Parsed instance of response_model
        """
        if not self._async_client:
            self._async_client = await self._create_client()

        # Determine model based on task type
        if model is None:
            # Check if this is a reasoning task
            is_reasoning = any(
                keyword in str(messages).lower()
                for keyword in [
                    "reason",
                    "analyze",
                    "explain",
                    "think",
                    "plan",
                    "design",
                ]
            )
            model = "o4-mini" if is_reasoning else self.openai_config.default_model

        # Validate model
        try:
            OpenAIModelValidator.validate_model(model)
        except ValueError:
            model = self.openai_config.default_model

        # Log the operation
        if self.audit_logger:
            self.audit_logger.log_request(
                provider="openai",
                model=model,
                operation="create_structured_response",
                request_data={
                    "messages": [msg.model_dump() for msg in messages],
                    "response_model": response_model.__name__,
                    "temperature": temperature,
                },
            )

        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            # Create the structured response using Responses API
            response = await self._async_client.beta.chat.completions.parse(
                model=model,
                messages=openai_messages,
                response_format=response_model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Log successful response
            if self.audit_logger:
                self.audit_logger.log_response(
                    provider="openai",
                    model=model,
                    operation="create_structured_response",
                    response_data={"status": "success"},
                )

            # Return the parsed response
            return response.choices[0].message.parsed

        except Exception as e:
            logger.error(f"Error creating structured response: {e}")
            if self.audit_logger:
                self.audit_logger.log_error(
                    provider="openai",
                    model=model,
                    operation="create_structured_response",
                    error=str(e),
                )
            raise LLMProviderError(f"Failed to create structured response: {e}") from e

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
    ) -> OpenAIResponse:
        """Create a response using the OpenAI Responses API (2025 standard).

        This is the PREFERRED method for new implementations.

        Args:
            input: Text or message list input for the model
            model: Model to use (auto-selected based on task if None)
            instructions: System instructions for the model
            reasoning_effort: For reasoning models (o3, o4-mini) - "low", "medium", "high"
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: Tools available to the model
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            OpenAI Response object
        """
        if not self._async_client:
            self._async_client = await self._create_client()

        # Auto-select model if not provided
        if model is None:
            # Check if this is a reasoning task
            is_reasoning = any(
                keyword in str(input).lower()
                for keyword in [
                    "reason",
                    "analyze",
                    "explain",
                    "think",
                    "plan",
                    "design",
                    "evaluate",
                    "solve",
                ]
            )

            if is_reasoning:
                model = "o4-mini"
                # Set reasoning effort if not provided
                if reasoning_effort is None:
                    reasoning_effort = "medium"
            else:
                model = self.openai_config.default_model

        # Validate model
        OpenAIModelValidator.validate_model(model)

        # Prepare parameters
        create_params = {
            "model": model,
            "input": input,
        }

        # Add temperature only for non-reasoning models
        # GPT-5 series and O-series models don't support temperature
        reasoning_models = [
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "o3",
            "o4-mini",
            "o1",
            "o1-mini",
        ]
        if (
            not any(model.startswith(rm) for rm in reasoning_models)
            and temperature is not None
        ):
            create_params["temperature"] = temperature

        # Add optional parameters
        if instructions:
            create_params["instructions"] = instructions
        if max_tokens:
            # Responses API uses max_output_tokens instead of max_tokens
            create_params["max_output_tokens"] = max_tokens
        if tools:
            create_params["tools"] = tools
        if stream:
            create_params["stream"] = stream

        # Add reasoning-specific parameters
        if model in ["o3", "o4-mini"] and reasoning_effort:
            create_params["reasoning_effort"] = reasoning_effort

        # Add any additional kwargs
        create_params.update(kwargs)

        # Sanitize input if enabled
        if self.openai_config.enable_sanitization and isinstance(input, str):
            create_params["input"] = self.sanitizer.sanitize_input(input)

        # Log request if audit logging is enabled
        request_id = None
        if self.audit_logger:
            request_id = self.audit_logger.log_request(
                model=model,
                operation="responses.create",
                input_data=create_params,
                provider="openai",
            )

        try:
            # Create response using Responses API
            response = await self._async_client.responses.create(**create_params)

            # Log successful response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id,
                    success=True,
                    response_data={"status": "success", "id": response.id},
                )

            return response

        except Exception as e:
            # Log failed response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id, success=False, error=str(e)
                )
            logger.error(f"OpenAI Responses API call failed: {e}")
            raise LLMProviderError(f"Responses API call failed: {e}") from e

    async def responses_create_with_structured_output(
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
        """Create a structured response using the OpenAI Responses API.

        This method uses the Responses API with structured output format.

        Args:
            input: Text or message list input for the model
            response_model: Pydantic model class for response structure
            model: Model to use (auto-selected based on task if None)
            instructions: System instructions for the model
            reasoning_effort: For reasoning models - "low", "medium", "high"
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API

        Returns:
            Parsed instance of response_model
        """
        if not self._async_client:
            self._async_client = await self._create_client()

        # Auto-select model if not provided
        if model is None:
            # Check if this is a reasoning task
            is_reasoning = any(
                keyword in str(input).lower()
                for keyword in [
                    "reason",
                    "analyze",
                    "explain",
                    "think",
                    "plan",
                    "design",
                    "evaluate",
                    "solve",
                ]
            )

            if is_reasoning:
                model = "o4-mini"
                if reasoning_effort is None:
                    reasoning_effort = "medium"
            else:
                # For structured outputs, prefer gpt-5 over gpt-5-mini
                model = "gpt-5"

        # Validate model
        OpenAIModelValidator.validate_model(model)

        # Prepare text format for structured output (Responses API format)
        text_format = {
            "type": "json_schema",
            "name": response_model.__name__,
            "strict": True,
            "schema": response_model.model_json_schema(),
        }

        # Prepare parameters
        create_params = {
            "model": model,
            "input": input,
            "text": {"format": text_format},  # Correct parameter for Responses API
        }

        # Add temperature only if not using gpt-5-nano (which doesn't support it)
        if model != "gpt-5-nano" and temperature is not None:
            create_params["temperature"] = temperature

        # Add optional parameters
        if instructions:
            create_params["instructions"] = instructions
        if max_tokens:
            # Responses API uses max_output_tokens instead of max_tokens
            create_params["max_output_tokens"] = max_tokens

        # Add reasoning-specific parameters
        if model in ["o3", "o4-mini"] and reasoning_effort:
            create_params["reasoning_effort"] = reasoning_effort

        # Add any additional kwargs
        create_params.update(kwargs)

        # Sanitize input if enabled
        if self.openai_config.enable_sanitization and isinstance(input, str):
            create_params["input"] = self.sanitizer.sanitize_input(input)

        # Log request if audit logging is enabled
        request_id = None
        if self.audit_logger:
            sanitized = create_params.get("input", input)
            request_id = self.audit_logger.log_request(
                model=model,
                operation="responses.create_structured",
                input_data=create_params,
                sanitized_input=sanitized,
                provider="openai",
            )

        try:
            # Create response using Responses API
            response = await self._async_client.responses.create(**create_params)

            # Parse the structured output from Responses API format
            # The response structure includes output array with content
            import json

            if hasattr(response, "output_text") and response.output_text:
                # Direct output_text field
                json_str = response.output_text
            elif hasattr(response, "output") and response.output:
                # Extract from output array structure
                content = None
                for output_item in response.output:
                    if hasattr(output_item, "content") and output_item.content:
                        for content_item in output_item.content:
                            if hasattr(content_item, "text"):
                                content = content_item.text
                                break
                        if content:
                            break

                if content:
                    json_str = content
                else:
                    raise ValueError("No text content found in response output")
            else:
                raise ValueError("Response does not contain expected output structure")

            # Parse JSON and validate with Pydantic model
            try:
                parsed_data = json.loads(json_str)
                parsed_output = response_model.model_validate(parsed_data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse structured response: {e}")
                logger.error(f"Response content: {json_str}")
                raise LLMProviderError(
                    f"Failed to parse structured response: {e}"
                ) from e

            # Log successful response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id,
                    success=True,
                    response_data={
                        "status": "success",
                        "type": response_model.__name__,
                    },
                )

            return parsed_output

        except Exception as e:
            # Log failed response
            if self.audit_logger and request_id:
                self.audit_logger.log_response(
                    request_id=request_id, success=False, error=str(e)
                )
            logger.error(f"OpenAI Responses API structured call failed: {e}")
            raise LLMProviderError(f"Responses API structured call failed: {e}") from e

    async def responses_create_from_messages(
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
    ) -> OpenAIResponse:
        """Create a response using the Responses API with Message objects.

        This is a convenience method that converts Message objects to the
        Responses API input format.

        Args:
            messages: List of Message objects
            model: Model to use (auto-selected based on task if None)
            instructions: System instructions for the model
            reasoning_effort: For reasoning models - "low", "medium", "high"
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: Tools available to the model
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            OpenAI Response object
        """
        # Convert messages to Responses API input format
        input_messages = self._convert_messages_to_input(messages)

        # Extract instructions from system/developer messages if not provided
        if not instructions:
            for msg in messages:
                if msg.role in ["system", "developer"]:
                    instructions = msg.content
                    # Remove the system message from input
                    input_messages = [
                        m
                        for m in input_messages
                        if not (
                            m["role"] == "developer" and m["content"] == instructions
                        )
                    ]
                    break

        # Call the main responses_create method
        return await self.responses_create(
            input=input_messages,
            model=model,
            instructions=instructions,
            reasoning_effort=reasoning_effort,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=stream,
            **kwargs,
        )
