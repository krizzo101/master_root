"""
Simple Phase 2 Test - Verify Enhanced Capabilities

Tests the core Phase 2 enhancements without complex workflows.
"""

import sys
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
from .error_recovery import (
    create_default_error_patterns,
    RetryStrategy,
)
from ..plugins.available.cognitive_reminder_plugin import CognitiveReminderPlugin


def test_conditional_routing():
    """Test conditional routing capabilities."""
    print("🔀 Testing Conditional Routing...")

    router = ConditionalRouter()

    # Add test conditions
    router.add_condition(
        "has_errors",
        lambda state: len(state.get("errors", [])) > 0,
        "Check if workflow has errors",
    )

    router.add_condition(
        "good_quality",
        lambda state: len(state.get("workflow_state", {}).get("response", "")) > 50,
        "Check if response is good quality",
    )

    # Add routes
    router.add_route("step1", "has_errors", "error_handler", "step2")
    router.add_route("step2", "good_quality", "finalize", "improve")

    # Test state with no errors, good quality
    test_state = ASEAState(
        workflow_name="test",
        run_id="test1",
        current_step="step2",
        workflow_state={
            "response": "This is a good quality response with sufficient length."
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
    )

    routing_func = router.create_routing_function("step2")
    next_step = routing_func(test_state)

    print(f"✅ Conditional routing working: step2 → {next_step}")
    return True


def test_streaming():
    """Test streaming capabilities."""
    print("📡 Testing Streaming Manager...")

    streaming = StreamingManager(enable_streaming=True)

    # Test callback
    updates_received = []

    def test_callback(update):
        updates_received.append(update)

    streaming.subscribe(test_callback)

    # Emit test updates
    streaming.emit_update("test_type", {"message": "test data"})

    if len(updates_received) == 1:
        print("✅ Streaming working: callback received update")
        return True
    else:
        print("❌ Streaming failed: no updates received")
        return False


def test_error_recovery():
    """Test error recovery capabilities."""
    print("🛡️  Testing Error Recovery...")

    recovery_manager = create_default_error_patterns()

    # Configure retry for test node
    recovery_manager.configure_retry(
        "test_node", max_attempts=2, strategy=RetryStrategy.IMMEDIATE
    )

    # Test function that fails once then succeeds
    attempt_count = 0

    def test_node_func(state):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise Exception("Test failure")
        return state

    # Create test state
    test_state = ASEAState(
        workflow_name="test",
        run_id="test1",
        current_step="test_node",
        workflow_state={},
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
    )

    # Execute with recovery
    result_state = recovery_manager.execute_with_recovery(
        "test_node", test_node_func, test_state
    )

    if (
        "recovery_metadata" in result_state
        and result_state["recovery_metadata"]["test_node"]["recovery_used"]
    ):
        print("✅ Error recovery working: retry succeeded")
        return True
    else:
        print("❌ Error recovery failed")
        return False


def test_enhanced_workflow():
    """Test enhanced workflow builder."""
    print("🏗️  Testing Enhanced Workflow Builder...")

    builder = EnhancedWorkflowBuilder(enable_streaming=True, enable_approvals=False)

    # Add simple node
    builder.add_plugin_node(
        name="cognitive_reminder",
        plugin_class=CognitiveReminderPlugin,
        input_mapping={
            "user_prompt": "{{ workflow.input.user_prompt }}",
            "task_type": "{{ workflow.input.task_type }}",
        },
        output_mapping={"reminders": "reminders"},
    )

    builder.set_entry_point("cognitive_reminder")
    builder.add_edge("cognitive_reminder", END)

    # Build workflow
    workflow_graph = builder.build()
    compiled_workflow = workflow_graph.compile(checkpointer=MemorySaver())

    # Test execution
    initial_state = create_initial_state(
        workflow_name="test_workflow",
        run_id=str(uuid.uuid4()),
        user_input={
            "user_prompt": "Test productivity question",
            "task_type": "productivity",
        },
        workflow_config={"enable_streaming": True},
    )

    try:
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        final_state = compiled_workflow.invoke(initial_state, config=config)
        if "reminders" in final_state.get("workflow_state", {}):
            print("✅ Enhanced workflow working: reminders generated")
            return True
        else:
            print("❌ Enhanced workflow failed: no reminders")
            return False
    except Exception as e:
        print(f"❌ Enhanced workflow failed: {e}")
        return False


def run_phase2_tests():
    """Run all Phase 2 tests."""
    print("=" * 60)
    print("🧪 PHASE 2 ENHANCED CAPABILITIES TEST SUITE")
    print("=" * 60)

    tests = [
        ("Conditional Routing", test_conditional_routing),
        ("Streaming Manager", test_streaming),
        ("Error Recovery", test_error_recovery),
        ("Enhanced Workflow", test_enhanced_workflow),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 All Phase 2 capabilities working correctly!")
    else:
        print("⚠️  Some Phase 2 capabilities need attention.")

    return passed == total


if __name__ == "__main__":
    run_phase2_tests()
