import asyncio
import time

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig

# A unique collection name for this test run to avoid conflicts
TEST_COLLECTION = f"test_collection_{int(time.time())}"


async def main():
    """
    Tests the new self-capability plugins with an expressive, self-contained workflow.
    """
    print("--- Testing Self-Capability Workflow ---")

    # 1. Define plugins
    plugin_list = [
        "asea_orchestrator.plugins.available.file_system_plugin",
        "asea_orchestrator.plugins.available.arango_db_plugin",
        "asea_orchestrator.plugins.available.shell_plugin",
        "asea_orchestrator.plugins.available.web_search_plugin",
    ]

    # 2. Define workflow with step-specific parameters
    workflow_definitions = {
        "self_capability_test": {
            "steps": [
                {
                    "plugin_name": "web_search",
                    "parameters": {"query": "ASEA Orchestrator"},
                    "outputs": {"search_results": "search_results"},
                },
                {
                    "plugin_name": "file_system",
                    "parameters": {"action": "read", "path": "pyproject.toml"},
                    "outputs": {"content": "file_content"},
                },
                {
                    "plugin_name": "arango_db",
                    "parameters": {
                        "aql_query": f"INSERT {{ file_content: @doc }} INTO {TEST_COLLECTION} RETURN NEW",
                    },
                    "inputs": {"file_content": "doc"},
                    "outputs": {"query_result": "db_result"},
                },
                {
                    "plugin_name": "shell",
                    "parameters": {"command": "ls -l"},
                    "outputs": {"command_result": "ls_result"},
                },
            ]
        }
    }

    # 3. Setup
    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(plugin_list, workflow_manager)

    # 4. Initialize
    plugin_configs = {
        p: PluginConfig(name=f"{p}_conf", version="1.0")
        for p in ["file_system", "arango_db", "shell", "web_search"]
    }
    await orchestrator.initialize_plugins(plugin_configs)

    # 5. Run workflow
    final_state = await orchestrator.run_workflow("self_capability_test", {})

    # 6. Validate
    print(f"\\nFinal workflow state: {final_state}")
    try:
        assert "ASEA" in str(final_state.get("search_results", ""))
        assert "[project]" in final_state.get("file_content", "")
        # Check that the DB result is a list with one document
        db_res = final_state.get("db_result", [])
        assert isinstance(db_res, list) and len(db_res) == 1
        assert "[project]" in db_res[0].get("file_content", "")
        # Check that the shell command output contains the file name
        assert "pyproject.toml" in final_state.get("ls_result", {}).get("stdout", "")
        print("\\nSelf-Capability test PASSED.")
    except (AssertionError, KeyError) as e:
        print(f"\\nSelf-Capability test FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
