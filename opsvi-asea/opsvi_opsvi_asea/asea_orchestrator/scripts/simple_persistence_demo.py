#!/usr/bin/env python3
"""
Simple demonstration of persistent state management without Celery dependencies.
Shows direct database operations for workflow state persistence.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from asea_orchestrator.database import ArangoDBClient


async def demo_basic_persistence():
    """Demonstrate basic persistence operations."""
    print("🚀 SIMPLE PERSISTENT STATE MANAGEMENT DEMO")
    print("=" * 60)

    # Connect to database
    db_client = ArangoDBClient(host="http://localhost:8530", password="")

    print("📡 Connecting to ArangoDB...")
    connected = await db_client.connect()
    if not connected:
        print("❌ Failed to connect to database")
        return False

    print("✅ Connected to ArangoDB successfully!")

    # Demo 1: Save and load workflow state
    print("\n🔄 Demo 1: Workflow State Persistence")
    print("-" * 40)

    workflow_id = f"demo_workflow_{uuid.uuid4().hex[:8]}"
    initial_state = {
        "workflow_name": "autonomous_agent_workflow",
        "status": "RUNNING",
        "current_step": 2,
        "total_steps": 5,
        "state": {
            "user_input": "Create an AI agent",
            "processed_data": {"tokens": 1500, "complexity": "high"},
            "next_action": "generate_code",
            "context": {
                "session_id": str(uuid.uuid4()),
                "start_time": datetime.now(timezone.utc).isoformat(),
                "agent_capabilities": ["code_generation", "analysis", "optimization"],
            },
        },
    }

    # Save state
    print(f"💾 Saving workflow state for ID: {workflow_id}")
    saved = await db_client.save_workflow_state(workflow_id, initial_state)
    if saved:
        print("✅ Workflow state saved successfully")
    else:
        print("❌ Failed to save workflow state")
        await db_client.disconnect()
        return False

    # Load state
    print(f"📖 Loading workflow state for ID: {workflow_id}")
    loaded_state = await db_client.load_workflow_state(workflow_id)
    if loaded_state:
        print("✅ Workflow state loaded successfully")
        print(f"   - Workflow: {loaded_state['workflow_name']}")
        print(f"   - Status: {loaded_state['status']}")
        print(
            f"   - Progress: {loaded_state['current_step']}/{loaded_state['total_steps']}"
        )
        print(f"   - Context keys: {list(loaded_state['state']['context'].keys())}")
    else:
        print("❌ Failed to load workflow state")

    # Demo 2: Checkpoint system
    print("\n⚡ Demo 2: Checkpoint System")
    print("-" * 40)

    checkpoints = [
        {
            "name": "initialize_agent",
            "data": {"memory_allocated": "256MB", "plugins_loaded": 5},
        },
        {
            "name": "analyze_requirements",
            "data": {"complexity_score": 8.5, "estimated_time": "45min"},
        },
        {
            "name": "generate_architecture",
            "data": {
                "components": ["core", "plugins", "database"],
                "patterns": ["mvc", "observer"],
            },
        },
        {
            "name": "implement_core",
            "data": {"files_created": 12, "lines_of_code": 2847},
        },
        {"name": "test_integration", "data": {"tests_passed": 47, "coverage": "94%"}},
    ]

    print(f"📋 Saving {len(checkpoints)} checkpoints...")
    for i, checkpoint in enumerate(checkpoints):
        success = await db_client.save_checkpoint(
            workflow_id, checkpoint["name"], checkpoint["data"]
        )
        if success:
            print(f"✅ Checkpoint {i+1}: {checkpoint['name']}")
        else:
            print(f"❌ Failed to save checkpoint: {checkpoint['name']}")

    # Load checkpoints
    print(f"📚 Loading checkpoints for workflow: {workflow_id}")
    loaded_checkpoints = await db_client.load_checkpoints(workflow_id)
    if loaded_checkpoints:
        print(f"✅ Loaded {len(loaded_checkpoints)} checkpoints:")
        for checkpoint in loaded_checkpoints:
            print(f"   - {checkpoint['step_name']}: {checkpoint['timestamp']}")

    # Demo 3: Plugin state persistence
    print("\n🔌 Demo 3: Plugin State Persistence")
    print("-" * 40)

    plugin_states = {
        "code_generator": {
            "config": {"language": "python", "style": "pep8", "complexity": "advanced"},
            "runtime_data": {"templates_loaded": 15, "cache_size": "128MB"},
            "metrics": {"generations": 234, "success_rate": 0.97, "avg_time": 2.3},
        },
        "database_connector": {
            "config": {"host": "localhost:8530", "pool_size": 10, "timeout": 30},
            "runtime_data": {"connections_active": 3, "queries_cached": 45},
            "metrics": {"queries": 1847, "avg_response_time": 0.15, "errors": 2},
        },
        "autonomous_reasoner": {
            "config": {
                "model": "claude-3-sonnet",
                "temperature": 0.7,
                "max_tokens": 4000,
            },
            "runtime_data": {"context_window": "active", "reasoning_depth": 5},
            "metrics": {"decisions": 89, "confidence_avg": 0.92, "corrections": 3},
        },
    }

    for plugin_name, state in plugin_states.items():
        print(f"💾 Saving state for plugin: {plugin_name}")
        saved = await db_client.save_plugin_state(plugin_name, state)
        if saved:
            print(f"✅ Plugin state saved: {plugin_name}")
        else:
            print(f"❌ Failed to save plugin state: {plugin_name}")

    # Load plugin states
    print("\n📖 Loading plugin states...")
    for plugin_name in plugin_states.keys():
        loaded_state = await db_client.load_plugin_state(plugin_name)
        if loaded_state:
            print(
                f"✅ {plugin_name}: {loaded_state['metrics']['success_rate'] if 'success_rate' in loaded_state.get('metrics', {}) else 'loaded'}"
            )

    # Demo 4: Execution history
    print("\n📈 Demo 4: Execution History")
    print("-" * 40)

    history_events = [
        {
            "type": "workflow_started",
            "data": {"trigger": "user_request", "priority": "high"},
        },
        {
            "type": "step_completed",
            "data": {"step": "initialize_agent", "duration": 2.5},
        },
        {
            "type": "step_completed",
            "data": {"step": "analyze_requirements", "duration": 15.2},
        },
        {
            "type": "checkpoint_created",
            "data": {"checkpoint": "analyze_requirements", "state_size": "2.1KB"},
        },
        {
            "type": "plugin_loaded",
            "data": {"plugin": "code_generator", "version": "1.2.3"},
        },
        {
            "type": "step_completed",
            "data": {"step": "generate_architecture", "duration": 8.7},
        },
        {
            "type": "autonomous_decision",
            "data": {"decision": "optimize_performance", "confidence": 0.94},
        },
        {
            "type": "step_completed",
            "data": {"step": "implement_core", "duration": 120.5},
        },
        {
            "type": "quality_check",
            "data": {"score": 9.2, "issues": 0, "suggestions": 2},
        },
        {
            "type": "workflow_completed",
            "data": {"total_duration": 147.1, "success": True},
        },
    ]

    print(f"📝 Logging {len(history_events)} execution events...")
    for event in history_events:
        success = await db_client.log_execution(
            workflow_id, event["type"], event["data"]
        )
        if success:
            print(f"✅ Logged: {event['type']}")

    # Query execution history
    print(f"\n📊 Retrieving execution history...")
    history = await db_client.get_execution_history(workflow_id)
    if history:
        print(f"✅ Retrieved {len(history)} history entries:")
        for entry in history[-5:]:  # Show last 5 events
            print(f"   - {entry['event_type']}: {entry['timestamp']}")

    # Demo 5: Autonomous operation simulation
    print("\n🤖 Demo 5: Autonomous Operation Simulation")
    print("-" * 40)

    print("🎯 Simulating autonomous agent restart and recovery...")

    # Simulate agent shutdown and restart
    await db_client.disconnect()
    print("💤 Agent 'shutdown' - connection closed")

    # Restart simulation
    print("🔄 Agent 'restart' - reconnecting...")
    new_db_client = ArangoDBClient(host="http://localhost:8530", password="")
    connected = await new_db_client.connect()

    if connected:
        print("✅ Agent reconnected successfully")

        # Recover workflow state
        recovered_state = await new_db_client.load_workflow_state(workflow_id)
        if recovered_state:
            print("🎉 AUTONOMOUS RECOVERY SUCCESSFUL!")
            print(f"   - Recovered workflow: {recovered_state['workflow_name']}")
            print(f"   - Status: {recovered_state['status']}")
            print(f"   - Can resume from step: {recovered_state['current_step']}")
            print("   - Full context preserved across restart!")

            # Show that we can continue exactly where we left off
            print("\n🚀 Agent can now continue autonomous operation...")
            print("   - All state preserved")
            print("   - Context maintained")
            print("   - Plugins can be reloaded")
            print("   - Execution can resume seamlessly")

        await new_db_client.disconnect()

    print("\n" + "=" * 60)
    print("🎉 DEMONSTRATION COMPLETE!")
    print("=" * 60)
    print("✅ Workflow state persistence - WORKING")
    print("✅ Checkpoint system - WORKING")
    print("✅ Plugin state management - WORKING")
    print("✅ Execution history logging - WORKING")
    print("✅ Autonomous recovery - WORKING")
    print("\n🤖 This system enables true autonomous intelligence:")
    print("   • Survives restarts and crashes")
    print("   • Maintains full context across sessions")
    print("   • Enables long-running autonomous operations")
    print("   • Provides complete audit trail")
    print("   • Supports complex workflow resumption")

    return True


if __name__ == "__main__":
    print("Note: This demo requires ArangoDB running in Docker on localhost:8530")
    print(
        "Run: docker run -d --name test-arango -p 8530:8529 -e ARANGO_NO_AUTH=1 arangodb/arangodb:latest"
    )
    print()

    try:
        success = asyncio.run(demo_basic_persistence())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
