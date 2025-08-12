#!/usr/bin/env python3
"""
Demonstration of persistent workflow state management.
Shows how workflows can be paused, resumed, and survive restarts.
"""

import asyncio
import sys
import os
import uuid

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager, Workflow, WorkflowStep
from asea_orchestrator.plugins.types import PluginConfig
from asea_orchestrator.database import ArangoDBClient


def create_demo_workflow():
    """Create a demo workflow for testing persistence."""
    steps = [
        WorkflowStep(
            plugin_name="hello_world",
            inputs={"name": "user_name"},
            outputs={"greeting": "greeting_result"},
            parameters={"prefix": "Hello"},
        ),
        WorkflowStep(
            plugin_name="to_upper",
            inputs={"text": "greeting_result"},
            outputs={"result": "upper_greeting"},
            parameters={},
        ),
        WorkflowStep(
            plugin_name="hello_world",
            inputs={"name": "upper_greeting"},
            outputs={"final_message": "final_result"},
            parameters={"prefix": "Final:"},
        ),
    ]

    return Workflow(
        name="demo_persistent_workflow",
        description="Demo workflow to test persistence",
        steps=steps,
    )


async def demo_workflow_execution():
    """Demonstrate workflow execution with persistence."""
    print("🚀 Starting Persistent Workflow Demonstration")
    print("=" * 60)

    # Initialize components
    workflow_manager = WorkflowManager()
    orchestrator = Orchestrator(
        plugin_dir="asea_orchestrator/src/asea_orchestrator/plugins/available",
        workflow_manager=workflow_manager,
    )

    # Update database connection to use Docker instance
    orchestrator.db_client = ArangoDBClient(host="http://localhost:8530", password="")

    # Add demo workflow
    demo_workflow = create_demo_workflow()
    workflow_manager.add_workflow(demo_workflow)

    # Configure plugins
    plugin_configs = {
        "hello_world": PluginConfig(name="hello_world", enabled=True, config={}),
        "to_upper": PluginConfig(name="to_upper", enabled=True, config={}),
    }
    orchestrator.temp_configure_plugins(plugin_configs)

    print("✓ Orchestrator initialized")
    print("✓ Demo workflow added")
    print("✓ Plugins configured")

    # Initial state
    initial_state = {"user_name": "Autonomous Agent", "session_id": str(uuid.uuid4())}

    print(f"\n📝 Initial state: {initial_state}")

    # Execute workflow
    print("\n🎯 Executing workflow...")
    try:
        result = await orchestrator.run_workflow(
            workflow_name="demo_persistent_workflow", initial_state=initial_state
        )

        print("\n✅ Workflow completed successfully!")
        print(f"Final result: {result}")

        return result.get("run_id")

    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")
        return None


async def demo_workflow_resumption(run_id: str):
    """Demonstrate workflow resumption from saved state."""
    print("\n🔄 Demonstrating Workflow Resumption")
    print("=" * 60)

    # Create new orchestrator instance (simulating restart)
    workflow_manager = WorkflowManager()
    orchestrator = Orchestrator(
        plugin_dir="asea_orchestrator/src/asea_orchestrator/plugins/available",
        workflow_manager=workflow_manager,
    )

    # Update database connection
    orchestrator.db_client = ArangoDBClient(host="http://localhost:8530", password="")

    # Add demo workflow again
    demo_workflow = create_demo_workflow()
    workflow_manager.add_workflow(demo_workflow)

    # Configure plugins
    plugin_configs = {
        "hello_world": PluginConfig(name="hello_world", enabled=True, config={}),
        "to_upper": PluginConfig(name="to_upper", enabled=True, config={}),
    }
    orchestrator.temp_configure_plugins(plugin_configs)

    print("✓ New orchestrator instance created (simulating restart)")

    # Try to resume workflow
    print(f"\n🔍 Attempting to resume workflow with run_id: {run_id}")

    try:
        # Load the saved state
        saved_state = await orchestrator.db_client.load_workflow_state(run_id)
        if saved_state:
            print("✓ Found saved state:")
            print(f"  - Workflow: {saved_state['workflow_name']}")
            print(f"  - Status: {saved_state['status']}")
            print(f"  - Current step: {saved_state['current_step']}")
            print(f"  - State keys: {list(saved_state['state'].keys())}")

            # Resume execution (this would continue from where it left off)
            print("\n🎯 Resuming workflow execution...")
            result = await orchestrator.run_workflow(
                workflow_name="demo_persistent_workflow",
                initial_state={},  # Will be ignored since we're resuming
                run_id=run_id,
            )

            print("\n✅ Workflow resumption completed!")
            print(f"Final result: {result}")

        else:
            print(f"❌ No saved state found for run_id: {run_id}")

    except Exception as e:
        print(f"❌ Workflow resumption failed: {e}")


async def demo_state_inspection():
    """Demonstrate inspection of saved workflow states."""
    print("\n🔍 Demonstrating State Inspection")
    print("=" * 60)

    # Connect to database
    db_client = ArangoDBClient(host="http://localhost:8530", password="")
    await db_client.connect()

    print("✓ Connected to database")

    # Query all workflow states
    try:
        # Use AQL to get all workflow states
        job = db_client.async_db.aql.execute(
            "FOR doc IN workflow_states SORT doc.timestamp DESC LIMIT 10 RETURN doc"
        )

        while job.status() != "done":
            await asyncio.sleep(0.01)

        cursor = job.result()
        states = list(cursor)

        if states:
            print(f"\n📊 Found {len(states)} saved workflow states:")
            for i, state in enumerate(states):
                print(f"\n  {i+1}. Run ID: {state['_key']}")
                print(f"     Workflow: {state['state']['workflow_name']}")
                print(f"     Status: {state['state']['status']}")
                print(f"     Step: {state['state']['current_step']}")
                print(f"     Timestamp: {state['timestamp']}")
        else:
            print("📊 No saved workflow states found")

        # Query checkpoints
        job = db_client.async_db.aql.execute(
            "FOR doc IN workflow_checkpoints SORT doc.timestamp DESC LIMIT 5 RETURN doc"
        )

        while job.status() != "done":
            await asyncio.sleep(0.01)

        cursor = job.result()
        checkpoints = list(cursor)

        if checkpoints:
            print("\n📋 Recent checkpoints:")
            for checkpoint in checkpoints:
                print(
                    f"  - {checkpoint['workflow_id']}: {checkpoint['step_name']} ({checkpoint['timestamp']})"
                )

        # Query execution history
        job = db_client.async_db.aql.execute(
            "FOR doc IN execution_history SORT doc.timestamp DESC LIMIT 5 RETURN doc"
        )

        while job.status() != "done":
            await asyncio.sleep(0.01)

        cursor = job.result()
        history = list(cursor)

        if history:
            print("\n📈 Recent execution events:")
            for event in history:
                print(
                    f"  - {event['workflow_id']}: {event['event_type']} ({event['timestamp']})"
                )

    except Exception as e:
        print(f"❌ State inspection failed: {e}")

    await db_client.disconnect()


async def run_full_demo():
    """Run the complete demonstration."""
    print("🎭 PERSISTENT WORKFLOW STATE MANAGEMENT DEMONSTRATION")
    print("=" * 80)
    print("This demo shows how workflows can survive restarts and resume execution")
    print("from exactly where they left off, enabling true autonomous resilience.")
    print("=" * 80)

    # Part 1: Execute a workflow
    run_id = await demo_workflow_execution()

    if run_id:
        # Part 2: Simulate restart and resumption
        await demo_workflow_resumption(run_id)

        # Part 3: Inspect saved states
        await demo_state_inspection()

        print("\n" + "=" * 80)
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 80)
        print("Key features demonstrated:")
        print("✅ Workflow execution with automatic state persistence")
        print("✅ Checkpoint creation at each step")
        print("✅ Workflow resumption after 'restart'")
        print("✅ State inspection and audit trail")
        print("✅ Complete autonomous operation continuity")
        print("\nThis enables agents to maintain context across restarts,")
        print("providing true autonomous resilience and long-running operations.")

    else:
        print("\n❌ Demo failed - workflow execution unsuccessful")


if __name__ == "__main__":
    print("Note: This demo requires ArangoDB running in Docker on localhost:8530")
    print(
        "Run: docker run -d --name test-arango -p 8530:8529 -e ARANGO_NO_AUTH=1 arangodb/arangodb:latest"
    )
    print()

    try:
        asyncio.run(run_full_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
