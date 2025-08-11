#!/usr/bin/env python3
"""
Simple test script to verify Perplexity integration works.
"""

import os
import asyncio
from opsvi_llm.providers import PerplexityProvider, PerplexityConfig
from opsvi_llm.providers.base import ChatRequest, Message


async def test_perplexity():
    """Test Perplexity provider with correct model names."""
    print("🧪 Testing Perplexity Integration")
    print("=" * 50)

    # Get API key from environment
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment")
        return

    print(f"✅ API Key found: {api_key[:10]}...")

    # Initialize provider with correct model
    config = PerplexityConfig(
        provider_name="perplexity",
        api_key=api_key,
        default_model="sonar-pro",  # Correct model name
        search_mode="web",
        reasoning_effort="medium",
        temperature=0.7,
        max_tokens=500,
    )

    provider = PerplexityProvider(config)

    try:
        print("🔧 Initializing Perplexity provider...")
        await provider.initialize()
        print("✅ Provider initialized successfully")

        # Test health check
        print("🏥 Testing health check...")
        health = await provider.health_check()
        print(f"✅ Health check: {health}")

        # Test listing models
        print("📋 Listing available models...")
        models = await provider.list_models()
        print(f"✅ Available models: {models}")

        # Test chat completion
        print("💬 Testing chat completion...")
        chat_request = ChatRequest(
            messages=[Message(role="user", content="What is the capital of France?")],
            model="sonar-pro",
            max_tokens=100,
            temperature=0.7,
        )

        response = await provider.chat(chat_request)
        print(f"✅ Chat response: {response.message.content[:100]}...")
        print(f"✅ Model used: {response.model}")

        print("\n🎉 All tests passed! Perplexity integration is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("🔧 Shutting down provider...")
        await provider.shutdown()
        print("✅ Provider shut down successfully")


if __name__ == "__main__":
    asyncio.run(test_perplexity())
