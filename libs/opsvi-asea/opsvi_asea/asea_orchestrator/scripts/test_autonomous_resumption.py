#!/usr/bin/env python3
"""
DEFINITIVE TEST FOR AUTONOMOUS WORKFLOW RESUMPTION

This script provides definitive proof of the orchestrator's ability to
autonomously resume a workflow from the exact point of failure.

It runs against the OPERATIONAL database configured in the .env file.
Ensure your .env file is correctly configured with the operational ArangoDB
host, database name, user, and password.
"""

import asyncio
import sys
import os
import uuid
import traceback
import time
from pathlib import Path
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.database import ArangoDBClient
from asea_orchestrator.plugins.plugin_manager import PluginManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Absolute Path Setup ---
# Use absolute path for src directory to ensure module resolution
WORKSPACE_ROOT = "/home/opsvi/asea"
SRC_PATH = os.path.join(WORKSPACE_ROOT, "asea_orchestrator/src")
sys.path.insert(0, SRC_PATH)
# ---

# Add project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig

# --- Absolute Path for Plugins ---
PLUGIN_DIR = os.path.join(SRC_PATH, "asea_orchestrator/plugins/available")
# ---


def get_db_client():
    """Creates and returns a configured ArangoDB client."""
    return ArangoDBClient(
        host=os.getenv("ARANGO_HOST", "http://localhost:8529"),
        database=os.getenv("ARANGO_DB_NAME", "asea_prod_db"),
        username=os.getenv("ARANGO_USER", "root"),
        password=os.getenv("ARANGO_PASSWORD", "arango_dev_password"),
    )


def create_resumption_workflow_dict():
    """Creates a dict definition for the resumption workflow."""
    return {
        "resumption_test_workflow": {
            "steps": [
                {
                    "plugin_name": "hello_world",
                    "inputs": {"initial_data": "name"},
                    "outputs": {"greeting": "step1_result"},
                },
                {
                    "plugin_name": "crashable_plugin",
                    "inputs": {},
                    "outputs": {
                        "crashable_plugin_ran_at_attempt": "crashable_plugin_ran_at_attempt",
                        "crashable_attempt_count": "crashable_attempt_count",
                    },
                },
                {
                    "plugin_name": "to_upper",
                    "inputs": {"step1_result": "text"},
                    "outputs": {"result": "final_result"},
                },
            ]
        }
    }


async def wait_for_job(job):
    """Polls an AsyncJob until it is complete."""
    while job.status() != "done":
        await asyncio.sleep(0.01)
    return job.result()


async def run_definitive_test():
    """
    This is a definitive test to prove the autonomous resumption capability.
    It runs against the OPERATIONAL database defined in the .env file.
    """
    db_client = get_db_client()
    if not await db_client.connect():
        print("❌ CRITICAL FAILURE: Could not connect to the operational database.")
        print(
            "   Please check your .env configuration and ensure the database is running."
        )
        return False

    test_run_id = f"resumption-test-{uuid.uuid4().hex[:8]}"

    # Define counter file for the crashable plugin
    counter_file = f"/tmp/crashable_plugin_{test_run_id}.count"

    # --- Cleanup from previous runs ---
    print("--- 🧼 Phase 0: Cleanup ---")
    if os.path.exists(counter_file):
        os.remove(counter_file)
        print(f"✓ Removed old counter file: {counter_file}")

    # Use direct AQL for guaranteed deletion without loading the full object
    delete_job = db_client.async_db.collection("workflow_states").delete(
        test_run_id, ignore_missing=True
    )
    # Wait for the async job to complete
    while delete_job.status() != "done":
        await asyncio.sleep(0.01)
    delete_job.result()  # Get the result to ensure completion
    print(f"✓ Ensured no previous state for run_id: {test_run_id}")
    await db_client.disconnect()
    print("-" * 50)

    # --- PART 1: Simulate the initial run and crash ---
    print(f"--- ▶️ Phase 1: Initial Run & Simulated Crash (Run ID: {test_run_id}) ---")

    # Create the first orchestrator instance
    workflow_defs_1 = create_resumption_workflow_dict()
    workflow_manager_1 = WorkflowManager(workflow_definitions=workflow_defs_1)
    orchestrator_1 = Orchestrator(
        plugin_dir=PLUGIN_DIR,  # Using absolute path
        workflow_manager=workflow_manager_1,
    )
    orchestrator_1.db_client = get_db_client()

    # Correctly configure plugins, setting crashable_plugin to fail
    plugin_configs_1 = {
        "hello_world": PluginConfig(name="hello_world", config={"prefix": "Step 1:"}),
        "to_upper": PluginConfig(name="to_upper"),
        "crashable_plugin": PluginConfig(
            name="crashable_plugin",
            config={"run_id": test_run_id, "crash_on_attempt": 1},
        ),
    }
    orchestrator_1.temp_configure_plugins(plugin_configs_1)

    # Define initial state
    initial_state = {"initial_data": "Resilience Test"}

    print("🚀 Executing workflow, expecting a crash...")
    try:
        await orchestrator_1.run_workflow(
            workflow_name="resumption_test_workflow",
            initial_state=initial_state,
            run_id=test_run_id,
        )
    except RuntimeError as e:
        print(f"✅ SUCCESSFULLY caught expected crash: {e}")

    print("✓ Workflow execution correctly interrupted.")
    print("-" * 50)

    # --- PART 2: Verify the saved state ---
    print("--- 🔎 Phase 2: Verifying Persisted State ---")
    db_client = get_db_client()  # Create a new client to be sure
    await db_client.connect()

    saved_state_doc = await db_client.load_workflow_state(test_run_id)

    assert saved_state_doc is not None, "Test Failed: Workflow state was not saved."
    print("✓ Found persisted state in the database.")

    assert (
        saved_state_doc["status"] == "FAILED"
    ), f"Test Failed: Expected status FAILED, got {saved_state_doc['status']}"
    print(f"✓ Workflow status correctly marked as FAILED.")

    assert (
        saved_state_doc["current_step"] == 1
    ), f"Test Failed: Expected to fail on step 1, but last completed was {saved_state_doc['current_step']}"
    print(f"✓ Failure occurred at the correct step (step index 1).")

    persisted_state = saved_state_doc["state"]
    assert (
        persisted_state["step1_result"] == "Step 1: Resilience Test"
    ), "Test Failed: State from step 0 was not correctly saved."
    print("✓ State from completed steps was correctly persisted.")

    await db_client.disconnect()
    print("-" * 50)

    # --- PART 3: Simulate application restart and resume ---
    print("--- 🔄 Phase 3: Resuming Workflow After 'Restart' ---")

    # Create a NEW orchestrator instance to prove no in-memory state is used
    print("✨ Creating a new orchestrator instance (simulating app restart)...")
    workflow_defs_2 = create_resumption_workflow_dict()
    workflow_manager_2 = WorkflowManager(workflow_definitions=workflow_defs_2)
    orchestrator_2 = Orchestrator(
        plugin_dir=PLUGIN_DIR,  # Using absolute path
        workflow_manager=workflow_manager_2,
    )
    orchestrator_2.db_client = get_db_client()

    # Reconfigure plugins, setting crashable_plugin to succeed
    plugin_configs_2 = {
        "hello_world": PluginConfig(name="hello_world", config={"prefix": "Step 1:"}),
        "to_upper": PluginConfig(name="to_upper"),
        "crashable_plugin": PluginConfig(
            name="crashable_plugin",
            config={"run_id": test_run_id, "crash_on_attempt": -1},
        ),
    }
    orchestrator_2.temp_configure_plugins(plugin_configs_2)

    print(f"🚀 Attempting to resume workflow with run_id: {test_run_id}")

    final_state_2 = await orchestrator_2.run_workflow(
        workflow_name="resumption_test_workflow",
        initial_state={},  # This should be ignored as we are resuming
        run_id=test_run_id,
    )

    assert final_state_2 is not None, "Test Failed: Resumed workflow did not complete."
    print("✅ Workflow resumed and completed successfully!")
    print("-" * 50)

    # --- PART 4: Final Validation ---
    print("--- 🏆 Phase 4: Final State Validation ---")

    print(f"Final State: {final_state_2}")

    # 1. Check result from before the crash
    assert (
        final_state_2["step1_result"] == "Step 1: Resilience Test"
    ), "Validation Failed: State from before crash is missing."
    print("✓ State from before crash is present.")

    # 2. Check result from the resumed plugin
    assert (
        final_state_2["crashable_plugin_ran_at_attempt"] == 2
    ), "Validation Failed: Crashable plugin did not execute correctly on resumption."
    print("✓ Resumed plugin executed correctly (attempt 2).")

    # 3. Check result from after the crash
    assert (
        final_state_2["final_result"] == "STEP 1: RESILIENCE TEST"
    ), "Validation Failed: State from after crash is incorrect."
    print("✓ State from after crash is present and correct.")

    # 4. Final status check in DB
    db_client = get_db_client()
    await db_client.connect()
    final_doc = await db_client.load_workflow_state(test_run_id)
    assert (
        final_doc["status"] == "COMPLETED"
    ), "Validation Failed: Final status in DB is not COMPLETED."
    print("✓ Final workflow status in database is COMPLETED.")

    print("\n\n🎉🎉🎉 DEFINITIVE PROOF: AUTONOMOUS RESUMPTION VALIDATED! 🎉🎉🎉")
    print(
        "The system correctly saved state on failure, and a new instance resumed and completed the workflow seamlessly."
    )

    # --- Final Cleanup ---
    if os.path.exists(counter_file):
        os.remove(counter_file)

    await db_client.connect()  # Reconnect for cleanup
    delete_job = db_client.async_db.collection("workflow_states").delete(
        test_run_id, ignore_missing=True
    )
    # Wait for the async job to complete
    while delete_job.status() != "done":
        await asyncio.sleep(0.01)
    delete_job.result()  # Get the result to ensure completion
    await db_client.disconnect()

    return True


async def main():
    print("=" * 60)
    print("  Running Definitive Test for Autonomous Workflow Resumption")
    print("=" * 60)
    print(
        "NOTE: This test runs against the OPERATIONAL database defined in your .env file."
    )

    success = await run_definitive_test()

    print("=" * 60)
    if success:
        print("✅ Definitive test PASSED.")
    else:
        print("❌ Definitive test FAILED.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
