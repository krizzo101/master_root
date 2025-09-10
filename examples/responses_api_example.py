#!/usr/bin/env python3
"""
OpenAI Responses API Example - 2025 Best Practices
==================================================
Demonstrates the PREFERRED method for structured outputs using OpenAI's Responses API.
"""

import asyncio
from typing import List

from pydantic import BaseModel, Field

from libs.opsvi_llm.opsvi_llm.providers.base import Message
from libs.opsvi_llm.opsvi_llm.providers.openai_provider import (
    OpenAIConfig,
    OpenAIProvider,
)


# Define structured output models
class TaskAnalysis(BaseModel):
    """Structured analysis of a task."""

    title: str = Field(description="Brief title of the task")
    category: str = Field(
        description="Task category: bug, feature, refactor, test, docs"
    )
    priority: str = Field(description="Priority level: low, medium, high, critical")
    estimated_hours: float = Field(ge=0.1, description="Estimated hours to complete")
    dependencies: List[str] = Field(
        default_factory=list, description="Task dependencies"
    )
    reasoning: str = Field(description="Reasoning behind the analysis")


class CodeReview(BaseModel):
    """Code review response structure."""

    quality_score: int = Field(ge=1, le=10, description="Code quality score 1-10")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    improvements: List[str] = Field(
        default_factory=list, description="Suggested improvements"
    )
    security_concerns: List[str] = Field(
        default_factory=list, description="Security issues"
    )


async def example_task_analysis():
    """Example: Analyze a task using o4-mini for reasoning."""
    print("\n=== Task Analysis Example (Uses o4-mini for reasoning) ===")

    # Initialize provider with 2025 models
    config = OpenAIConfig(
        api_key="your-api-key-here",  # Set via environment variable
        default_model="gpt-5-mini",
        enable_audit_logging=True,
    )

    provider = OpenAIProvider(config)

    # Create messages for task analysis
    messages = [
        Message(
            role="system",
            content="You are a project manager expert. "
            "Analyze tasks and provide structured insights.",
        ),
        Message(
            role="user",
            content="Analyze this task: Refactor the authentication module to use "
            "JWT tokens instead of sessions. This includes updating "
            "login/logout endpoints and protected routes.",
        ),
    ]

    try:
        # The word "analyze" triggers o4-mini model selection for reasoning
        result = await provider.create_structured_response(
            messages=messages,
            response_model=TaskAnalysis,
            temperature=0.3,  # Lower temperature for analytical tasks
        )

        print(f"Title: {result.title}")
        print(f"Category: {result.category}")
        print(f"Priority: {result.priority}")
        print(f"Estimated Hours: {result.estimated_hours}")
        print(
            f"Dependencies: {', '.join(result.dependencies) if result.dependencies else 'None'}"
        )
        print(f"Reasoning: {result.reasoning}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await provider._close_client()


async def example_code_review():
    """Example: Review code using gpt-5-mini for execution."""
    print("\n=== Code Review Example (Uses gpt-5-mini for execution) ===")

    config = OpenAIConfig(api_key="your-api-key-here", default_model="gpt-5-mini")

    provider = OpenAIProvider(config)

    code_sample = """
def process_data(data):
    result = []
    for item in data:
        if item['status'] == 'active':
            result.append(item)
    return result
"""

    messages = [
        Message(
            role="system",
            content="You are a senior code reviewer. Provide detailed code analysis.",
        ),
        Message(
            role="user",
            content=f"Review this Python code and provide structured feedback:\n\n{code_sample}",
        ),
    ]

    try:
        # Explicitly use gpt-5-mini for code review (execution task)
        result = await provider.create_structured_response(
            messages=messages,
            response_model=CodeReview,
            model="gpt-5-mini",
            temperature=0.5,
        )

        print(f"Quality Score: {result.quality_score}/10")
        print(f"Issues: {result.issues}")
        print(f"Improvements: {result.improvements}")
        print(f"Security Concerns: {result.security_concerns}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await provider._close_client()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("OpenAI Responses API Examples - 2025 Standards")
    print("Using GPT-5 series and o4-mini models")
    print("=" * 60)

    # Run task analysis (will use o4-mini for reasoning)
    await example_task_analysis()

    # Run code review (will use gpt-5-mini for execution)
    await example_code_review()

    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: Set your OpenAI API key via environment variable:
    # export OPENAI_API_KEY="your-key-here"
    asyncio.run(main())
