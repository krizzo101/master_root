"""
ASEA-LangGraph Integration Demo

Demonstrates the integration between ASEA plugins and LangGraph workflows,
showing how existing ASEA functionality works within LangGraph orchestration.
"""

import sys
import time
import uuid
from pathlib import Path

# Add the ASEA orchestrator to the path
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ASEAState, create_initial_state
from .plugin_adapter import create_plugin_node
from .workflow_converter import WorkflowConverter
from ..plugins.available.cognitive_reminder_plugin import CognitiveReminderPlugin
from ..plugins.available.cognitive_pre_analysis_plugin import CognitivePreAnalysisPlugin
from ..plugins.available.ai_reasoning_plugin import AIReasoningPlugin


def create_simple_cognitive_workflow() -> StateGraph:
    """
    Create a simple cognitive enhancement workflow using LangGraph.

    Returns:
        Compiled LangGraph workflow
    """
    # Create the workflow graph
    workflow = StateGraph(ASEAState)

    # Create plugin nodes
    reminder_node = create_plugin_node(
        plugin_class=CognitiveReminderPlugin,
        input_mapping={"context": "{{ workflow.input.user_prompt }}"},
        output_mapping={"reminders": "reminders"},
    )

    pre_analysis_node = create_plugin_node(
        plugin_class=CognitivePreAnalysisPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "context": "{{ workflow.state.reminders }}",
        },
        output_mapping={"enhanced_understanding": "enhanced_understanding"},
    )

    reasoning_node = create_plugin_node(
        plugin_class=AIReasoningPlugin,
        input_mapping={
            "prompt": "{{ workflow.state.enhanced_understanding }}",
            "user_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"response": "final_response"},
    )

    # Add nodes to workflow
    workflow.add_node("cognitive_reminder", reminder_node)
    workflow.add_node("cognitive_pre_analysis", pre_analysis_node)
    workflow.add_node("ai_reasoning", reasoning_node)

    # Define workflow flow
    workflow.set_entry_point("cognitive_reminder")
    workflow.add_edge("cognitive_reminder", "cognitive_pre_analysis")
    workflow.add_edge("cognitive_pre_analysis", "ai_reasoning")
    workflow.add_edge("ai_reasoning", END)

    return workflow


def demo_basic_integration():
    """
    Demonstrate basic ASEA-LangGraph integration.
    """
    print("=== ASEA-LangGraph Integration Demo ===")
    print("Creating cognitive enhancement workflow...")

    # Create workflow
    workflow = create_simple_cognitive_workflow()

    # Add checkpointing
    checkpointer = MemorySaver()
    compiled_workflow = workflow.compile(checkpointer=checkpointer)

    # Test input
    user_input = {
        "user_prompt": "How can I improve my productivity while working from home?"
    }

    # Create initial state
    run_id = str(uuid.uuid4())
    initial_state = create_initial_state(
        workflow_name="cognitive_enhancement_demo",
        run_id=run_id,
        user_input=user_input,
        workflow_config={},
    )

    print(f"\nExecuting workflow with run_id: {run_id}")
    print(f"User prompt: {user_input['user_prompt']}")

    # Execute workflow
    start_time = time.time()
    config = {"configurable": {"thread_id": run_id}}

    try:
        final_state = compiled_workflow.invoke(initial_state, config=config)
        execution_time = time.time() - start_time

        print(f"\n=== Workflow Execution Results ===")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Steps completed: {len(final_state.get('plugin_outputs', {}))}")

        # Display step results
        for step_name, output in final_state.get("plugin_outputs", {}).items():
            print(f"\n--- {step_name.upper()} ---")
            if isinstance(output, dict):
                for key, value in output.items():
                    print(f"{key}: {value}")
            else:
                print(f"Output: {output}")

        # Display final response
        final_response = final_state.get("workflow_state", {}).get("final_response")
        if final_response:
            print(f"\n=== FINAL ENHANCED RESPONSE ===")
            print(final_response)

        # Display performance metrics
        step_timings = final_state.get("step_timings", {})
        if step_timings:
            print(f"\n=== Performance Metrics ===")
            for step, timing in step_timings.items():
                print(f"{step}: {timing:.3f}s")

        # Display any errors
        errors = final_state.get("errors", [])
        if errors:
            print(f"\n=== Errors ===")
            for error in errors:
                print(f"- {error}")

        return final_state

    except Exception as e:
        print(f"\nWorkflow execution failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def demo_workflow_converter():
    """
    Demonstrate the workflow converter functionality.
    """
    print("\n=== Workflow Converter Demo ===")

    # Try to convert existing workflow
    try:
        converter = WorkflowConverter()
        workflow_executor = converter.convert_cognitive_enhancement_workflow()

        print("Successfully converted cognitive enhancement workflow!")

        # Test the converted workflow
        user_input = {
            "user_prompt": "What are the best practices for remote team collaboration?"
        }

        print(f"\nTesting converted workflow...")
        print(f"User prompt: {user_input['user_prompt']}")

        start_time = time.time()
        result = workflow_executor(user_input)
        execution_time = time.time() - start_time

        print(f"\nConverted workflow execution time: {execution_time:.2f} seconds")
        print(f"Final state keys: {list(result.keys())}")

        return result

    except Exception as e:
        print(f"Workflow converter demo failed: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Run basic integration demo
    basic_result = demo_basic_integration()

    # Run workflow converter demo
    converter_result = demo_workflow_converter()

    print("\n=== Demo Complete ===")

    if basic_result and converter_result:
        print("✅ Both demos completed successfully!")
        print("✅ ASEA-LangGraph integration is working!")
    else:
        print("❌ Some demos failed - check errors above")
