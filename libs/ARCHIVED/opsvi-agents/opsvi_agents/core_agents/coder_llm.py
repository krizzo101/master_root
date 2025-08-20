"""
LLM-based Code Generation Agent

This agent uses OpenAI models for intelligent code generation, refactoring,
and optimization instead of template-based approaches.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Import opsvi-llm components
from opsvi_llm import (
    ChatRequest,
    Message,
    OpenAIConfig,
    OpenAIProvider,
    OpenAIResponsesInterface,
    StructuredResponse,
)

# Import base agent
from ..base import BaseAgent
from ..config import AgentConfig
from ..types import AgentCapability, AgentResponse, Priority

logger = logging.getLogger(__name__)


class CodeGenerationType(str, Enum):
    """Types of code generation tasks."""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    API = "api"
    TEST = "test"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    DEBUG = "debug"
    DOCUMENTATION = "documentation"
    PATTERN = "design_pattern"


@dataclass
class CodeGenerationRequest:
    """Request for code generation."""

    description: str
    generation_type: CodeGenerationType
    language: str = "python"
    context: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class CodeGenerationResult:
    """Result of code generation."""

    code: str
    language: str
    explanation: str
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMCoderAgent(BaseAgent):
    """
    LLM-based code generation agent using OpenAI models.

    This agent leverages large language models to:
    - Generate code from natural language descriptions
    - Refactor existing code
    - Optimize code performance
    - Fix bugs and issues
    - Create tests
    - Generate documentation
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the LLM Coder Agent."""
        super().__init__(
            config
            or AgentConfig(
                name="LLMCoderAgent",
                enabled=True,
                priority=Priority.HIGH,
                capabilities=[
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.CODE_ANALYSIS,
                    AgentCapability.TESTING,
                ],
            )
        )

        # Initialize OpenAI provider
        self.llm_config = OpenAIConfig(
            provider_name="openai",
            default_model="gpt-4",  # Use GPT-4 for code generation
            timeout=60.0,
            temperature=0.3,  # Lower temperature for more consistent code
        )
        self.llm_provider = OpenAIProvider(self.llm_config)
        self.response_interface = OpenAIResponsesInterface()

        # System prompts for different tasks
        self.system_prompts = self._initialize_system_prompts()

    def _initialize_system_prompts(self) -> Dict[str, str]:
        """Initialize system prompts for different code generation tasks."""
        return {
            CodeGenerationType.FUNCTION: """You are an expert programmer. Generate clean, efficient, and well-documented functions.
Follow best practices for the specified language. Include proper error handling and type hints where applicable.""",
            CodeGenerationType.CLASS: """You are an expert in object-oriented programming. Generate well-structured classes with:
- Clear responsibilities (Single Responsibility Principle)
- Proper encapsulation
- Meaningful method and property names
- Comprehensive documentation
- Type hints and error handling""",
            CodeGenerationType.API: """You are an expert API developer. Generate RESTful API endpoints with:
- Proper HTTP methods and status codes
- Request/response validation
- Error handling
- Security considerations
- OpenAPI/Swagger documentation where applicable""",
            CodeGenerationType.TEST: """You are an expert in test-driven development. Generate comprehensive tests including:
- Unit tests for individual functions/methods
- Edge cases and boundary conditions
- Mocking and fixtures where appropriate
- Clear test descriptions
- Proper assertions""",
            CodeGenerationType.REFACTOR: """You are an expert in code refactoring. Improve code by:
- Enhancing readability and maintainability
- Reducing complexity
- Improving performance where possible
- Following language-specific best practices
- Preserving functionality while improving structure""",
            CodeGenerationType.OPTIMIZE: """You are an expert in code optimization. Optimize code for:
- Performance (time and space complexity)
- Memory usage
- Readability without sacrificing performance
- Language-specific optimizations
- Proper algorithm selection""",
            CodeGenerationType.DEBUG: """You are an expert debugger. Analyze and fix code by:
- Identifying bugs and issues
- Providing clear explanations of problems
- Suggesting multiple solution approaches
- Adding proper error handling
- Improving code robustness""",
            CodeGenerationType.DOCUMENTATION: """You are an expert technical writer. Generate documentation that:
- Clearly explains code functionality
- Includes usage examples
- Documents parameters, returns, and exceptions
- Follows language-specific documentation standards
- Is accessible to developers of various skill levels""",
            CodeGenerationType.PATTERN: """You are an expert in software design patterns. Implement patterns that:
- Solve specific design problems effectively
- Follow established pattern structures
- Include clear documentation of pattern usage
- Demonstrate proper implementation in the target language
- Consider trade-offs and alternatives""",
        }

    async def _execute(self, request: Dict[str, Any]) -> AgentResponse:
        """Execute the code generation request using LLM."""
        try:
            # Parse request
            gen_request = self._parse_request(request)

            # Generate code using LLM
            result = await self._generate_with_llm(gen_request)

            return AgentResponse(
                success=True,
                message="Code generated successfully",
                data={
                    "code": result.code,
                    "language": result.language,
                    "explanation": result.explanation,
                    "warnings": result.warnings,
                    "suggestions": result.suggestions,
                    "metadata": result.metadata,
                },
            )

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return AgentResponse(
                success=False,
                message=f"Code generation failed: {str(e)}",
                data={"error": str(e)},
            )

    def _parse_request(self, request: Dict[str, Any]) -> CodeGenerationRequest:
        """Parse the incoming request into a CodeGenerationRequest."""
        # Determine generation type
        gen_type = request.get("type", CodeGenerationType.FUNCTION)
        if isinstance(gen_type, str):
            gen_type = CodeGenerationType(gen_type)

        return CodeGenerationRequest(
            description=request.get("description", ""),
            generation_type=gen_type,
            language=request.get("language", "python"),
            context=request.get("context", {}),
            requirements=request.get("requirements", []),
            constraints=request.get("constraints", []),
            examples=request.get("examples", []),
        )

    async def _generate_with_llm(
        self, request: CodeGenerationRequest
    ) -> CodeGenerationResult:
        """Generate code using the LLM."""
        # Get appropriate system prompt
        system_prompt = self.system_prompts.get(
            request.generation_type, self.system_prompts[CodeGenerationType.FUNCTION]
        )

        # Build user prompt
        user_prompt = self._build_user_prompt(request)

        # Create chat request
        chat_request = ChatRequest(
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt),
            ],
            model=self.llm_config.default_model,
            temperature=self.llm_config.temperature,
            response_format={"type": "json_object"},  # Request structured JSON response
        )

        # Get response from LLM
        response = await self.llm_provider.chat(chat_request)

        # Parse response
        return self._parse_llm_response(response, request)

    def _build_user_prompt(self, request: CodeGenerationRequest) -> str:
        """Build the user prompt for the LLM."""
        prompt_parts = [
            f"Generate {request.language} code for the following:",
            f"\nDescription: {request.description}",
        ]

        if request.requirements:
            prompt_parts.append("\nRequirements:")
            for req in request.requirements:
                prompt_parts.append(f"- {req}")

        if request.constraints:
            prompt_parts.append("\nConstraints:")
            for constraint in request.constraints:
                prompt_parts.append(f"- {constraint}")

        if request.examples:
            prompt_parts.append("\nExamples for reference:")
            for example in request.examples:
                prompt_parts.append(f"```\n{example}\n```")

        if request.context:
            prompt_parts.append(
                f"\nAdditional context: {json.dumps(request.context, indent=2)}"
            )

        prompt_parts.append(
            """
\nProvide the response in JSON format with the following structure:
{
    "code": "the generated code",
    "explanation": "brief explanation of the code",
    "warnings": ["any warnings or caveats"],
    "suggestions": ["suggestions for improvement or next steps"],
    "metadata": {
        "complexity": "low/medium/high",
        "lines_of_code": number,
        "estimated_time": "development time estimate"
    }
}"""
        )

        return "\n".join(prompt_parts)

    def _parse_llm_response(
        self, response: Any, request: CodeGenerationRequest
    ) -> CodeGenerationResult:
        """Parse the LLM response into a CodeGenerationResult."""
        try:
            # Extract content from response
            if hasattr(response, "content"):
                content = response.content
            elif hasattr(response, "message"):
                content = response.message.content
            else:
                content = str(response)

            # Parse JSON response
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content

            return CodeGenerationResult(
                code=data.get("code", ""),
                language=request.language,
                explanation=data.get("explanation", ""),
                warnings=data.get("warnings", []),
                suggestions=data.get("suggestions", []),
                metadata=data.get("metadata", {}),
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                f"Failed to parse structured response, using raw content: {e}"
            )
            # Fallback to raw content
            return CodeGenerationResult(
                code=str(content),
                language=request.language,
                explanation="Generated code (raw output)",
                warnings=["Response was not in expected format"],
            )

    # Convenience methods for specific generation types

    async def generate_function(
        self, description: str, language: str = "python", **kwargs
    ) -> CodeGenerationResult:
        """Generate a function based on description."""
        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.FUNCTION,
            language=language,
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def generate_class(
        self, description: str, language: str = "python", **kwargs
    ) -> CodeGenerationResult:
        """Generate a class based on description."""
        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.CLASS,
            language=language,
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def generate_tests(
        self,
        code: str,
        language: str = "python",
        test_framework: str = "pytest",
        **kwargs,
    ) -> CodeGenerationResult:
        """Generate tests for given code."""
        description = f"Generate {test_framework} tests for the following code:\n```{language}\n{code}\n```"
        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.TEST,
            language=language,
            context={"test_framework": test_framework},
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def refactor_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: List[str] = None,
        **kwargs,
    ) -> CodeGenerationResult:
        """Refactor existing code."""
        description = f"Refactor the following {language} code"
        if focus_areas:
            description += f" focusing on: {', '.join(focus_areas)}"
        description += f":\n```{language}\n{code}\n```"

        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.REFACTOR,
            language=language,
            requirements=focus_areas or [],
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def optimize_code(
        self,
        code: str,
        language: str = "python",
        optimization_goals: List[str] = None,
        **kwargs,
    ) -> CodeGenerationResult:
        """Optimize existing code."""
        description = f"Optimize the following {language} code"
        if optimization_goals:
            description += f" for: {', '.join(optimization_goals)}"
        description += f":\n```{language}\n{code}\n```"

        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.OPTIMIZE,
            language=language,
            requirements=optimization_goals or ["performance", "readability"],
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def debug_code(
        self, code: str, error_message: str = None, language: str = "python", **kwargs
    ) -> CodeGenerationResult:
        """Debug and fix code issues."""
        description = f"Debug and fix the following {language} code"
        if error_message:
            description += f" which produces this error: {error_message}"
        description += f":\n```{language}\n{code}\n```"

        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.DEBUG,
            language=language,
            context={"error_message": error_message} if error_message else {},
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def generate_documentation(
        self, code: str, language: str = "python", doc_style: str = "google", **kwargs
    ) -> CodeGenerationResult:
        """Generate documentation for code."""
        description = f"Generate {doc_style}-style documentation for the following {language} code:\n```{language}\n{code}\n```"

        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.DOCUMENTATION,
            language=language,
            context={"doc_style": doc_style},
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)

    async def implement_pattern(
        self, pattern_name: str, context: str, language: str = "python", **kwargs
    ) -> CodeGenerationResult:
        """Implement a design pattern."""
        description = (
            f"Implement the {pattern_name} design pattern in {language} for: {context}"
        )

        request = CodeGenerationRequest(
            description=description,
            generation_type=CodeGenerationType.PATTERN,
            language=language,
            context={"pattern": pattern_name},
            **kwargs,
        )
        response = await self._execute(request.__dict__)
        return CodeGenerationResult(**response.data)
