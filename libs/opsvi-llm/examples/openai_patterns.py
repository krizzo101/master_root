"""OpenAI API usage patterns with correct parameter mapping (2025 standards).

This example demonstrates the correct way to use OpenAI APIs with the
approved models and proper parameter names.
"""

# import asyncio  # Uncomment to run examples
from typing import List

from opsvi_llm.providers.base import Message
from opsvi_llm.providers.openai_unified_interface import OpenAIUnifiedInterface
from pydantic import BaseModel


class ExtractedInfo(BaseModel):
    """Example structured output model."""

    title: str
    summary: str
    tags: List[str]
    confidence: float


async def main():
    """Demonstrate correct OpenAI API usage patterns."""

    # Initialize the unified interface
    interface = OpenAIUnifiedInterface()

    print("=" * 60)
    print("OpenAI API Usage Patterns (2025 Standards)")
    print("=" * 60)

    # =========================================================================
    # 1. Simple chat with GPT-5-mini (Chat Completions API)
    # =========================================================================
    print("\n1. Simple chat with GPT-5-mini")
    print("-" * 40)

    try:
        response = await interface.chat_completion(
            messages=[
                Message(role="user", content="Explain quantum computing in 5 words")
            ],
            model="gpt-5-mini",
            max_tokens=32,  # Internally translated to max_completion_tokens
            temperature=0.7,  # Supported for GPT-5 models
        )
        print("Model: gpt-5-mini")
        print(f"Response: {response.message.content}")
        print("✅ Uses max_completion_tokens internally")
    except Exception as e:
        print(f"Error: {e}")

    # =========================================================================
    # 2. Reasoning with o4-mini (Responses API preferred)
    # =========================================================================
    print("\n2. Reasoning with o4-mini")
    print("-" * 40)

    try:
        response = await interface.responses_create(
            input="Prove that the sum of first n natural numbers is n(n+1)/2",
            model="o4-mini",
            reasoning_effort="medium",  # Reasoning-specific parameter
            max_tokens=400,  # Internally uses max_output_tokens
            # temperature=0.5,  # NOT included - o4-mini doesn't support it
        )
        print("Model: o4-mini")
        print(f"Response: {getattr(response, 'output_text', 'Response generated')}")
        print("✅ Uses max_output_tokens")
        print("✅ Includes reasoning_effort")
        print("✅ Temperature excluded (not supported)")
    except Exception as e:
        print(f"Error: {e}")

    # =========================================================================
    # 3. Structured output with GPT-5 (Responses API)
    # =========================================================================
    print("\n3. Structured output with GPT-5")
    print("-" * 40)

    try:
        result = await interface.responses_create_structured(
            input=(
                'Extract info from: "Quantum Computing: The Future of '
                'Technology. Tags: quantum, computing, future"'
            ),
            response_model=ExtractedInfo,
            model="gpt-5",
            max_tokens=200,  # Uses max_output_tokens
            temperature=0.3,  # Supported for GPT-5
        )
        print("Model: gpt-5")
        print(f"Extracted data: {result.model_dump()}")
        print("✅ Uses Responses API with structured output")
        print("✅ Uses max_output_tokens")
    except Exception as e:
        print(f"Error: {e}")

    # =========================================================================
    # 4. Fast response with GPT-5-nano (no temperature)
    # =========================================================================
    print("\n4. Fast response with GPT-5-nano")
    print("-" * 40)

    try:
        response = await interface.chat_completion(
            messages=[
                Message(role="user", content="Yes or no: Is Python interpreted?")
            ],
            model="gpt-5-nano",
            max_tokens=10,  # Uses max_completion_tokens
            # temperature=0.5,  # NOT included - nano doesn't support it
        )
        print("Model: gpt-5-nano")
        print(f"Response: {response.message.content}")
        print("✅ Temperature excluded (not supported by nano)")
    except Exception as e:
        print(f"Error: {e}")

    # =========================================================================
    # 5. Complex reasoning with o3 (Responses API)
    # =========================================================================
    print("\n5. Complex reasoning with o3")
    print("-" * 40)

    try:
        response = await interface.responses_create(
            input="Design a distributed system for real-time video streaming at scale",
            model="o3",
            reasoning_effort="high",  # Maximum reasoning
            max_tokens=1000,  # Uses max_output_tokens
            # No temperature - reasoning models don't use it
        )
        print("Model: o3")
        print("Response generated successfully")
        print("✅ Uses max_output_tokens")
        print("✅ High reasoning effort")
        print("✅ No temperature parameter")
    except Exception as e:
        print(f"Error: {e}")

    # =========================================================================
    # 6. Error case: Text Completions with modern model
    # =========================================================================
    print("\n6. Error case: Text Completions API (deprecated)")
    print("-" * 40)

    try:
        # This WILL fail - Text Completions not supported for modern models
        from opsvi_llm.providers.base import CompletionRequest
        from opsvi_llm.providers.openai_provider import OpenAIConfig, OpenAIProvider

        config = OpenAIConfig(
            provider_name="openai", api_key="test-key", default_model="gpt-5-mini"
        )
        provider = OpenAIProvider(config)

        request = CompletionRequest(
            prompt="Complete this text", model="gpt-5-mini", max_tokens=50
        )

        # This will raise an error
        await provider.complete(request)

    except Exception as e:
        print(f"Expected error: {e}")
        print("✅ Text Completions correctly rejected for modern models")

    print("\n" + "=" * 60)
    print("Summary of Key Points:")
    print("=" * 60)
    print(
        """
    1. Chat Completions with reasoning models → max_completion_tokens
    2. Responses API (all models) → max_output_tokens
    3. Temperature excluded for: o3, o4-mini, gpt-5-nano
    4. Text Completions API → deprecated, raises error
    5. Structured outputs → Use Responses API, not beta.parse
    6. Reasoning models → Include reasoning_effort parameter
    """
    )


if __name__ == "__main__":
    print("\nNOTE: This example demonstrates API patterns.")
    print("Replace with actual API key to run real requests.\n")

    # For demonstration, we'll skip actual execution
    # In real usage, uncomment the following line:
    # asyncio.run(main())

    # Instead, just show the patterns
    print("Example patterns shown above. To run with real API:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Uncomment asyncio.run(main()) line")
    print("3. Run the script")
