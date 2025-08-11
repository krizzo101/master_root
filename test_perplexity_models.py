#!/usr/bin/env python3
"""Test Perplexity API to get available models."""

import asyncio
import aiohttp
import os


async def test_perplexity_models():
    """Test Perplexity API to get available models."""
    api_key = "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"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        try:
            # Get models
            async with session.get(
                "https://api.perplexity.ai/models", headers=headers
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")

                if response.status == 200:
                    data = await response.json()
                    print("Available models:")
                    for model in data.get("data", []):
                        print(f"  - {model.get('id')}")
                else:
                    text = await response.text()
                    print(f"Error response: {text}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_perplexity_models())
