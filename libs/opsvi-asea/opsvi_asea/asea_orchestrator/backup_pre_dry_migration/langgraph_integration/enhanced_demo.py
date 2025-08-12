"""
Enhanced ASEA-LangGraph Integration Demo - Phase 2

Demonstrates advanced capabilities including conditional routing, streaming,
human-in-the-loop, and enhanced state management.
"""

import sys
import time
import uuid
from pathlib import Path

# Add the ASEA orchestrator to the path
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import END
from langgraph.checkpoint.memory import MemorySaver

from .state import ASEAState, create_initial_state
from .enhanced_workflows import (
    EnhancedWorkflowBuilder,
    ConditionalRouter,
    StreamingManager,
)
from .checkpointer import ASEAArangoCheckpointer
from ..plugins.available.cognitive_reminder_plugin import CognitiveReminderPlugin
from ..plugins.available.cognitive_pre_analysis_plugin import CognitivePreAnalysisPlugin
from ..plugins.available.ai_reasoning_plugin import AIReasoningPlugin
from ..plugins.available.cognitive_critic_plugin import CognitiveCriticPlugin


def create_streaming_callback():
    """Create a streaming callback for real-time updates."""

    def streaming_callback(update: dict):
        timestamp = update["timestamp"]
        update_type = update["type"]
        data = update["data"]

        if update_type == "step_start":
            print(f"🚀 [{timestamp[-8:]}] Starting: {data['step_name']}")

        elif update_type == "step_complete":
            execution_time = data["execution_time"]
            print(
                f"✅ [{timestamp[-8:]}] Completed: {data['step_name']} ({execution_time:.3f}s)"
            )

        elif update_type == "step_error":
            execution_time = data["execution_time"]
            error = data["error"]
            print(
                f"❌ [{timestamp[-8:]}] Error: {data['step_name']} ({execution_time:.3f}s) - {error}"
            )

        elif update_type == "workflow_complete":
            total_time = data["total_execution_time"]
            steps = data["steps_completed"]
            print(
                f"🎯 [{timestamp[-8:]}] Workflow Complete: {steps} steps in {total_time:.3f}s"
            )

    return streaming_callback


def create_enhanced_cognitive_workflow_with_routing():
    """
    Create an enhanced cognitive workflow with conditional routing.

    Flow:
    1. Cognitive Reminder (always)
    2. Pre-Analysis (always)
    3. AI Reasoning (always)
    4. Conditional: If reasoning quality is low → Critic Review → Improved Reasoning
    5. Final output
    """
    builder = EnhancedWorkflowBuilder(enable_streaming=True, enable_approvals=True)

    # Add streaming callback
    builder.streaming.subscribe(create_streaming_callback())

    # Step 1: Cognitive Reminder
    builder.add_plugin_node(
        name="cognitive_reminder",
        plugin_class=CognitiveReminderPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "task_type": "{{ workflow.input.task_type }}",
        },
        output_mapping={"reminders": "reminders"},
    )

    # Step 2: Pre-Analysis
    builder.add_plugin_node(
        name="cognitive_pre_analysis",
        plugin_class=CognitivePreAnalysisPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "context": "{{ workflow.state.reminders }}",
        },
        output_mapping={"enhanced_understanding": "enhanced_understanding"},
    )

    # Step 3: Initial AI Reasoning
    builder.add_plugin_node(
        name="ai_reasoning_initial",
        plugin_class=AIReasoningPlugin,
        input_mapping={
            "prompt": "{{ workflow.state.enhanced_understanding }}",
            "user_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"response": "initial_response"},
        requires_approval=True,
        approval_type="quality_check",
    )

    # Step 4: Cognitive Critic (conditional)
    builder.add_plugin_node(
        name="cognitive_critic",
        plugin_class=CognitiveCriticPlugin,
        input_mapping={
            "response": "{{ workflow.state.initial_response }}",
            "original_prompt": "{{ workflow.input.user_prompt }}",
        },
        output_mapping={"critique": "critique_results"},
    )

    # Step 5: Improved AI Reasoning (conditional)
    builder.add_plugin_node(
        name="ai_reasoning_improved",
        plugin_class=AIReasoningPlugin,
        input_mapping={
            "prompt": "{{ workflow.state.enhanced_understanding }}",
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "previous_response": "{{ workflow.state.initial_response }}",
            "critique_feedback": "{{ workflow.state.critique_results }}",
        },
        output_mapping={"response": "final_response"},
    )

    # Define workflow edges
    builder.add_edge("cognitive_reminder", "cognitive_pre_analysis")
    builder.add_edge("cognitive_pre_analysis", "ai_reasoning_initial")

    # Conditional routing: Check if initial response needs improvement
    def needs_improvement(state: ASEAState) -> bool:
        """Check if the initial AI response needs improvement."""
        # Check approval results
        human_feedback = state.get("human_feedback", {})
        initial_approval = human_feedback.get("ai_reasoning_initial", {})

        if not initial_approval.get("approved", True):
            return True

        # Check quality metrics
        quality_metrics = initial_approval.get("quality_metrics", {})
        quality_score = quality_metrics.get("score", 1.0)

        return quality_score < 0.8  # Improve if quality score < 80%

    # Add conditional routing
    builder.add_conditional_edge(
        from_node="ai_reasoning_initial",
        condition_func=needs_improvement,
        true_path="cognitive_critic",  # Route to critic if improvement needed
        false_path=END,  # End workflow if quality is good
        condition_name="quality_check",
    )

    builder.add_edge("cognitive_critic", "ai_reasoning_improved")
    builder.add_edge("ai_reasoning_improved", END)

    # Set entry point
    builder.set_entry_point("cognitive_reminder")

    return builder


def demo_enhanced_workflow():
    """
    Demonstrate the enhanced workflow with all Phase 2 capabilities.
    """
    print("=== Enhanced ASEA-LangGraph Integration Demo - Phase 2 ===")
    print(
        "Features: Conditional Routing + Streaming + Human-in-the-Loop + Advanced State Management"
    )
    print()

    # Create enhanced workflow
    print("🏗️  Building enhanced cognitive workflow...")
    builder = create_enhanced_cognitive_workflow_with_routing()
    workflow_graph = builder.build()

    # Add checkpointing
    checkpointer = MemorySaver()
    compiled_workflow = workflow_graph.compile(checkpointer=checkpointer)

    print("✅ Enhanced workflow built successfully!")
    print()

    # Test scenarios
    test_scenarios = [
        {
            "name": "Simple Productivity Question",
            "user_prompt": "How can I be more productive when working from home?",
            "task_type": "productivity",
        },
        {
            "name": "Complex Research Question",
            "user_prompt": "What are the latest developments in quantum computing and their potential impact on cybersecurity?",
            "task_type": "research",
        },
        {
            "name": "Creative Problem Solving",
            "user_prompt": "Design an innovative solution for reducing food waste in urban areas.",
            "task_type": "creative",
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🧪 Test Scenario {i}: {scenario['name']}")
        print(f"📝 Prompt: {scenario['user_prompt']}")
        print()

        # Create initial state
        run_id = str(uuid.uuid4())
        initial_state = create_initial_state(
            workflow_name="enhanced_cognitive_workflow",
            run_id=run_id,
            user_input={
                "user_prompt": scenario["user_prompt"],
                "task_type": scenario.get("task_type", "general"),
            },
            workflow_config={"enable_streaming": True},
        )

        # Execute workflow
        start_time = time.time()
        config = {"configurable": {"thread_id": run_id}}

        try:
            print("🚀 Executing enhanced workflow...")
            final_state = compiled_workflow.invoke(initial_state, config=config)
            execution_time = time.time() - start_time

            # Emit final streaming update
            builder.streaming.emit_workflow_complete(final_state, execution_time)

            print()
            print("📊 === Enhanced Workflow Results ===")
            print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
            print(f"🔧 Steps completed: {len(final_state.get('plugin_outputs', {}))}")

            # Show routing decisions
            human_feedback = final_state.get("human_feedback", {})
            if human_feedback:
                print()
                print("🤖 Human-in-the-Loop Decisions:")
                for step, feedback in human_feedback.items():
                    approved = (
                        "✅ Approved" if feedback.get("approved") else "❌ Rejected"
                    )
                    print(
                        f"   {step}: {approved} - {feedback.get('feedback', 'No feedback')}"
                    )

            # Show final outputs
            workflow_state = final_state.get("workflow_state", {})
            if "final_response" in workflow_state:
                print()
                print("🎯 Final Enhanced Response:")
                print(workflow_state["final_response"])
            elif "initial_response" in workflow_state:
                print()
                print("🎯 Initial Response (No Improvement Needed):")
                print(workflow_state["initial_response"])

            # Show performance metrics
            step_timings = final_state.get("step_timings", {})
            if step_timings:
                print()
                print("⚡ Performance Metrics:")
                for step, timing in step_timings.items():
                    print(f"   {step}: {timing:.3f}s")

            # Show any errors
            errors = final_state.get("errors", [])
            if errors:
                print()
                print("⚠️  Errors:")
                for error in errors:
                    print(f"   - {error}")

        except Exception as e:
            print(f"❌ Enhanced workflow execution failed: {e}")
            import traceback

            traceback.print_exc()

        print()
        print("=" * 80)
        print()


def demo_conditional_routing():
    """
    Demonstrate conditional routing capabilities.
    """
    print("🔀 === Conditional Routing Demo ===")

    router = ConditionalRouter()

    # Add example conditions
    router.add_condition(
        "has_errors",
        lambda state: len(state.get("errors", [])) > 0,
        "Check if workflow has any errors",
    )

    router.add_condition(
        "quality_threshold",
        lambda state: state.get("workflow_state", {}).get("quality_score", 0) > 0.8,
        "Check if output quality is above threshold",
    )

    router.add_condition(
        "needs_review",
        lambda state: len(state.get("workflow_state", {}).get("response", "")) < 100,
        "Check if response is too short and needs review",
    )

    # Add routes
    router.add_route("step1", "has_errors", "error_handler", "step2")
    router.add_route("step2", "quality_threshold", "finalize", "quality_improvement")
    router.add_route("quality_improvement", "needs_review", "human_review", END)

    print("✅ Conditional router configured with 3 conditions and 3 routes")

    # Test routing decisions
    test_states = [
        {
            "name": "No errors, high quality",
            "state": ASEAState(
                workflow_name="test",
                run_id="test1",
                current_step="step2",
                workflow_state={
                    "quality_score": 0.9,
                    "response": "This is a high quality response with sufficient detail.",
                },
                plugin_outputs={},
                execution_context={},
                cognitive_metadata={},
                reminders=[],
                enhanced_understanding=None,
                input_mappings={},
                output_mappings={},
                errors=[],
                fallback_data={},
                step_timings={},
                plugin_metadata={},
                checkpointed_at=None,
                human_feedback=None,
                streaming_enabled=False,
            ),
        },
        {
            "name": "Has errors",
            "state": ASEAState(
                workflow_name="test",
                run_id="test2",
                current_step="step1",
                workflow_state={},
                plugin_outputs={},
                execution_context={},
                cognitive_metadata={},
                reminders=[],
                enhanced_understanding=None,
                input_mappings={},
                output_mappings={},
                errors=["Plugin failed", "API timeout"],
                fallback_data={},
                step_timings={},
                plugin_metadata={},
                checkpointed_at=None,
                human_feedback=None,
                streaming_enabled=False,
            ),
        },
        {
            "name": "Low quality, short response",
            "state": ASEAState(
                workflow_name="test",
                run_id="test3",
                current_step="quality_improvement",
                workflow_state={"quality_score": 0.6, "response": "Short answer."},
                plugin_outputs={},
                execution_context={},
                cognitive_metadata={},
                reminders=[],
                enhanced_understanding=None,
                input_mappings={},
                output_mappings={},
                errors=[],
                fallback_data={},
                step_timings={},
                plugin_metadata={},
                checkpointed_at=None,
                human_feedback=None,
                streaming_enabled=False,
            ),
        },
    ]

    print()
    print("🧪 Testing routing decisions:")
    for test in test_states:
        print(f"\n📋 Test: {test['name']}")
        state = test["state"]
        current_step = state["current_step"]

        if current_step in router.routes:
            routing_func = router.create_routing_function(current_step)
            next_step = routing_func(state)
            route_config = router.routes[current_step]
            condition_name = route_config["condition"]
            condition_result = router.conditions[condition_name]["func"](state)

            print(f"   Current step: {current_step}")
            print(f"   Condition '{condition_name}': {condition_result}")
            print(f"   Next step: {next_step}")
        else:
            print(f"   No routing configured for step: {current_step}")

    print()


if __name__ == "__main__":
    # Run conditional routing demo
    demo_conditional_routing()

    # Run enhanced workflow demo
    demo_enhanced_workflow()

    print("🎉 Enhanced demo complete! Phase 2 capabilities demonstrated.")
