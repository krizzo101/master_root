#!/usr/bin/env python3
"""
Simple Hello World Async Function
Demonstrates basic async functionality
"""

import asyncio


async def hello_world_async(name: str = "World", delay: float = 1.0) -> str:
    """
    Simple hello world async function with optional delay

    Args:
        name: Name to greet (default: "World")
        delay: Delay in seconds before returning greeting

    Returns:
        Greeting message
    """
    print(f"Starting greeting for {name}...")
    await asyncio.sleep(delay)
    greeting = f"Hello, {name}!"
    print(f"Completed greeting: {greeting}")
    return greeting


async def main():
    """Demonstrate the hello world async function"""
    print("🌟 Hello World Async Demo")

    # Basic usage
    result1 = await hello_world_async()
    print(f"Result 1: {result1}")

    # With custom name
    result2 = await hello_world_async("Claude", 0.5)
    print(f"Result 2: {result2}")

    # Multiple concurrent greetings
    print("\nConcurrent greetings:")
    tasks = [
        hello_world_async("Alice", 0.3),
        hello_world_async("Bob", 0.2),
        hello_world_async("Charlie", 0.4),
    ]

    results = await asyncio.gather(*tasks)
    for i, result in enumerate(results, 1):
        print(f"Concurrent result {i}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
