#!/usr/bin/env python3
"""
Test script for the new ACCF Agents package structure.
"""

import asyncio
import sys
from typing import Dict, Any

# Test imports
try:
    from accf_agents import Settings, AgentOrchestrator
    from accf_agents.agents import Task, Result, BaseAgent
    from accf_agents.utils.logging import setup_logging

    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test settings
try:
    settings = Settings()
    print("✅ Settings created successfully")
except Exception as e:
    print(f"❌ Settings creation failed: {e}")
    sys.exit(1)


# Test orchestrator
async def test_orchestrator():
    try:
        orchestrator = AgentOrchestrator(settings)
        print("✅ Orchestrator created successfully")

        # Test agent status
        status = orchestrator.get_agent_status()
        print(f"✅ Agent status: {status['total_agents']} agents")

        return True
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        return False


# Test task creation
def test_task_creation():
    try:
        task = Task(id="test-task-1", type="test", parameters={"test": "data"})
        print("✅ Task creation successful")
        return True
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        return False


# Test result creation
def test_result_creation():
    try:
        result = Result(
            task_id="test-task-1", status="success", data={"result": "test"}
        )
        print("✅ Result creation successful")
        return True
    except Exception as e:
        print(f"❌ Result creation failed: {e}")
        return False


async def main():
    print("🧪 Testing ACCF Agents package structure...")
    print("=" * 50)

    # Run tests
    tests = [
        ("Task Creation", test_task_creation),
        ("Result Creation", test_result_creation),
        ("Orchestrator", test_orchestrator),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! New package structure is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
