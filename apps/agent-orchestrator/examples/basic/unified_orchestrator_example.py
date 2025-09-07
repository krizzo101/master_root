#!/usr/bin/env python3
"""
WORKING UnifiedOrchestrator Example
This is the REFERENCE EXAMPLE for all agents - copy these patterns exactly
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path - ALWAYS USE THIS PATTERN
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from src.unified.enhanced_agent_task import EnhancedAgentTask
    from src.unified.unified_orchestrator import (
        FeatureFlag,
        UnifiedConfig,
        UnifiedOrchestrator,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the agent-orchestrator directory")
    sys.exit(1)


async def basic_example():
    """Basic example - minimal configuration"""
    print("🧪 Basic UnifiedOrchestrator Example")

    # CORRECT CONFIG PATTERN - COPY THIS EXACTLY
    config = UnifiedConfig(
        output_dir=Path("example_output"),
        max_parallel=2,
        enabled_features=set(),  # No extra features
        enable_collaboration=False,
        enable_quality_gates=False,
        enable_monitoring=False,
    )

    # Create orchestrator - CORRECT PATTERN
    orchestrator = UnifiedOrchestrator(config=config)

    # Create task - CORRECT PATTERN
    task = EnhancedAgentTask(
        task_id="example_basic_task",
        task_type="general-purpose",
        prompt="Create a simple test file with timestamp and confirm it works.",
        agent_uuid="example_agent_basic",
        monitoring_enabled=False,
    )

    # Execute task
    print("Executing basic task...")
    results = await orchestrator.execute_batch([task])

    if results and results[0].get("status") == "completed":
        print("✅ Basic example successful!")
        return True
    else:
        print(f"❌ Basic example failed: {results[0] if results else 'No results'}")
        return False


async def enhanced_example():
    """Enhanced example with features enabled"""
    print("\n🚀 Enhanced UnifiedOrchestrator Example")

    # CONFIG WITH ENHANCED FEATURES - COPY THIS PATTERN
    config = UnifiedConfig(
        output_dir=Path("enhanced_example_output"),
        max_parallel=3,
        enabled_features={
            FeatureFlag.ENHANCED_METRICS,
            FeatureFlag.BACKGROUND_EXECUTION,
        },
        enable_collaboration=False,
        enable_quality_gates=False,
        enable_monitoring=True,
    )

    orchestrator = UnifiedOrchestrator(config=config)

    # Enhanced task with UUID and monitoring
    task = EnhancedAgentTask(
        task_id="example_enhanced_task",
        task_type="development-specialist",
        prompt="Create a JSON file with system info, timestamp, and UUID. Include error handling.",
        agent_uuid="example_agent_enhanced",
        monitoring_enabled=True,
    )

    print("Executing enhanced task...")
    results = await orchestrator.execute_batch([task])

    if results and results[0].get("status") == "completed":
        print("✅ Enhanced example successful!")

        # Show enhanced features working
        print("📊 Enhanced features demonstrated:")
        print("  - UUID tracking enabled")
        print("  - Monitoring enabled")
        print("  - Background execution capable")

        return True
    else:
        print(f"❌ Enhanced example failed: {results[0] if results else 'No results'}")
        return False


async def parallel_example():
    """Parallel execution example"""
    print("\n⚡ Parallel Execution Example")

    config = UnifiedConfig(
        output_dir=Path("parallel_example_output"),
        max_parallel=3,
        enabled_features={FeatureFlag.ENHANCED_METRICS},
        enable_collaboration=False,
        enable_quality_gates=False,
        enable_monitoring=True,
    )

    orchestrator = UnifiedOrchestrator(config=config)

    # Create multiple tasks for parallel execution
    tasks = [
        EnhancedAgentTask(
            task_id=f"parallel_task_{i}",
            task_type="general-purpose",
            prompt=f"Create test file {i} with unique content and timestamp.",
            agent_uuid=f"parallel_agent_{i}",
            monitoring_enabled=True,
        )
        for i in range(3)
    ]

    print("Executing 3 tasks in parallel...")
    results = await orchestrator.execute_batch(tasks)

    completed = sum(1 for r in results if r.get("status") == "completed")
    total = len(results)

    print(f"📊 Parallel execution results: {completed}/{total} completed")

    if completed == total:
        print("✅ All parallel tasks successful!")
        return True
    else:
        print("⚠️ Some parallel tasks failed")
        return False


async def main():
    """Run all examples"""
    print("🎯 UNIFIED ORCHESTRATOR EXAMPLES")
    print("=" * 50)
    print("These are REFERENCE EXAMPLES - copy these patterns exactly")
    print("=" * 50)

    examples = [
        ("Basic Example", basic_example),
        ("Enhanced Example", enhanced_example),
        ("Parallel Example", parallel_example),
    ]

    results = []
    for name, example_func in examples:
        try:
            result = await example_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 EXAMPLE RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    for name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\n🎯 OVERALL: {passed}/{len(results)} examples successful")

    if passed == len(results):
        print("🎉 All examples work - UnifiedOrchestrator is ready!")
        print("\n💡 AGENTS: Use these exact patterns in your tasks!")
    else:
        print("⚠️ Some examples failed - check the configuration")

    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
