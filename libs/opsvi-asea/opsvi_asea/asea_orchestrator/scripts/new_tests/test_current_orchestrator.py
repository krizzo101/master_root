#!/usr/bin/env python3
"""
Test script for current Orchestrator API (plugin_dir + workflow_manager based)
"""
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig


def main():
    print("=== Testing Current Orchestrator API ===")

    # Use the actual plugin directory path
    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )

    print(f"Plugin directory: {plugin_dir}")
    print(f"Directory exists: {os.path.exists(plugin_dir)}")

    try:
        # Create a simple workflow definition for testing
        print("\n1. Creating WorkflowManager...")
        workflow_definitions = {
            "test_workflow": {
                "steps": [
                    {
                        "plugin_name": "hello_world",
                        "parameters": {"greeting": "Test"},
                        "inputs": {},
                        "outputs": {"message": "result_message"},
                    }
                ]
            }
        }

        workflow_manager = WorkflowManager(workflow_definitions)
        print("✓ WorkflowManager created successfully")

        # Test current constructor signature
        print("\n2. Creating Orchestrator with plugin_dir and workflow_manager...")
        orchestrator = Orchestrator(
            plugin_dir=plugin_dir, workflow_manager=workflow_manager
        )
        print("✓ Orchestrator created successfully")

        # The orchestrator should have discovered plugins during initialization
        print("\n3. Plugins discovered by orchestrator:")
        for plugin_class in orchestrator.plugin_manager.plugins:
            print(f"   - {plugin_class.get_name()} ({plugin_class.__name__})")

        print(f"Total plugins: {len(orchestrator.plugin_manager.plugins)}")

        print("\n=== Orchestrator Basic Test COMPLETED SUCCESSFULLY ===")
        return True

    except Exception as e:
        print(f"\n✗ Orchestrator test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_workflow_execution():
    """Test actual workflow execution if basic test passes"""
    print("\n=== Testing Workflow Execution ===")

    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )

    try:
        # Create workflow manager
        workflow_definitions = {
            "simple_test": {
                "steps": [
                    {
                        "plugin_name": "hello_world",
                        "parameters": {"greeting": "Workflow"},
                        "inputs": {},
                        "outputs": {"message": "workflow_result"},
                    }
                ]
            }
        }

        workflow_manager = WorkflowManager(workflow_definitions)
        orchestrator = Orchestrator(
            plugin_dir=plugin_dir, workflow_manager=workflow_manager
        )

        # Configure plugins
        hello_config = PluginConfig(
            name="hello_world_config",
            version="1.0",
            config={"greeting": "Workflow Test"},
        )

        orchestrator.temp_configure_plugins({"hello_world": hello_config})

        print("Attempting to run workflow...")

        # Note: This might fail due to Celery requirements, but let's see
        result = await orchestrator.run_workflow("simple_test", {"initial": "state"})

        print("✓ Workflow completed successfully!")
        print(f"Result: {result}")

        return True

    except Exception as e:
        print(f"✗ Workflow execution failed: {e}")
        print("(This might be expected if Celery is not running)")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run basic test first
    basic_success = main()

    if basic_success:
        print("\n" + "=" * 50)
        print("Basic test passed, attempting workflow execution...")
        workflow_success = asyncio.run(test_workflow_execution())

        if workflow_success:
            print("\n=== ALL TESTS PASSED ===")
            sys.exit(0)
        else:
            print("\n=== BASIC TEST PASSED, WORKFLOW EXECUTION FAILED ===")
            sys.exit(1)
    else:
        print("\n=== BASIC TEST FAILED ===")
        sys.exit(1)
