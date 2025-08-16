"""
test_resume_workflow.py

This script tests the workflow resume feature of the ASEA Orchestrator.

Test Objective:
Verify that an interrupted workflow can be successfully resumed from its last
checkpoint and run to completion.
"""

import asyncio
import os
import sys
from pathlib import Path
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.database import ArangoDBClient

# --- ArangoDB Test Setup ---
ARANGO_HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "arango_dev_password")
DB_NAME = "asea_prod_db"
COLLECTION_NAME = "workflow_states"


def get_db_client():
    """Get database client with correct configuration."""
    return ArangoDBClient(
        host=os.getenv("ARANGO_HOST", "http://localhost:8529"),
        database=os.getenv("ARANGO_DB_NAME", "asea_prod_db"),
        username=os.getenv("ARANGO_USER", "root"),
        password=os.getenv("ARANGO_PASSWORD", "arango_dev_password"),
    )


async def setup_test_db():
    """Ensures the test database and collection exist in ArangoDB."""
    db_client = get_db_client()
    await db_client.connect()

    # Ensure collection exists
    has_collection_job = db_client.async_db.has_collection(COLLECTION_NAME)
    while has_collection_job.status() != "done":
        await asyncio.sleep(0.01)

    if not has_collection_job.result():
        create_job = db_client.async_db.create_collection(COLLECTION_NAME)
        while create_job.status() != "done":
            await asyncio.sleep(0.01)
        create_job.result()

    return db_client


# --- Workflow & Plugin Definitions ---
WORKFLOW_DEFS = {
    "resume_test_workflow": {
        "steps": [
            {
                "plugin_name": "to_upper",
                "inputs": {"text_to_transform": "initial_text"},
                "outputs": {"transformed_text": "step1_output"},
            },
            {
                "plugin_name": "pause_for_input",
                "parameters": {"message": "Pausing workflow for resume test."},
            },
            {
                "plugin_name": "logging",
                "parameters": {
                    "message": "Step 3 logging a value from step 1.",
                    "log_value_from_key": "step1_output",
                },
            },
        ]
    }
}


async def main():
    """Main function to run the resume test."""
    print("--- Starting Workflow Resume Test ---")
    run_id = str(uuid.uuid4())
    print(f"Using Run ID: {run_id}")

    # 1. Ensure the DB collection for workflow runs exists
    db = await setup_test_db()

    # 2. Initialize Orchestrator for the FIRST run
    print("\n--- Part 1: Running workflow until interruption ---")
    workflow_manager = WorkflowManager(WORKFLOW_DEFS)
    orchestrator1 = Orchestrator(workflow_manager=workflow_manager)

    # 3. Run the workflow until the 'pause_for_input' plugin interrupts it
    initial_state = {"initial_text": "hello resume world"}

    try:
        await orchestrator1.run_workflow(
            "resume_test_workflow", initial_state, run_id=run_id
        )
    except Exception as e:
        # We expect an exception from the pause plugin
        print(f"Workflow paused as expected: {e}")

    # 4. Verify the intermediate state in ArangoDB
    print("\n--- Verifying Interrupted State in ArangoDB ---")
    try:
        get_job = db.async_db.collection(COLLECTION_NAME).get(run_id)
        while get_job.status() != "done":
            await asyncio.sleep(0.01)
        persisted_doc = get_job.result()

        assert persisted_doc, f"Could not find document for run_id '{run_id}'"
        print("Successfully fetched persisted document for interrupted run.")
        assert (
            persisted_doc["status"] == "PAUSED"
        ), f"Expected status PAUSED, got {persisted_doc['status']}"
        assert (
            persisted_doc["current_step_index"] == 1
        ), f"Expected step index 1, got {persisted_doc['current_step_index']}"
        print("Intermediate state verification PASSED.")
    except Exception as e:
        print(f"Error verifying intermediate state: {e}")
        raise

    # 5. Initialize a NEW Orchestrator to simulate a resume scenario
    print("\n--- Part 2: Resuming workflow from checkpoint ---")
    orchestrator2 = Orchestrator(workflow_manager=workflow_manager)

    # 6. Resume the workflow
    # The 'pause_for_input' plugin will be skipped on resume
    await orchestrator2.run_workflow("resume_test_workflow", {}, run_id=run_id)

    # 7. Verify the final state in ArangoDB
    print("\n--- Verifying Final State in ArangoDB after Resume ---")
    try:
        final_get_job = db.async_db.collection(COLLECTION_NAME).get(run_id)
        while final_get_job.status() != "done":
            await asyncio.sleep(0.01)
        final_doc = final_get_job.result()

        assert final_doc, f"Could not find document for run_id '{run_id}'"
        print("Successfully fetched persisted document for final run.")
        assert (
            final_doc["status"] == "COMPLETED"
        ), f"Expected status COMPLETED, got {final_doc['status']}"
        assert (
            final_doc["current_step_index"] == 2
        ), f"Expected final step index 2, got {final_doc['current_step_index']}"

        final_persisted_state = final_doc["state"]
        expected_step1_output = "HELLO RESUME WORLD"
        assert (
            final_persisted_state.get("step1_output") == expected_step1_output
        ), "Incorrect value for 'step1_output' in final persisted state."

        print("Final state verification PASSED.")
        print("\n--- Test Finished Successfully ---")
    except Exception as e:
        print(f"Error verifying final state: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
