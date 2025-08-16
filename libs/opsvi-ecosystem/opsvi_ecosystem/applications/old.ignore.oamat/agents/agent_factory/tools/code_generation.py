"""
OAMAT Agent Factory - Code Generation Tools

Code generation and development tools for LangGraph agents.
Extracted from agent_factory.py for better modularity and maintainability.
"""

import logging

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger("OAMAT.AgentFactory.CodeGenerationTools")


class CodeRequest(BaseModel):
    """Code generation task input schema"""

    task_description: str = Field(
        ..., min_length=10, description="Code task description"
    )
    language: str = Field("python", description="Programming language")
    framework: str | None = Field(None, description="Framework or library to use")
    requirements: list[str] = Field(
        default_factory=list, description="Specific requirements"
    )


class ReviewRequest(BaseModel):
    """Code review task input schema"""

    code: str = Field(..., min_length=10, description="Code to review")
    language: str = Field("python", description="Programming language")
    review_type: str = Field(
        "general", description="Type of review (security, performance, style)"
    )


class DocumentationRequest(BaseModel):
    """Documentation generation task input schema"""

    content: str = Field(..., min_length=10, description="Content to document")
    doc_type: str = Field(
        "api", description="Documentation type (api, user, technical)"
    )
    format: str = Field("markdown", description="Output format (markdown, rst, html)")


def create_code_generation_tool(base_agent=None):
    """Create a code generation tool that fails if base_agent is unavailable"""

    @tool
    def generate_code(
        task_description: str,
        language: str = "python",
        framework: str | None = None,
        requirements: list[str] = None,
    ) -> str:
        """
        Generates code based on the task description and requirements.
        Fails if base_agent is not available.
        """
        if not base_agent:
            raise RuntimeError(
                "Code generation tool is not available: base_agent not configured."
            )
        if not task_description.strip():
            raise ValueError("Cannot generate code without task description")

        try:
            # Build requirements context
            requirements_text = ""
            if requirements:
                requirements_text = "\nSpecific requirements:\n" + "\n".join(
                    f"- {req}" for req in requirements
                )

            framework_text = f" using {framework}" if framework else ""

            prompt = f"""You are an expert {language} developer. Generate clean, well-documented, production-ready code that follows best practices. Include appropriate imports, error handling, and comments where needed.

Generate {language} code{framework_text} for the following task:

{task_description}{requirements_text}

Please provide complete, working code with proper structure and documentation."""

            result = base_agent.process_request(
                {"task": "code_generation", "prompt": prompt}
            )
            return result.get("response", "Error generating code")

        except Exception as e:
            raise RuntimeError(f"Code generation failed: {str(e)}")

    return generate_code


def create_code_review_tool(base_agent=None):
    """Create a code review tool that fails if base_agent is unavailable"""

    @tool
    def review_code(code: str, language: str = "python") -> str:
        """
        Reviews code for quality, best practices, and potential issues.
        Fails if base_agent is not available.
        """
        if not base_agent:
            raise RuntimeError(
                "Code review tool is not available: base_agent not configured."
            )
        if not code.strip():
            raise ValueError("Cannot review empty code")

        try:
            prompt = f"""You are an expert {language} code reviewer. Provide detailed feedback on code quality, best practices, potential bugs, security issues, and optimization opportunities.

Please review this {language} code:

```{language}
{code}
```"""
            result = base_agent.process_request(
                {"task": "code_review", "prompt": prompt}
            )
            return result.get("response", "Error reviewing code")

        except Exception as e:
            raise RuntimeError(f"Code review failed: {str(e)}")

    return review_code


def create_documentation_tool(base_agent=None):
    """Create a documentation generation tool"""

    @tool
    def generate_documentation(
        content: str, doc_type: str = "api", format: str = "markdown"
    ) -> str:
        """
        Generates documentation for code or projects.

        Args:
            content: Code or content to document
            doc_type: Type of documentation (api, user, technical, README)
            format: Output format (markdown, rst, html)
        """
        try:
            # Construct documentation prompt
            prompt = f"""
Generate {doc_type} documentation in {format} format for the following content:

{content}

Please provide comprehensive documentation including:
- Clear overview and purpose
- Installation and setup instructions (if applicable)
- Usage examples and code snippets
- API reference with parameters and return values
- Configuration options and settings
- Troubleshooting and common issues
- Contributing guidelines (if applicable)
- Proper formatting and structure for {format}
"""

            if base_agent:
                # Use base agent for actual documentation generation
                result = base_agent.process_request(
                    {"task": "documentation", "prompt": prompt}
                )
                return result.get("response", "Error generating documentation")
            else:
                # Raise an error if the base_agent is not available
                raise RuntimeError(
                    "Documentation tool is not available: base_agent not configured."
                )

        except Exception as e:
            error_msg = f"Error generating documentation: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    return generate_documentation


def create_completion_tool():
    """Create a task completion tool"""

    @tool
    def complete(message: str = "Task completed successfully") -> str:
        """
        Marks a task as complete with an optional completion message.

        Args:
            message: Completion message to display
        """
        logger.info(f"Task completion: {message}")
        return f"✅ {message}"

    return complete


# Export all public functions and classes
__all__ = [
    "CodeRequest",
    "ReviewRequest",
    "DocumentationRequest",
    "create_code_generation_tool",
    "create_code_review_tool",
    "create_documentation_tool",
    "create_completion_tool",
]
