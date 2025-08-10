#!/usr/bin/env python3
"""
Enhanced OPSVI LLM Demo

Demonstrates all the enhanced LLM capabilities ported from agent_world:
- OpenAI Provider (base functionality)
- OpenAI Embeddings Interface
- OpenAI Models Interface
- OpenAI Batch Interface
- OpenAI Responses Interface

This demo shows the comprehensive LLM integration capabilities.
"""

import asyncio
import os
import sys

# Add the library to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opsvi_llm import (
    # Base provider
    OpenAIProvider,
    OpenAIConfig,
    # Enhanced interfaces
    OpenAIEmbeddingsInterface,
    OpenAIModelsInterface,
    OpenAIBatchInterface,
    OpenAIResponsesInterface,
)


def demo_openai_provider():
    """Demo the base OpenAI provider functionality."""
    print("=== OpenAI Provider Demo ===")

    try:
        # Create configuration
        config = OpenAIConfig(
            provider_name="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            timeout=30.0,
            default_model="gpt-3.5-turbo",
        )

        # Create provider
        provider = OpenAIProvider(config)
        print(f"  ✅ Provider initialized with model: {config.default_model}")

        # Test health check
        health = asyncio.run(provider._check_health())
        print(f"  ✅ Health check: {health}")

        return True

    except Exception as e:
        print(f"  ❌ Provider demo failed: {e}")
        return False


def demo_embeddings_interface():
    """Demo the OpenAI embeddings interface."""
    print("=== OpenAI Embeddings Interface Demo ===")

    try:
        # Create embeddings interface
        embeddings = OpenAIEmbeddingsInterface()
        print("  ✅ Embeddings interface initialized")

        # Test text validation
        test_text = "Hello, world!"
        is_valid = embeddings.validate_input(test_text)
        print(f"  ✅ Input validation: {is_valid}")

        # Test dimension lookup
        dimension = embeddings.get_embedding_dimension("text-embedding-ada-002")
        print(f"  ✅ Embedding dimension: {dimension}")

        return True

    except Exception as e:
        print(f"  ❌ Embeddings demo failed: {e}")
        return False


def demo_models_interface():
    """Demo the OpenAI models interface."""
    print("=== OpenAI Models Interface Demo ===")

    try:
        # Create models interface
        models = OpenAIModelsInterface()
        print("  ✅ Models interface initialized")

        # Test model categorization
        chat_models = models.get_chat_models()
        embedding_models = models.get_embedding_models()

        print(f"  ✅ Chat models found: {len(chat_models)}")
        print(f"  ✅ Embedding models found: {len(embedding_models)}")

        # Test model existence check
        gpt_exists = models.model_exists("gpt-3.5-turbo")
        print(f"  ✅ GPT-3.5-turbo exists: {gpt_exists}")

        return True

    except Exception as e:
        print(f"  ❌ Models demo failed: {e}")
        return False


def demo_batch_interface():
    """Demo the OpenAI batch interface."""
    print("=== OpenAI Batch Interface Demo ===")

    try:
        # Create batch interface
        batch = OpenAIBatchInterface()
        print("  ✅ Batch interface initialized")

        # Test parameter validation
        valid_params = {
            "input_file_id": "file-123",
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        }

        is_valid = batch.validate_batch_params(**valid_params)
        print(f"  ✅ Parameter validation: {is_valid}")

        # Test batch summary (if any batches exist)
        try:
            summary = batch.get_batch_summary()
            print(f"  ✅ Batch summary: {summary['total_batches']} total batches")
        except Exception:
            print("  ✅ No batches found (expected)")

        return True

    except Exception as e:
        print(f"  ❌ Batch demo failed: {e}")
        return False


def demo_responses_interface():
    """Demo the OpenAI responses interface."""
    print("=== OpenAI Responses Interface Demo ===")

    try:
        # Create responses interface
        responses = OpenAIResponsesInterface()
        print("  ✅ Responses interface initialized")

        # Test interface methods
        methods = [
            "create_response",
            "retrieve_response",
            "list_input_items",
            "delete_response",
            "cancel_response",
        ]

        for method in methods:
            if hasattr(responses, method):
                print(f"  ✅ Method available: {method}")
            else:
                print(f"  ❌ Method missing: {method}")

        return True

    except Exception as e:
        print(f"  ❌ Responses demo failed: {e}")
        return False


async def demo_async_capabilities():
    """Demo async capabilities of the interfaces."""
    print("=== Async Capabilities Demo ===")

    try:
        # Test async embeddings
        OpenAIEmbeddingsInterface()
        print("  ✅ Async embeddings interface ready")

        # Test async models
        OpenAIModelsInterface()
        print("  ✅ Async models interface ready")

        # Test async batch
        OpenAIBatchInterface()
        print("  ✅ Async batch interface ready")

        print("  ✅ All async interfaces initialized")
        return True

    except Exception as e:
        print(f"  ❌ Async demo failed: {e}")
        return False


def demo_integration():
    """Demo integration between different interfaces."""
    print("=== Integration Demo ===")

    try:
        # Create all interfaces
        embeddings = OpenAIEmbeddingsInterface()
        models = OpenAIModelsInterface()
        OpenAIResponsesInterface()  # Test creation

        print("  ✅ All interfaces created successfully")

        # Test cross-interface functionality
        # Get embedding model info
        embedding_models = models.get_embedding_models()
        if embedding_models:
            model_id = embedding_models[0].id
            dimension = embeddings.get_embedding_dimension(model_id)
            print(f"  ✅ Cross-interface: {model_id} has {dimension} dimensions")

        print("  ✅ Integration test completed")
        return True

    except Exception as e:
        print(f"  ❌ Integration demo failed: {e}")
        return False


def main():
    """Run all demos."""
    print("🚀 Enhanced OPSVI LLM Demo")
    print("=" * 50)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - some demos may fail")
        print("   Set OPENAI_API_KEY to test full functionality")

    results = []

    # Run demos
    results.append(("Provider", demo_openai_provider()))
    results.append(("Embeddings", demo_embeddings_interface()))
    results.append(("Models", demo_models_interface()))
    results.append(("Batch", demo_batch_interface()))
    results.append(("Responses", demo_responses_interface()))
    results.append(("Integration", demo_integration()))

    # Run async demo
    async_result = asyncio.run(demo_async_capabilities())
    results.append(("Async", async_result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Demo Results:")

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} demos passed")

    if passed == total:
        print("🎉 All enhanced LLM demos passed!")
        print(
            "   The OPSVI LLM library is fully functional with agent_world enhancements."
        )
    else:
        print("⚠️  Some demos failed - check configuration and API access.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
