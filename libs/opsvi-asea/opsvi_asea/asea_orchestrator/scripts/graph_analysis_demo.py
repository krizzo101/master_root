import asyncio
import re
from pathlib import Path
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig, ExecutionContext

# --- Configuration ---
VERTEX_COLLECTION = "code_components"
EDGE_COLLECTION = "component_relationships"
WORKFLOW_FILE_TO_ANALYZE = "scripts/demonstration.py"


async def main():
    """
    Demonstrates using the orchestrator to build and analyze a graph of its own codebase.
    """
    print("--- 🚀 Kicking off Codebase Graph Analysis Demonstration ---")

    plugin_list = [
        "asea_orchestrator.plugins.available.file_system_plugin",
        "asea_orchestrator.plugins.available.arango_db_plugin",
    ]

    # --- Phase 1: Define Schema Setup Workflow ---
    workflow_definitions = {
        "1_setup_schema": {
            "steps": [
                {
                    "plugin_name": "arango_db",
                    "parameters": {
                        "action": "create_collection",
                        "name": VERTEX_COLLECTION,
                    },
                },
                {
                    "plugin_name": "arango_db",
                    "parameters": {
                        "action": "create_collection",
                        "name": EDGE_COLLECTION,
                        "type": "edge",
                    },
                },
            ]
        }
    }

    # --- Execute Phase 1 ---
    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(plugin_list, workflow_manager)
    plugin_configs = {
        "file_system": PluginConfig(name="fs_conf", version="1.0"),
        "arango_db": PluginConfig(name="arango_conf", version="1.0"),
    }
    await orchestrator.initialize_plugins(plugin_configs)

    print("\\n---  PHASE 1: Ensuring database schema exists ---")
    # We run this but ignore errors, as the collections might already exist.
    # A more robust solution would use a `collection_exists` plugin action.
    try:
        await orchestrator.run_workflow("1_setup_schema", {})
        print("Schema setup workflow completed successfully.")
    except Exception as e:
        print(f"Schema setup workflow failed or collections already exist: {e}")

    # --- Phase 2: Ingestion ---
    print("\\n--- PHASE 2: Ingesting codebase structure into graph ---")

    # 2a. Read the workflow file
    print(f"Reading workflow definition from: {WORKFLOW_FILE_TO_ANALYZE}")
    file_content = Path(WORKFLOW_FILE_TO_ANALYZE).read_text()

    # 2b. Parse the file to find workflow and plugin names
    # This is a simplified parser for demonstration purposes.
    workflow_name_search = re.search(
        r'workflow_definitions = {\s*"([^"]+)"', file_content
    )
    plugin_list_search = re.search(r"plugin_list = \[(.*?)\]", file_content, re.DOTALL)

    if not workflow_name_search or not plugin_list_search:
        print("Could not parse workflow file. Aborting.")
        return

    workflow_name = workflow_name_search.group(1)
    plugin_names_str = plugin_list_search.group(1)
    plugin_names = re.findall(r'"([^"]+)"', plugin_names_str)

    print(
        f"Found workflow '{workflow_name}' using plugins: {[p.split('.')[-1] for p in plugin_names]}"
    )

    # 2c. Insert components into ArangoDB
    # Insert workflow vertex
    workflow_doc = {
        "_key": workflow_name.replace("-", "_"),
        "type": "workflow",
        "name": workflow_name,
    }
    await orchestrator.run_plugin(
        "arango_db",
        ExecutionContext(
            workflow_id="ingestion",
            task_id="insert_workflow",
            state={
                "action": "insert",
                "collection": VERTEX_COLLECTION,
                "document": workflow_doc,
            },
        ),
    )

    # Insert plugin vertices and the edges connecting them
    for i, plugin_path in enumerate(plugin_names):
        plugin_name = plugin_path.split(".")[-1]
        plugin_doc = {"_key": plugin_name, "type": "plugin", "path": plugin_path}
        await orchestrator.run_plugin(
            "arango_db",
            ExecutionContext(
                workflow_id="ingestion",
                task_id=f"insert_plugin_{i}",
                state={
                    "action": "insert",
                    "collection": VERTEX_COLLECTION,
                    "document": plugin_doc,
                },
            ),
        )

        # Create the edge
        edge_doc = {
            "_from": f"{VERTEX_COLLECTION}/{workflow_doc['_key']}",
            "_to": f"{VERTEX_COLLECTION}/{plugin_doc['_key']}",
            "type": "USES_PLUGIN",
        }
        await orchestrator.run_plugin(
            "arango_db",
            ExecutionContext(
                workflow_id="ingestion",
                task_id=f"insert_edge_{i}",
                state={
                    "action": "insert",
                    "collection": EDGE_COLLECTION,
                    "document": edge_doc,
                },
            ),
        )

    print("Successfully populated graph with workflow and plugin data.")

    # --- Phase 3: Analysis & Reporting ---
    print("\\n--- PHASE 3: Analyzing graph and generating report ---")

    # 3a. Define the AQL graph traversal query
    aql_query = f"""
    WITH {VERTEX_COLLECTION}
    FOR v, e IN 1..1 OUTBOUND '{VERTEX_COLLECTION}/{workflow_doc['_key']}' {EDGE_COLLECTION}
      RETURN {{
        plugin_name: v._key,
        plugin_path: v.path,
        relationship: e.type
      }}
    """
    print("Executing AQL graph traversal query...")

    # 3b. Run the query
    query_context = ExecutionContext(
        workflow_id="analysis",
        task_id="query_graph",
        state={"action": "query", "aql_query": aql_query},
    )
    query_result = await orchestrator.run_plugin("arango_db", query_context)

    # 3c. Format and print the report
    print("\\n--- 📊 Codebase Dependency Graph Report ---")
    print(f"Dependencies for workflow: '{workflow_name}'")
    print("=" * 40)

    if query_result.success and query_result.data:
        dependencies = query_result.data.get("query_result", [])
        if dependencies:
            for dep in dependencies:
                print(f"- Uses Plugin: '{dep['plugin_name']}' ({dep['relationship']})")
        else:
            print("No dependencies found.")
    else:
        print("Failed to retrieve dependencies.")
        print(f"Error: {query_result.error_message}")

    print("=" * 40)
    print("\\n---  Graph analysis demonstration complete ---")


if __name__ == "__main__":
    asyncio.run(main())
