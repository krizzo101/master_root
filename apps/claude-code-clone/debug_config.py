#!/usr/bin/env python3
"""Debug config loading for claude-code-clone"""

import asyncio
import os

from src.claude_code.config import ClaudeCodeConfig
from src.claude_code.providers.llm_adapter import LLMAdapter

print("=== Environment ===")
print(f"OPENAI_API_KEY exists: {'OPENAI_API_KEY' in os.environ}")
print(f"OPENAI_API_KEY value: {os.environ.get('OPENAI_API_KEY', 'NOT_SET')[:10]}...")

print("\n=== Config Loading ===")
config = ClaudeCodeConfig()
print(f"Config provider: {config.provider}")
print(f"Config model: {config.model}")
print(f"Config api_key: {config.api_key[:10] if config.api_key else 'None'}...")


async def test_adapter():
    print("\n=== LLM Adapter ===")
    try:
        adapter = LLMAdapter(config)
        print("LLM Adapter created successfully")

        # Try code generation
        result = await adapter.generate_code("Create a simple hello world function")
        print(f"Generation result: {result}")

    except Exception as e:
        print(f"LLM Adapter error: {e}")
        import traceback

        traceback.print_exc()


asyncio.run(test_adapter())
