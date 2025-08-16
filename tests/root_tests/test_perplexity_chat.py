#!/usr/bin/env python3
"""Test Perplexity chat completion with different models."""

import asyncio

import aiohttp


async def test_perplexity_chat():
    """Test Perplexity chat completion."""
    api_key = "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"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Test different model names
    models_to_test = [
        "llama-3.1-8b-online",
        "llama-3.1-70b-online",
        "llama-3.1-8b",
        "llama-3.1-70b",
        "mixtral-8x7b-instruct",
        "codellama-34b-instruct",
        "llama-2-70b-chat",
        "mistral-7b-instruct",
        "pplx-7b-online",
        "pplx-70b-online",
        "pplx-7b-chat",
        "pplx-70b-chat",
    ]

    async with aiohttp.ClientSession() as session:
        for model in models_to_test:
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Hello, what models are available?"}
                    ],
                    "max_tokens": 50,
                }

                print(f"Testing model: {model}")
                async with session.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"  ✅ SUCCESS: {model}")
                        print(
                            f"     Response: {data.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]}..."
                        )
                        break
                    else:
                        error_text = await response.text()
                        print(f"  ❌ FAILED: {model} - {response.status}")
                        if error_text:
                            print(f"     Error: {error_text[:200]}")

            except Exception as e:
                print(f"  ❌ ERROR: {model} - {e}")

            print()


if __name__ == "__main__":
    asyncio.run(test_perplexity_chat())
