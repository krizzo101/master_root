#!/usr/bin/env python3
"""
ASEA Orchestrator Command-Line Interface (CLI)

A tool for interacting with and managing `asea_orchestrator` workflows.
"""

import argparse
import asyncio
import sys
import os
import json

# --- Absolute Path Setup for Module Resolution ---
WORKSPACE_ROOT = "/home/opsvi/asea"
SRC_PATH = os.path.join(WORKSPACE_ROOT, "asea_orchestrator/src")
sys.path.insert(0, SRC_PATH)
# ---

from asea_orchestrator.database import ArangoDBClient


class WorkflowCLI:
    """Handles CLI commands for workflows."""

    def __init__(self):
        self.db_client = ArangoDBClient()

    async def connect(self):
        """Connects the client to the database."""
        print("Connecting to database...")
        connected = await self.db_client.connect()
        if not connected:
            print(
                "Error: Could not connect to the database. Check configuration and ensure ArangoDB is running."
            )
            return False
        print("✓ Database connection successful.")
        return True

    async def disconnect(self):
        """Disconnects the client from the database."""
        if self.db_client:
            await self.db_client.disconnect()
            print("✓ Database connection closed.")

    async def list_workflows(self, args):
        """Lists all workflow runs from the database."""
        print("\n--- Listing All Workflow Runs ---")
        cursor = await self.db_client.async_db.aql.execute(
            "FOR doc IN workflow_states RETURN { run_id: doc._key, status: doc.status, updated_at: doc.updated_at }"
        )
        results = [doc async for doc in cursor]

        print("Run ID                             | Status      | Last Updated")
        print(
            "------------------------------------|-------------|--------------------------"
        )
        if not results:
            print("No workflow runs found.")
        else:
            for res in results:
                run_id = res.get("run_id", "N/A").ljust(35)
                status = res.get("status", "N/A").ljust(12)
                updated = res.get("updated_at", "N/A")
                print(f"{run_id}| {status}| {updated}")

    async def workflow_status(self, args):
        """Gets the detailed status of a specific workflow run."""
        run_id = args.run_id
        print(f"\n--- Status for Workflow Run: {run_id} ---")

        doc = await self.db_client.load_workflow_state(run_id)

        if not doc:
            print(f"Error: No workflow found with run_id '{run_id}'.")
            return

        print(f"Status: {doc.get('status', 'N/A')}")
        print(f"Current Step: {doc.get('current_step', 'N/A')}")
        print("State:")
        # Pretty print the state dictionary
        state_json = json.dumps(doc.get("state", {}), indent=2)
        print(state_json)

    async def clean_workflows(self, args):
        """Cleans up workflow runs from the database."""
        print("\n--- Cleaning Workflows ---")

        aql_query = "FOR doc IN workflow_states "
        bind_vars = {}

        if args.all:
            print("Mode: Cleaning ALL workflow runs.")
            # No filter needed to remove all
        elif args.failed:
            print("Mode: Cleaning FAILED workflow runs.")
            aql_query += "FILTER doc.status == @status "
            bind_vars["status"] = "FAILED"
        elif args.completed:
            print("Mode: Cleaning COMPLETED workflow runs.")
            aql_query += "FILTER doc.status == @status "
            bind_vars["status"] = "COMPLETED"
        else:
            print("No cleanup mode selected. Use --all, --failed, or --completed.")
            return

        aql_query += "REMOVE doc IN workflow_states"

        print("Executing cleanup...")
        await self.db_client.async_db.aql.execute(aql_query, bind_vars=bind_vars)
        print("✓ Cleanup operation completed.")


async def main():
    """Parses arguments and dispatches commands."""
    parser = argparse.ArgumentParser(description="ASEA Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    cli = WorkflowCLI()

    # 'workflow list' command
    list_parser = subparsers.add_parser("list", help="List all workflow runs.")
    list_parser.set_defaults(func=cli.list_workflows)

    # 'workflow status' command
    status_parser = subparsers.add_parser(
        "status", help="Get the status of a specific workflow."
    )
    status_parser.add_argument("run_id", help="The unique ID of the workflow run.")
    status_parser.set_defaults(func=cli.workflow_status)

    # 'workflow clean' command
    clean_parser = subparsers.add_parser("clean", help="Clean up workflow runs.")
    clean_group = clean_parser.add_mutually_exclusive_group(required=True)
    clean_group.add_argument(
        "--all", action="store_true", help="Clean up all workflow runs."
    )
    clean_group.add_argument(
        "--failed", action="store_true", help="Clean up only failed workflow runs."
    )
    clean_group.add_argument(
        "--completed",
        action="store_true",
        help="Clean up only completed workflow runs.",
    )
    clean_parser.set_defaults(func=cli.clean_workflows)

    args = parser.parse_args()

    # Connect to DB before running command
    if not await cli.connect():
        return

    try:
        if hasattr(args, "func"):
            await args.func(args)
        else:
            parser.print_help()
    finally:
        # Ensure disconnection
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
