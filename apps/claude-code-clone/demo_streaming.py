#!/usr/bin/env python3
"""Demonstrate streaming capabilities."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code import ClaudeCodeConfig, StreamingHandler


async def demonstrate_streaming():
    """Demonstrate streaming capabilities."""
    print("🌊 Claude Code Clone - Streaming Demo")
    print("=" * 50)

    # Configuration
    config = ClaudeCodeConfig(
        working_directory=".",
        enable_streaming=True,
    )

    # Initialize streaming handler
    streaming_handler = StreamingHandler(config)

    print("🔧 Initializing streaming handler...")
    await streaming_handler.initialize()
    print("✅ Streaming handler initialized")
    print()

    # Demo 1: File analysis streaming
    print("📄 **Demo 1: File Analysis Streaming**")
    print("-" * 40)

    async for chunk in streaming_handler.stream_file_analysis(
        "sample_code.py", "security"
    ):
        print(f"📊 {chunk['type']}: {chunk['data']}")
        await asyncio.sleep(0.1)  # Small delay for demo effect
    print()

    # Demo 2: Code generation streaming
    print("⚡ **Demo 2: Code Generation Streaming**")
    print("-" * 40)

    async for chunk in streaming_handler.stream_code_generation(
        "Create a secure password hashing function", "python"
    ):
        print(f"🔧 {chunk['type']}: {chunk['data']}")
        await asyncio.sleep(0.1)  # Small delay for demo effect
    print()

    # Demo 3: Project analysis streaming
    print("🏗️  **Demo 3: Project Analysis Streaming**")
    print("-" * 40)

    async for chunk in streaming_handler.stream_project_analysis(
        ".", ["structure", "complexity", "duplicates"]
    ):
        print(f"📈 {chunk['type']}: {chunk['data']}")
        await asyncio.sleep(0.1)  # Small delay for demo effect
    print()

    # Demo 4: Active streams management
    print("🎛️  **Demo 4: Stream Management**")
    print("-" * 40)

    active_streams = streaming_handler.get_active_streams()
    print(f"📊 Active streams: {len(active_streams)}")

    if active_streams:
        print("🔍 Active stream IDs:")
        for stream_id in active_streams:
            print(f"   • {stream_id}")
    else:
        print("✅ No active streams")
    print()

    # Cleanup
    print("🧹 Cleaning up...")
    await streaming_handler.shutdown()
    print("✅ Streaming handler shutdown complete")
    print()

    print("🎉 Streaming demonstration complete!")


if __name__ == "__main__":
    asyncio.run(demonstrate_streaming())

