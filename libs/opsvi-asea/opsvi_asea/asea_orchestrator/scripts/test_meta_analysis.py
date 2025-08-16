import asyncio
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig


async def main():
    """
    Tests the orchestrator's ability to perform a meta-analysis on its own codebase.
    """
    print("--- Testing Codebase Meta-Analysis Workflow ---")

    # 1. Define plugins
    plugin_list = [
        "asea_orchestrator.plugins.available.file_system_plugin",
    ]

    # 2. Define workflow
    workflow_definitions = {
        "code_analysis": {
            "steps": [
                {
                    "plugin_name": "file_system",
                    "parameters": {"action": "list", "path": "src/asea_orchestrator"},
                    "outputs": {"files": "file_list"},
                },
                # The subsequent steps (read, analyze, write) will be driven by a
                # more advanced "workflow controller" plugin in the future.
                # For now, we will demonstrate the first step.
            ]
        }
    }

    # 3. Setup
    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(plugin_list, workflow_manager)

    # 4. Initialize
    plugin_configs = {
        "file_system": PluginConfig(name="fs_conf", version="1.0"),
    }
    await orchestrator.initialize_plugins(plugin_configs)

    # 5. Run workflow
    final_state = await orchestrator.run_workflow("code_analysis", {})

    # 6. Validate
    print(f"\\nFinal workflow state: {final_state}")
    try:
        assert "core.py" in str(final_state.get("file_list", []))
        assert "workflow.py" in str(final_state.get("file_list", []))
        print("\\nMeta-Analysis test (step 1) PASSED.")
    except (AssertionError, KeyError) as e:
        print(f"\\nMeta-Analysis test FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
