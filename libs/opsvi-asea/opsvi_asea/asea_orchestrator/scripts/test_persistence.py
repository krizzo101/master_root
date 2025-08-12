"""
test_persistence.py

This script tests the workflow persistence feature of the ASEA Orchestrator.

Test Objective:
Verify that after a complete and successful workflow execution, the final state
is correctly persisted to the ArangoDB `workflow_runs` collection with a
'COMPLETED' status.
"""

import asyncio
import os
import sys
from pathlib import Path
from arango import ArangoClient
from dotenv import load_dotenv

# Add project root to the Python path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig
from asea_orchestrator.database import ArangoDBClient

# --- Configuration ---
HOST = os.getenv("ARANGO_HOST", "http://localhost:8529")
USER = os.getenv("ARANGO_USER", "root")
PASSWORD = os.getenv("ARANGO_PASSWORD", "arango_dev_password")
DB_NAME = "asea_prod_db"
# --- End Configuration ---


def setup_test_collection():
    """Ensures the test collection exists in ArangoDB."""
    try:
        client = ArangoClient(hosts=HOST)
        db = client.db(DB_NAME, username=USER, password=PASSWORD)
        if not db.has_collection("workflow_states"):
            print(f"Creating test collection: 'workflow_states'...")
            db.create_collection("workflow_states")
        else:
            print(f"Test collection 'workflow_states' already exists.")
    except Exception as e:
        print(f"!! Failed to set up ArangoDB collection: {e}")
        print("!! Please ensure ArangoDB is running and credentials are correct.")
        sys.exit(1)


# --- Workflow & Plugin Definitions ---
WORKFLOW_DEFS = {
    "persistence_test_workflow": {
        "steps": [
            {
                "plugin_name": "to_upper",
                "inputs": {"text": "initial_text"},
                "outputs": {"result": "step1_output"},
            },
            {
                "plugin_name": "logger",
                "parameters": {
                    "message": "Step 2 logging a value from step 1.",
                    "log_value_from_key": "step1_output",
                },
            },
        ]
    }
}

PLUGIN_CONFIGS: dict[str, PluginConfig] = {
    "arango_db": PluginConfig(
        name="arango_db",
        config={
            "host": HOST,
            "db_name": DB_NAME,
            "username": USER,
            "password": PASSWORD,
        },
    ),
    "logger": PluginConfig(name="logger"),
    "to_upper": PluginConfig(name="to_upper"),
}

PLUGIN_DIR = str(
    Path(__file__).resolve().parents[1]
    / "src"
    / "asea_orchestrator"
    / "plugins"
    / "available"
)


async def main():
    """Main function to run the persistence test."""
    print("--- Starting Workflow Persistence Test ---")

    # 1. Ensure the DB collection for workflow runs exists
    setup_test_collection()

    # 2. Initialize Orchestrator with database client
    workflow_manager = WorkflowManager(WORKFLOW_DEFS)
    orchestrator = Orchestrator(PLUGIN_DIR, workflow_manager)
    orchestrator.temp_configure_plugins(PLUGIN_CONFIGS)

    # 3. Initialize database client for persistence
    db_client = ArangoDBClient(
        host=HOST, database=DB_NAME, username=USER, password=PASSWORD
    )
    orchestrator.db_client = db_client

    # 4. Run the workflow
    initial_state = {"initial_text": "hello persistent world"}
    final_state = await orchestrator.run_workflow(
        "persistence_test_workflow", initial_state
    )

    run_id = final_state.get("run_id")
    assert run_id, "run_id was not found in the final state!"
    print(f"\nWorkflow completed with Run ID: {run_id}")

    # 5. Verify persisted state directly from ArangoDB
    print("\n--- Verifying Persisted State in ArangoDB ---")
    try:
        client = ArangoClient(hosts=HOST)
        db = client.db(DB_NAME, username=USER, password=PASSWORD)
        runs_collection = db.collection("workflow_states")

        persisted_doc = runs_collection.get(run_id)

        assert persisted_doc, f"Could not find document for run_id '{run_id}'"
        print("Successfully fetched persisted document.")

        # 6. Assertions
        print("Running assertions on persisted data...")

        # The database saves the WorkflowState as nested data
        saved_state = persisted_doc["state"]

        assert (
            saved_state["status"] == "COMPLETED"
        ), f"Expected status 'COMPLETED', but got '{saved_state['status']}'"

        assert (
            saved_state["current_step"] == 1
        ), f"Expected current_step '1', but got '{saved_state['current_step']}'"

        final_persisted_state = saved_state["state"]
        expected_step1_output = "HELLO PERSISTENT WORLD"
        assert (
            final_persisted_state.get("step1_output") == expected_step1_output
        ), "Incorrect value for 'step1_output' in persisted state."

        print("✅ Assertions passed!")
        print("\n--- Test Finished Successfully ---")

    except Exception as e:
        print(f"\n!! An error occurred during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
