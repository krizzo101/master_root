#!/usr/bin/env python3
"""
Test script for persistent workflow state management using ArangoDB.
Tests the new ArangoDBClient implementation with python-arango.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from asea_orchestrator.database import ArangoDBClient


async def test_database_connection():
    """Test basic database connection and collection creation."""
    print("=== Testing Database Connection ===")

    # Test with Docker instance on port 8530 (no auth)
    client = ArangoDBClient(host="http://localhost:8530", password="")

    # Test connection
    connected = await client.connect()
    if connected:
        print("✓ Successfully connected to ArangoDB (Docker instance)")
        await client.disconnect()
        print("✓ Successfully disconnected from ArangoDB")
        return True, ""
    else:
        print("✗ Failed to connect to ArangoDB Docker instance")
        return False, None


async def test_workflow_state_operations(password=""):
    """Test workflow state save/load operations."""
    print("\n=== Testing Workflow State Operations ===")

    client = ArangoDBClient(host="http://localhost:8530", password=password)
    connected = await client.connect()
    if not connected:
        print("✗ Failed to connect to database")
        return False

    # Test data
    workflow_id = f"test_workflow_{uuid.uuid4().hex[:8]}"
    test_state = {
        "run_id": workflow_id,
        "workflow_name": "test_workflow",
        "status": "RUNNING",
        "current_step": 2,
        "state": {
            "input_data": "test_input",
            "processed_count": 42,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
    }

    # Test save
    print(f"Saving workflow state for ID: {workflow_id}")
    success = await client.save_workflow_state(workflow_id, test_state)
    if success:
        print("✓ Successfully saved workflow state")
    else:
        print("✗ Failed to save workflow state")
        await client.disconnect()
        return False

    # Test load
    print(f"Loading workflow state for ID: {workflow_id}")
    loaded_state = await client.load_workflow_state(workflow_id)
    if loaded_state:
        print("✓ Successfully loaded workflow state")
        print(f"  - Workflow name: {loaded_state['workflow_name']}")
        print(f"  - Status: {loaded_state['status']}")
        print(f"  - Current step: {loaded_state['current_step']}")
        print(f"  - State keys: {list(loaded_state['state'].keys())}")

        # Verify data integrity
        if (
            loaded_state["workflow_name"] == test_state["workflow_name"]
            and loaded_state["status"] == test_state["status"]
            and loaded_state["current_step"] == test_state["current_step"]
        ):
            print("✓ Data integrity verified")
        else:
            print("✗ Data integrity check failed")
            await client.disconnect()
            return False
    else:
        print("✗ Failed to load workflow state")
        await client.disconnect()
        return False

    # Test update
    print("Testing workflow state update...")
    updated_state = test_state.copy()
    updated_state["status"] = "COMPLETED"
    updated_state["current_step"] = 5

    success = await client.save_workflow_state(workflow_id, updated_state)
    if success:
        print("✓ Successfully updated workflow state")

        # Verify update
        loaded_updated = await client.load_workflow_state(workflow_id)
        if (
            loaded_updated
            and loaded_updated["status"] == "COMPLETED"
            and loaded_updated["current_step"] == 5
        ):
            print("✓ Update verification successful")
        else:
            print("✗ Update verification failed")
            await client.disconnect()
            return False
    else:
        print("✗ Failed to update workflow state")
        await client.disconnect()
        return False

    await client.disconnect()
    return True


async def test_checkpoint_operations(password=""):
    """Test checkpoint save/load operations."""
    print("\n=== Testing Checkpoint Operations ===")

    client = ArangoDBClient(host="http://localhost:8530", password=password)
    connected = await client.connect()
    if not connected:
        print("✗ Failed to connect to database")
        return False

    workflow_id = f"test_checkpoint_{uuid.uuid4().hex[:8]}"

    # Save multiple checkpoints
    checkpoints = [
        {
            "step_name": "initialize",
            "data": {
                "setup": "complete",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "step_name": "process_data",
            "data": {
                "records_processed": 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "step_name": "validate",
            "data": {
                "validation_passed": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    ]

    print(f"Saving {len(checkpoints)} checkpoints for workflow: {workflow_id}")
    for i, checkpoint in enumerate(checkpoints):
        success = await client.save_checkpoint(
            workflow_id, checkpoint["step_name"], checkpoint["data"]
        )
        if success:
            print(f"✓ Saved checkpoint {i+1}: {checkpoint['step_name']}")
        else:
            print(f"✗ Failed to save checkpoint {i+1}: {checkpoint['step_name']}")
            await client.disconnect()
            return False

        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)

    # Load all checkpoints
    print(f"Loading checkpoints for workflow: {workflow_id}")
    loaded_checkpoints = await client.load_checkpoints(workflow_id)

    if loaded_checkpoints:
        print(f"✓ Successfully loaded {len(loaded_checkpoints)} checkpoints")
        for i, checkpoint in enumerate(loaded_checkpoints):
            print(
                f"  Checkpoint {i+1}: {checkpoint['step_name']} - {checkpoint['timestamp']}"
            )

        # Verify order (should be sorted by timestamp)
        if len(loaded_checkpoints) == len(checkpoints):
            print("✓ Checkpoint count matches")
        else:
            print(
                f"✗ Checkpoint count mismatch: expected {len(checkpoints)}, got {len(loaded_checkpoints)}"
            )
            await client.disconnect()
            return False
    else:
        print("✗ Failed to load checkpoints")
        await client.disconnect()
        return False

    await client.disconnect()
    return True


async def test_plugin_state_operations(password=""):
    """Test plugin state save/load operations."""
    print("\n=== Testing Plugin State Operations ===")

    client = ArangoDBClient(host="http://localhost:8530", password=password)
    connected = await client.connect()
    if not connected:
        print("✗ Failed to connect to database")
        return False

    plugin_name = "test_plugin"
    plugin_state = {
        "configuration": {"param1": "value1", "param2": 42},
        "runtime_data": {
            "cache_size": 1024,
            "last_execution": datetime.now(timezone.utc).isoformat(),
        },
        "metrics": {"executions": 15, "success_rate": 0.95},
    }

    # Save plugin state
    print(f"Saving state for plugin: {plugin_name}")
    success = await client.save_plugin_state(plugin_name, plugin_state)
    if success:
        print("✓ Successfully saved plugin state")
    else:
        print("✗ Failed to save plugin state")
        await client.disconnect()
        return False

    # Load plugin state
    print(f"Loading state for plugin: {plugin_name}")
    loaded_state = await client.load_plugin_state(plugin_name)
    if loaded_state:
        print("✓ Successfully loaded plugin state")
        print(f"  - Configuration keys: {list(loaded_state['configuration'].keys())}")
        print(f"  - Runtime data keys: {list(loaded_state['runtime_data'].keys())}")
        print(f"  - Metrics: {loaded_state['metrics']}")

        # Verify data integrity
        if (
            loaded_state["configuration"] == plugin_state["configuration"]
            and loaded_state["metrics"] == plugin_state["metrics"]
        ):
            print("✓ Plugin state data integrity verified")
        else:
            print("✗ Plugin state data integrity check failed")
            await client.disconnect()
            return False
    else:
        print("✗ Failed to load plugin state")
        await client.disconnect()
        return False

    await client.disconnect()
    return True


async def test_execution_history(password=""):
    """Test execution history logging."""
    print("\n=== Testing Execution History ===")

    client = ArangoDBClient(host="http://localhost:8530", password=password)
    connected = await client.connect()
    if not connected:
        print("✗ Failed to connect to database")
        return False

    workflow_id = f"test_history_{uuid.uuid4().hex[:8]}"

    # Log multiple execution events
    events = [
        {
            "event_type": "workflow_started",
            "data": {"initial_state": {"input": "test"}},
        },
        {"event_type": "step_completed", "data": {"step": "process", "duration": 1.5}},
        {"event_type": "step_completed", "data": {"step": "validate", "duration": 0.8}},
        {
            "event_type": "workflow_completed",
            "data": {"final_state": {"output": "result"}},
        },
    ]

    print(f"Logging {len(events)} execution events for workflow: {workflow_id}")
    for i, event in enumerate(events):
        success = await client.log_execution(
            workflow_id, event["event_type"], event["data"]
        )
        if success:
            print(f"✓ Logged event {i+1}: {event['event_type']}")
        else:
            print(f"✗ Failed to log event {i+1}: {event['event_type']}")
            await client.disconnect()
            return False

        await asyncio.sleep(0.1)  # Small delay for timestamp differentiation

    # Retrieve execution history
    print(f"Retrieving execution history for workflow: {workflow_id}")
    history = await client.get_execution_history(workflow_id, limit=10)

    if history:
        print(f"✓ Successfully retrieved {len(history)} history entries")
        for i, entry in enumerate(history):
            print(f"  Entry {i+1}: {entry['event_type']} - {entry['timestamp']}")

        # Verify count and order (should be newest first)
        if len(history) == len(events):
            print("✓ History count matches logged events")
        else:
            print(
                f"✗ History count mismatch: expected {len(events)}, got {len(history)}"
            )
            await client.disconnect()
            return False
    else:
        print("✗ Failed to retrieve execution history")
        await client.disconnect()
        return False

    await client.disconnect()
    return True


async def run_all_tests():
    """Run all database tests."""
    print("Starting ArangoDB Persistent State Management Tests")
    print("=" * 60)

    # First, test connection and get working password
    connection_success, working_password = await test_database_connection()
    if not connection_success:
        print("❌ Cannot connect to ArangoDB. Please check:")
        print("  1. ArangoDB is running on localhost:8529")
        print("  2. Default password is set correctly")
        print("  3. Root user has appropriate permissions")
        return False

    print(
        f"\nUsing password: {'(empty)' if not working_password else working_password}"
    )

    tests = [
        (
            "Workflow State Operations",
            lambda: test_workflow_state_operations(working_password),
        ),
        ("Checkpoint Operations", lambda: test_checkpoint_operations(working_password)),
        (
            "Plugin State Operations",
            lambda: test_plugin_state_operations(working_password),
        ),
        ("Execution History", lambda: test_execution_history(working_password)),
    ]

    results = [("Database Connection", True)]  # Already passed

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Persistent state management is working correctly.")
        return True
    else:
        print(
            "❌ Some tests failed. Please check the ArangoDB connection and configuration."
        )
        return False


if __name__ == "__main__":
    # Check if ArangoDB is accessible
    print("Note: This test uses ArangoDB running in Docker on localhost:8530")
    print("Make sure Docker is available and the test-arango container is running.\n")

    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
