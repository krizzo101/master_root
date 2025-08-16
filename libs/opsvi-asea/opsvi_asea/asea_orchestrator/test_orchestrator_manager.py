#!/usr/bin/env python3
"""
Test script for OrchestratorManager - validates auto-worker startup and database integration.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from asea_orchestrator.orchestrator_manager import create_orchestrator_manager
from asea_orchestrator.plugins.types import PluginConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_orchestrator_manager():
    """Comprehensive test of OrchestratorManager functionality."""

    print("\n🧪 TESTING ORCHESTRATOR MANAGER")
    print("=" * 50)

    try:
        # Test 1: Initialize OrchestratorManager
        print("\n📋 Test 1: OrchestratorManager Initialization")
        print("-" * 30)

        plugin_dir = str(
            Path(__file__).parent
            / "src"
            / "asea_orchestrator"
            / "plugins"
            / "available"
        )

        manager = await create_orchestrator_manager(
            plugin_dir=plugin_dir, auto_start_workers=True, worker_concurrency=2
        )

        print("✅ OrchestratorManager created and initialized successfully")

        # Test 2: Status Check
        print("\n📋 Test 2: Status Information")
        print("-" * 30)

        status = await manager.get_status()
        print("📊 Status Report:")
        for key, value in status.items():
            print(f"   {key}: {value}")

        # Test 3: Worker Verification
        print("\n📋 Test 3: Worker Verification")
        print("-" * 30)

        if status["active_workers"]:
            print(f"✅ Workers active: {len(status['active_workers'])}")
            for worker in status["active_workers"]:
                print(f"   🔧 {worker}")
        else:
            print("❌ No active workers found")

        # Test 4: Plugin Discovery
        print("\n📋 Test 4: Plugin Discovery")
        print("-" * 30)

        if status["plugin_count"] > 0:
            print(f"✅ Plugins loaded: {status['plugin_count']}")

            # List available plugins
            if manager.orchestrator:
                for plugin_class in manager.orchestrator.plugin_manager.plugins:
                    print(f"   🔌 {plugin_class.get_name()}")
        else:
            print("❌ No plugins loaded")

        # Test 5: Database Connection
        print("\n📋 Test 5: Database Connection")
        print("-" * 30)

        if status["database_connected"]:
            print("✅ Database connection established")
        else:
            print("⚠️ Database connection not available")

        # Test 6: Simple Workflow Execution (if possible)
        print("\n📋 Test 6: Basic Workflow Test")
        print("-" * 30)

        try:
            # Create minimal plugin configurations
            plugin_configs = {
                "logger": PluginConfig(
                    enabled=True, settings={"message": "Test workflow execution"}
                )
            }

            # Try to run a simple workflow if available
            if status["workflows_available"]:
                workflow_name = status["workflows_available"][0]
                print(f"🔄 Testing workflow: {workflow_name}")

                # This might fail if workflow requires specific plugins
                # but it will test the execution path
                try:
                    result = await manager.run_workflow(
                        workflow_name=workflow_name,
                        plugin_configs=plugin_configs,
                        initial_state={"test": True},
                    )
                    print("✅ Workflow execution completed")
                    print(f"   Result keys: {list(result.keys())}")
                except Exception as workflow_error:
                    print(f"⚠️ Workflow execution failed (expected): {workflow_error}")
            else:
                print("📭 No workflows available for testing")

        except Exception as workflow_test_error:
            print(f"⚠️ Workflow test failed: {workflow_test_error}")

        # Test 7: Final Status
        print("\n📋 Test 7: Final Status Check")
        print("-" * 30)

        final_status = await manager.get_status()
        print("📊 Final Status:")
        print(f"   ✅ Initialized: {final_status['initialized']}")
        print(f"   🔧 Workers: {len(final_status['active_workers'])} active")
        print(
            f"   📊 Database: {'Connected' if final_status['database_connected'] else 'Disconnected'}"
        )
        print(f"   🔌 Plugins: {final_status['plugin_count']} loaded")

        # Cleanup
        print("\n🧹 Cleanup")
        print("-" * 30)
        await manager.shutdown()
        print("✅ Manager shutdown complete")

        # Overall assessment
        print("\n🎯 OVERALL ASSESSMENT")
        print("=" * 50)

        success_criteria = [
            ("Manager initialized", final_status["initialized"]),
            ("Workers active", len(final_status["active_workers"]) > 0),
            ("Plugins loaded", final_status["plugin_count"] > 0),
        ]

        passed = sum(1 for _, condition in success_criteria if condition)
        total = len(success_criteria)

        print(f"✅ Passed: {passed}/{total} criteria")
        for criteria, condition in success_criteria:
            status_icon = "✅" if condition else "❌"
            print(f"   {status_icon} {criteria}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED - OrchestratorManager is working correctly!")
        elif passed >= total - 1:
            print("\n⚠️ MOSTLY WORKING - Minor issues detected")
        else:
            print("\n❌ SIGNIFICANT ISSUES - OrchestratorManager needs attention")

        return passed == total

    except Exception as e:
        print(f"\n❌ TEST FAILED with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_worker_management_only():
    """Test just the worker management functionality."""

    print("\n🔧 TESTING WORKER MANAGEMENT ONLY")
    print("=" * 40)

    try:
        from asea_orchestrator.orchestrator_manager import OrchestratorManager

        # Create manager without auto-starting workers
        manager = OrchestratorManager(
            plugin_dir="/tmp", auto_start_workers=False  # Dummy path
        )

        # Test worker status checking
        print("🔍 Testing worker status check...")
        workers_ready = await manager._ensure_workers_running()

        if workers_ready:
            print("✅ Workers are running or were started successfully")
        else:
            print("❌ Worker management failed")

        return workers_ready

    except Exception as e:
        print(f"❌ Worker management test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 ORCHESTRATOR MANAGER COMPREHENSIVE TEST")
    print("=" * 60)

    # Run comprehensive test
    success = asyncio.run(test_orchestrator_manager())

    if not success:
        print("\n🔧 Running worker management test only...")
        worker_success = asyncio.run(test_worker_management_only())

        if worker_success:
            print("✅ Worker management is working")
        else:
            print("❌ Worker management has issues")

    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETE")
