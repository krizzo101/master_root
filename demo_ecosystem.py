#!/usr/bin/env python3
"""
OPSVI Ecosystem Demo
Demonstrates basic functionality of the migrated ecosystem.
"""

import asyncio
import os
import sys

# Add libs to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "libs"))


async def demo_foundation():
    """Demo foundation components."""
    print("=== Foundation Demo ===")
    try:
        from opsvi_foundation import BaseComponent

        class DemoComponent(BaseComponent):
            async def _initialize_impl(self):
                print("  ✅ Demo component initialized")

            async def _shutdown_impl(self):
                print("  ✅ Demo component shutdown")

            async def _health_check_impl(self):
                return True

        component = DemoComponent("demo")
        await component.initialize()
        health = await component.health_check()
        await component.shutdown()
        print(f"  ✅ Health check: {health}")
        return True
    except Exception as e:
        print(f"  ❌ Foundation demo failed: {e}")
        return False


async def demo_core():
    """Demo core services."""
    print("=== Core Services Demo ===")
    try:
        from opsvi_core import EventBus, ServiceRegistry, StateManager

        registry = ServiceRegistry("demo-registry")
        event_bus = EventBus("demo-events")
        state_manager = StateManager("demo-state")

        await registry.initialize()
        await event_bus.initialize()
        await state_manager.initialize()

        print("  ✅ Core services initialized")

        await registry.shutdown()
        await event_bus.shutdown()
        await state_manager.shutdown()
        return True
    except Exception as e:
        print(f"  ❌ Core demo failed: {e}")
        return False


async def demo_llm():
    """Demo LLM services."""
    print("=== LLM Services Demo ===")
    try:
        from opsvi_llm.providers.base import LLMConfig

        config = LLMConfig(provider="openai")
        print(f"  ✅ LLM config created: {config.provider}")
        return True
    except Exception as e:
        print(f"  ❌ LLM demo failed: {e}")
        return False


async def demo_http():
    """Demo HTTP services."""
    print("=== HTTP Services Demo ===")
    try:
        from opsvi_http.client.base import HTTPConfig

        config = HTTPConfig(timeout=30)
        print(f"  ✅ HTTP config created: timeout={config.timeout}")
        return True
    except Exception as e:
        print(f"  ❌ HTTP demo failed: {e}")
        return False


async def demo_data():
    """Demo data services."""
    print("=== Data Services Demo ===")
    try:
        from opsvi_data.providers.base import DataConfig

        config = DataConfig(database_type="postgresql")
        print(f"  ✅ Data config created: {config.database_type}")
        return True
    except Exception as e:
        print(f"  ❌ Data demo failed: {e}")
        return False


async def demo_auth():
    """Demo auth services."""
    print("=== Auth Services Demo ===")
    try:
        from opsvi_auth.providers.base import AuthConfig

        config = AuthConfig(auth_type="jwt")
        print(f"  ✅ Auth config created: {config.auth_type}")
        return True
    except Exception as e:
        print(f"  ❌ Auth demo failed: {e}")
        return False


async def main():
    """Run all demos."""
    print("🚀 OPSVI Ecosystem Demo")
    print("=" * 50)

    demos = [
        demo_foundation(),
        demo_core(),
        demo_llm(),
        demo_http(),
        demo_data(),
        demo_auth(),
    ]

    results = await asyncio.gather(*demos, return_exceptions=True)

    print("\n" + "=" * 50)
    print("📊 Demo Results:")

    success_count = sum(1 for r in results if r is True)
    total_count = len(results)

    for i, result in enumerate(results):
        status = "✅ PASS" if result is True else "❌ FAIL"
        demo_names = ["Foundation", "Core", "LLM", "HTTP", "Data", "Auth"]
        print(f"  {demo_names[i]}: {status}")

    print(f"\n🎯 Overall: {success_count}/{total_count} demos passed")

    if success_count == total_count:
        print("🎉 All demos passed! Ecosystem is ready for use.")
    else:
        print("⚠️  Some demos failed. Check import issues.")


if __name__ == "__main__":
    asyncio.run(main())
