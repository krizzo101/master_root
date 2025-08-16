import asyncio
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.plugins.types import ExecutionContext, PluginConfig


async def main():
    """
    Tests the core Orchestrator functionality.
    """
    print("--- Testing Orchestrator ---")

    # Define which plugins to load
    plugin_list = ["asea_orchestrator.plugins.available.hello_world_plugin"]

    # Initialize the orchestrator (discovers plugins)
    orchestrator = Orchestrator(plugin_modules=plugin_list)

    # Prepare plugin configurations
    hello_config = PluginConfig(
        name="hello_world_config", version="1.0", config={"greeting": "Orchestrator"}
    )

    # Initialize plugins
    await orchestrator.initialize_plugins(configs={"hello_world": hello_config})

    # Prepare execution context
    context = ExecutionContext(workflow_id="wf-1", task_id="task-1", state={})

    # Run the plugin
    try:
        result = await orchestrator.run_plugin("hello_world", context)
        print(f"\nPlugin returned: {result}")
        assert result.success is True
        assert result.data["message"] == "Hello, World!"
        print("\nOrchestrator test PASSED.")
    except (ValueError, AssertionError) as e:
        print(f"\nOrchestrator test FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
