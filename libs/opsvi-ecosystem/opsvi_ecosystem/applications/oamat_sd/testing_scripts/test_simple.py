#!/usr/bin/env python3
import asyncio
import sys

# Add project root to path
sys.path.insert(0, "/home/opsvi/agent_world")

print("Starting simple test...")

try:
    print("Testing basic imports...")
    from src.applications.oamat_sd.src.config.dynamic_config_generator import (
        generate_dynamic_config,
    )

    print("✅ Import successful")

    async def test():
        print("🧪 Testing dynamic config generation...")
        result = await generate_dynamic_config("Simple test request", debug=True)
        print(f"✅ Result type: {type(result)}")
        return result

    # Run test
    result = asyncio.run(test())
    print("🎉 Test completed successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
