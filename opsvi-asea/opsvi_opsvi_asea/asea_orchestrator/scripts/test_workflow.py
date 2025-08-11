import asyncio

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig


async def main():
    """
    Tests the full workflow execution functionality.
    """
    print("--- Testing Workflow Execution ---")

    # 1. Define plugins to be available
    plugin_list = [
        "asea_orchestrator.plugins.available.hello_world_plugin",
        "asea_orchestrator.plugins.available.to_upper_plugin",
        "asea_orchestrator.plugins.available.logging_plugin",
    ]

    # 2. Define the workflow
    workflow_definitions = {
        "greeting_workflow": {
            "steps": [
                {
                    "plugin_name": "hello_world",
                    "inputs": {},
                    "outputs": {"message": "greeting_message"},
                },
                {
                    "plugin_name": "to_upper",
                    "inputs": {"greeting_message": "input_string"},
                    "outputs": {"output_string": "final_greeting"},
                },
            ]
        }
    }

    # 3. Setup managers and orchestrator
    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(plugin_list, workflow_manager)

    # 4. Prepare plugin configurations and initialize
    plugin_configs = {
        "hello_world": PluginConfig(name="hw_conf", version="1.0", config={}),
        "to_upper": PluginConfig(name="tu_conf", version="1.0", config={}),
        "logger": PluginConfig(name="log_conf", version="1.0", config={}),
    }
    await orchestrator.initialize_plugins(plugin_configs)

    # 5. Run the workflow
    initial_state = {"input": "This is the initial state."}
    final_state = await orchestrator.run_workflow("greeting_workflow", initial_state)

    # A small delay to allow event handlers to complete
    await asyncio.sleep(0.01)

    # 6. Validate the final state
    print(f"\\nFinal workflow state: {final_state}")
    try:
        assert final_state["greeting_message"] == "Hello, World!"
        assert final_state["final_greeting"] == "HELLO, WORLD!"
        print("\\nWorkflow test PASSED.")
    except (AssertionError, KeyError) as e:
        print(f"\\nWorkflow test FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
