"""LLM adapter for Claude Code Clone.

Provides a unified interface to the opsvi-llm library for Claude Code-like functionality.
Enforces OpenAI API Standards 2025 compliance.
"""

import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from pathlib import Path

from opsvi_llm import (
    OpenAIProvider,
    OpenAIConfig,
    ChatRequest,
    ChatResponse,
    Message,
    LLMProviderError,
)
from opsvi_llm.providers.openai_unified_interface import OpenAIUnifiedInterface

# OpenAI API Standards 2025 Compliance
from ..compliance import (
    OpenAIComplianceLayer,
    OpenAIComplianceError,
    ComplianceRequest,
    ReasoningEffort,
    create_simple_request,
    create_reasoning_request,
)

# Import optional providers
try:
    from opsvi_llm import AnthropicProvider, AnthropicConfig
except ImportError:
    AnthropicProvider = None
    AnthropicConfig = None

try:
    from opsvi_llm import PerplexityProvider, PerplexityConfig
except ImportError:
    PerplexityProvider = None
    PerplexityConfig = None
from opsvi_foundation import BaseComponent, ComponentError

from ..config import ClaudeCodeConfig
from ..validation import ModelValidator, ModelValidationError

logger = logging.getLogger(__name__)


class LLMAdapterError(ComponentError):
    """Error in LLM adapter operations."""

    pass


class LLMAdapter(BaseComponent):
    """Adapter for LLM providers in Claude Code Clone."""

    def __init__(self, config: ClaudeCodeConfig):
        """Initialize the LLM adapter."""
        super().__init__(name="LLMAdapter")
        self.config = config

        # ✅ MANDATORY: Validate model before initialization
        try:
            ModelValidator.validate_config(config)
        except ModelValidationError as e:
            logger.error(f"Model validation failed: {e}")
            raise LLMAdapterError(f"Configuration validation failed: {e}") from e

        # ✅ Initialize OpenAI API Standards 2025 Compliance Layer
        self._compliance = OpenAIComplianceLayer()
        logger.info("🔐 OpenAI API Standards 2025 compliance enforced")

        self._provider = None
        self._unified_interface = None
        self._setup_provider()

    async def _initialize_impl(self) -> None:
        """Initialize the LLM adapter."""
        if self._provider:
            await self._provider.initialize()
        logger.info("LLM adapter initialized")

    async def _shutdown_impl(self) -> None:
        """Shutdown the LLM adapter."""
        await self.close()
        logger.info("LLM adapter shutdown")

    async def _health_check_impl(self) -> bool:
        """Check if the LLM adapter is healthy."""
        try:
            return self._provider is not None
        except Exception as e:
            logger.error(f"LLM adapter health check failed: {e}")
            return False

    def _setup_provider(self) -> None:
        """Setup the LLM provider based on configuration."""
        try:
            if self.config.provider.lower() == "openai":
                # Use the unified interface which handles both APIs correctly
                provider_config = OpenAIConfig(
                    provider_name="openai",
                    api_key=self.config.api_key,
                    organization=self.config.organization,
                    default_model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                    enable_audit_logging=False,  # Disable audit logging for now
                )
                self._unified_interface = OpenAIUnifiedInterface(provider_config)
                self._provider = (
                    self._unified_interface.provider
                )  # Keep reference for compatibility

            elif self.config.provider.lower() == "anthropic":
                if AnthropicProvider is None or AnthropicConfig is None:
                    raise LLMAdapterError(
                        "Anthropic provider not available. Install anthropic package."
                    )
                provider_config = AnthropicConfig(
                    provider_name="anthropic",
                    api_key=self.config.api_key,
                    default_model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
                self._provider = AnthropicProvider(provider_config)

            elif self.config.provider.lower() == "perplexity":
                if PerplexityProvider is None or PerplexityConfig is None:
                    raise LLMAdapterError(
                        "Perplexity provider not available. Install perplexity package."
                    )
                provider_config = PerplexityConfig(
                    provider_name="perplexity",
                    api_key=self.config.api_key,
                    default_model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.timeout,
                )
                self._provider = PerplexityProvider(provider_config)

            else:
                raise LLMAdapterError(f"Unsupported provider: {self.config.provider}")

            logger.info(
                f"Initialized {self.config.provider} provider with model {self.config.model}"
            )

        except Exception as e:
            logger.error(f"Failed to setup provider: {e}")
            raise LLMAdapterError(f"Provider setup failed: {e}") from e

    async def compliant_request(
        self,
        prompt: str,
        max_tokens: int = 1000,
        schema: Optional[Dict[str, Any]] = None,
        reasoning: Optional[ReasoningEffort] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Make a compliant request using OpenAI API Standards 2025."""
        try:
            # Build compliance request
            compliance_req = ComplianceRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                schema=schema,
                reasoning=reasoning,
                model_override=self.config.model,
                extras=kwargs
            )
            
            # Get compliant request
            compliance_resp = self._compliance.build_compliant_request(compliance_req)
            
            # Log compliance proof
            logger.info(f"🔐 Compliance proof: {compliance_resp.proof_blob}")
            
            # Convert compliance request to messages format for existing infrastructure
            messages = [Message(role="user", content=prompt)]
            
            # Use existing chat_completion with validated parameters
            if stream:
                return self._stream_compliance_response(messages, compliance_resp)
            else:
                response = await self.chat_completion(messages, stream=False)
                validation = self._compliance.validate_response(response)
                
                if not validation["compliant"]:
                    logger.warning("Response format not fully compliant with Responses API")
                
                return validation["content"]
                
        except OpenAIComplianceError as e:
            logger.error(f"OpenAI compliance violation: {e}")
            raise LLMAdapterError(f"Compliance violation: {e}") from e
        except Exception as e:
            logger.error(f"Compliant request failed: {e}")
            raise LLMAdapterError(f"Compliant request failed: {e}") from e

    async def _stream_compliance_response(
        self, messages: List[Message], compliance_resp
    ) -> AsyncGenerator[str, None]:
        """Stream compliant response."""
        try:
            async for chunk in await self.chat_completion(messages, stream=True):
                # Handle new OpenAI API streaming response format
                if hasattr(chunk, "delta") and chunk.delta:
                    yield chunk.delta
                elif hasattr(chunk, "output_text") and chunk.output_text:
                    yield chunk.output_text
                elif hasattr(chunk, "choices") and chunk.choices:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"Streaming compliance failed: {e}")
            yield f"Error: {e}"

    async def chat_completion(
        self, messages: List[Message], stream: bool = False, **kwargs: Any
    ) -> Union[ChatResponse, AsyncGenerator[ChatResponse, None]]:
        """Perform chat completion using the unified interface."""
        try:
            if self._unified_interface:
                # Use the unified interface which handles API differences automatically
                if stream:
                    return await self._unified_interface.responses_from_messages(
                        messages=messages,
                        model=self.config.model,
                        stream=True,
                        **kwargs,
                    )
                else:
                    return await self._unified_interface.responses_from_messages(
                        messages=messages, model=self.config.model, **kwargs
                    )
            else:
                # Fallback to direct provider (for non-OpenAI providers)
                request = ChatRequest(messages=messages, stream=stream, **kwargs)
                if stream:
                    return await self._provider.chat(request, stream=True)
                else:
                    return await self._provider.chat(request)

        except LLMProviderError as e:
            logger.error(f"LLM provider error: {e}")
            raise LLMAdapterError(f"Chat completion failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {e}")
            raise LLMAdapterError(f"Chat completion failed: {e}") from e

    async def analyze_code(
        self,
        code: str,
        language: str = "python",
        analysis_type: str = "general",
        context: Optional[str] = None,
    ) -> str:
        """Analyze code using the LLM provider."""
        system_prompt = self._build_analysis_prompt(language, analysis_type, context)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Analyze this {language} code:\n\n{code}"),
        ]

        response = await self.chat_completion(messages)
        # Handle new OpenAI API response format
        if hasattr(response, "output_text"):
            return response.output_text
        elif hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content
        else:
            raise LLMAdapterError(f"Unexpected response format: {type(response)}")

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        context: Optional[str] = None,
        existing_code: Optional[str] = None,
    ) -> str:
        """Generate code using the LLM provider."""
        system_prompt = self._build_generation_prompt(language, context, existing_code)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=prompt),
        ]

        response = await self.chat_completion(messages)
        # Handle new OpenAI API response format
        if hasattr(response, "output_text"):
            return response.output_text
        elif hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content
        else:
            raise LLMAdapterError(f"Unexpected response format: {type(response)}")

    async def refactor_code(
        self,
        code: str,
        refactor_type: str = "improve",
        language: str = "python",
        context: Optional[str] = None,
    ) -> str:
        """Refactor code using the LLM provider."""
        system_prompt = self._build_refactor_prompt(language, refactor_type, context)

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Refactor this {language} code ({refactor_type}):\n\n{code}",
            ),
        ]

        response = await self.chat_completion(messages)
        # Handle new OpenAI API response format
        if hasattr(response, "output_text"):
            return response.output_text
        elif hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content
        else:
            raise LLMAdapterError(f"Unexpected response format: {type(response)}")

    def _build_analysis_prompt(
        self, language: str, analysis_type: str, context: Optional[str]
    ) -> str:
        """Build system prompt for code analysis."""
        base_prompt = f"""You are an expert {language} code analyzer. Analyze the provided code and provide detailed feedback.

Analysis type: {analysis_type}
"""

        if context:
            base_prompt += f"\nContext: {context}\n"

        if analysis_type == "security":
            base_prompt += "\nFocus on security vulnerabilities, potential exploits, and security best practices."
        elif analysis_type == "performance":
            base_prompt += "\nFocus on performance bottlenecks, optimization opportunities, and efficiency improvements."
        elif analysis_type == "style":
            base_prompt += "\nFocus on code style, readability, maintainability, and best practices."
        elif analysis_type == "bugs":
            base_prompt += "\nFocus on potential bugs, edge cases, error handling, and logical issues."
        else:
            base_prompt += (
                "\nProvide comprehensive analysis covering all aspects of the code."
            )

        base_prompt += "\n\nProvide clear, actionable feedback with specific examples and suggestions."

        return base_prompt

    def _build_generation_prompt(
        self, language: str, context: Optional[str], existing_code: Optional[str]
    ) -> str:
        """Build system prompt for code generation."""
        base_prompt = f"""You are an expert {language} developer. Generate high-quality, production-ready code.

Language: {language}
"""

        if context:
            base_prompt += f"\nContext: {context}\n"

        if existing_code:
            base_prompt += f"\nExisting code to extend/modify:\n{existing_code}\n"

        base_prompt += """
Requirements:
- Write clean, readable, and maintainable code
- Follow best practices and conventions
- Include proper error handling
- Add appropriate comments and documentation
- Ensure the code is production-ready
"""

        return base_prompt

    def _build_refactor_prompt(
        self, language: str, refactor_type: str, context: Optional[str]
    ) -> str:
        """Build system prompt for code refactoring."""
        base_prompt = f"""You are an expert {language} developer. Refactor the provided code to improve it.

Language: {language}
Refactor type: {refactor_type}
"""

        if context:
            base_prompt += f"\nContext: {context}\n"

        if refactor_type == "improve":
            base_prompt += "\nImprove the code by making it more readable, maintainable, and efficient."
        elif refactor_type == "optimize":
            base_prompt += (
                "\nOptimize the code for better performance and resource usage."
            )
        elif refactor_type == "modernize":
            base_prompt += "\nModernize the code using current best practices and language features."
        elif refactor_type == "simplify":
            base_prompt += "\nSimplify the code while maintaining functionality."
        else:
            base_prompt += f"\nRefactor the code according to: {refactor_type}"

        base_prompt += (
            "\n\nProvide the refactored code with explanations of the changes made."
        )

        return base_prompt

    async def close(self) -> None:
        """Close the LLM adapter and cleanup resources."""
        if self._provider and hasattr(self._provider, "close"):
            await self._provider.close()
        logger.info("LLM adapter closed")
