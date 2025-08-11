import asyncio

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig, Event


async def simulate_user(event_bus):
    """
    Waits for a prompt and then provides input after a delay.
    """

    async def handler(event: Event):
        print(f"  [Simulated User] Received prompt: '{event.payload.get('prompt')}'")
        # No need to create a new task, the event bus does that.
        # Just call the async function directly.
        await provide_input(event_bus)

    event_bus.subscribe("waiting_for_input", handler)


async def provide_input(event_bus):
    await asyncio.sleep(0.1)  # Simulate user thinking time
    user_data = "This is the input from the simulated user."
    print(f"  [Simulated User] Providing input: '{user_data}'")
    await event_bus.publish("input_received", {"data": user_data})


async def main():
    """
    Tests the Human-in-the-Loop functionality.
    """
    print("--- Testing HITL Workflow ---")

    # 1. Define plugins
    plugin_list = [
        "asea_orchestrator.plugins.available.pause_for_input_plugin",
    ]

    # 2. Define workflow
    workflow_definitions = {
        "hitl_workflow": {
            "steps": [
                {
                    "plugin_name": "pause_for_input",
                    "inputs": {},
                    "outputs": {"human_input": "final_result"},
                }
            ]
        }
    }

    # 3. Setup
    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(plugin_list, workflow_manager)

    # 4. Initialize
    plugin_configs = {
        "pause_for_input": PluginConfig(name="p_conf", version="1.0", config={}),
    }
    await orchestrator.initialize_plugins(plugin_configs)

    # 5. Run simulation
    # Run the user simulation and the workflow concurrently
    user_task = asyncio.create_task(simulate_user(orchestrator.event_bus))
    workflow_task = asyncio.create_task(orchestrator.run_workflow("hitl_workflow", {}))

    final_state = await workflow_task
    user_task.cancel()  # Clean up the user task

    # 6. Validate
    print(f"\\nFinal workflow state: {final_state}")
    try:
        assert (
            final_state["final_result"] == "This is the input from the simulated user."
        )
        print("\\nHITL test PASSED.")
    except (AssertionError, KeyError) as e:
        print(f"\\nHITL test FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
