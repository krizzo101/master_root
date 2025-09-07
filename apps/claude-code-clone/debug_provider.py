#!/usr/bin/env python3
"""Debug provider initialization."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code import ClaudeCodeConfig, LLMAdapter


async def debug_provider():
    """Debug provider initialization."""
    print("🔍 Debugging Provider Initialization")
    print("=" * 50)
    
    # Configuration
    config = ClaudeCodeConfig(
        provider="openai",
        model="gpt-5-mini",  # ✅ APPROVED MODEL
        api_key=os.getenv("OPENAI_API_KEY"),
        working_directory=".",
    )
    
    print(f"✅ Config created: {config.provider} with {config.model}")
    print(f"✅ API Key: {'Set' if config.api_key else 'Not set'}")
    
    # Initialize adapter
    print("\n🔧 Initializing LLM Adapter...")
    adapter = LLMAdapter(config)
    
    print(f"✅ Adapter created")
    print(f"✅ Provider: {adapter._provider}")
    print(f"✅ Provider type: {type(adapter._provider)}")
    
    if adapter._provider:
        print(f"✅ Provider methods: {[m for m in dir(adapter._provider) if not m.startswith('_')]}")
    else:
        print("❌ Provider is None!")
    
    # Try to initialize
    try:
        await adapter.initialize()
        print("✅ Adapter initialized successfully")
    except Exception as e:
        print(f"❌ Adapter initialization failed: {e}")
    
    # Try a simple chat
    try:
        from opsvi_llm import Message
        messages = [Message(role="user", content="Hello, world!")]
        response = await adapter.chat_completion(messages)
        print(f"✅ Chat completion successful: {response}")
    except Exception as e:
        print(f"❌ Chat completion failed: {e}")
    
    await adapter.close()


if __name__ == "__main__":
    asyncio.run(debug_provider())
