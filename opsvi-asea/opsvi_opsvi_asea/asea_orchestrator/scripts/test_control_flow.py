import asyncio
from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig


# A simple plugin for testing state changes.
class StateManagerPlugin:
    @staticmethod
    def get_name():
        return "state_manager"

    async def initialize(self, c, e):
        pass

    async def cleanup(self):
        pass

    def get_capabilities(self):
        return []

    def validate_input(self, i):
        return type("VR", (), {"is_valid": True})()

    async def execute(self, context):
        new_val = context.state.get("new_value")
        if new_val is not None:
            # The workflow maps the output 'result' to the state key 'final_result'.
            # The plugin must return data with the key 'result'.
            return type("PR", (), {"success": True, "data": {"result": new_val}})()

        op = context.state.get("operation")
        if op == "add_to_list":
            current_list = context.state.get("output_list", [])
            current_list.append(context.state.get("item"))
            return type(
                "PR", (), {"success": True, "data": {"list_key": current_list}}
            )()

        return type(
            "PR", (), {"success": False, "error_message": "Invalid operation"}
        )()


async def main():
    print("--- Testing Control Flow ---")

    # Define all workflows
    for_each_wf = {
        "for_each_test": {
            "steps": [
                {
                    "plugin_name": "control_flow",
                    "parameters": {
                        "type": "for_each",
                        "list_key": "input_list",
                        "item_key": "current_item",
                        "loop_workflow": {
                            "steps": [
                                {
                                    "plugin_name": "state_manager",
                                    "parameters": {"operation": "add_to_list"},
                                    "inputs": {
                                        "current_item": "item",
                                        "output_list": "output_list",
                                    },
                                    "outputs": {"list_key": "output_list"},
                                }
                            ]
                        },
                    },
                }
            ]
        }
    }
    if_else_wf = {
        "if_test": {
            "steps": [
                {
                    "plugin_name": "control_flow",
                    "parameters": {
                        "type": "if",
                        "condition": {
                            "key": "branch_on",
                            "operator": "equals",
                            "value": "go_left",
                        },
                        "then_workflow": {
                            "steps": [
                                {
                                    "plugin_name": "state_manager",
                                    "parameters": {"new_value": "left_branch_taken"},
                                    "outputs": {"result": "final_result"},
                                }
                            ]
                        },
                        "else_workflow": {
                            "steps": [
                                {
                                    "plugin_name": "state_manager",
                                    "parameters": {"new_value": "right_branch_taken"},
                                    "outputs": {"result": "final_result"},
                                }
                            ]
                        },
                    },
                }
            ]
        }
    }
    all_workflows = {**for_each_wf, **if_else_wf}

    # Setup orchestrator correctly
    wm = WorkflowManager(all_workflows)
    orchestrator = Orchestrator(plugin_modules=[], workflow_manager=wm)

    # Manually inject initialized plugin instances for testing
    orchestrator.plugin_instances = {
        "state_manager": StateManagerPlugin(),
        "control_flow": type("CFP", (), {"get_name": lambda: "control_flow"})(),
    }

    # --- Test 1: For Each Loop ---
    initial_state = {"input_list": ["a", "b", "c"], "output_list": []}
    final_state = await orchestrator.run_workflow("for_each_test", initial_state)

    print(f"Final state for 'for_each': {final_state}")
    assert final_state.get("output_list") == ["a", "b", "c"]
    print("✅ For Each Test PASSED.")

    # --- Test 2: If/Else Branching ---
    # Test the "then" branch
    initial_state = {"branch_on": "go_left"}
    final_state = await orchestrator.run_workflow("if_test", initial_state)
    print(f"Final state for 'if_then': {final_state}")
    assert final_state.get("final_result") == "left_branch_taken"

    # Test the "else" branch
    initial_state = {"branch_on": "go_right"}
    final_state = await orchestrator.run_workflow("if_test", initial_state)
    print(f"Final state for 'if_else': {final_state}")
    assert final_state.get("final_result") == "right_branch_taken"
    print("✅ If/Else Test PASSED.")


if __name__ == "__main__":
    asyncio.run(main())
