"""OpenAI provider for LLM services.

Comprehensive OpenAI integration for the OPSVI ecosystem
Enforces 2025 OpenAI API standards with strict model validation
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
from .openai_model_validator import OpenAIModelValidator, ModelType
from .openai_security import DataSanitizer, AuditLogger, SecurityEnforcer

logger = logging.getLogger(__name__)


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
        self.audit_logger = AuditLogger(config.audit_log_dir) if config.enable_audit_logging else None
        self.security_enforcer = SecurityEnforcer(self.sanitizer, self.audit_logger) if self.audit_logger else None
        
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
    
    def select_model_for_task(self, task_type: str, complexity: str = "standard") -> str:
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
        selected_model = OpenAIModelValidator.select_model_for_task(model_type, complexity)
        
        logger.info(f"Selected model '{selected_model}' for task type '{task_type}' with complexity '{complexity}'")
        return selected_model

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
                    temperature=request.temperature
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
                    request_id=request_id,
                    success=True,
                    response_data=response
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
                    request_id=request_id,
                    success=False,
                    error=str(e)
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
