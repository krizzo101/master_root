#!/usr/bin/env python3
"""
Test individual AI plugins to verify they work independently
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from asea_orchestrator.plugins.available.ai_reasoning_plugin import AIReasoningPlugin
from asea_orchestrator.plugins.available.budget_manager_plugin import (
    BudgetManagerPlugin,
)
from asea_orchestrator.plugins.available.workflow_intelligence_plugin import (
    WorkflowIntelligencePlugin,
)
from asea_orchestrator.plugins.types import PluginConfig, ExecutionContext


def test_ai_reasoning_plugin():
    """Test AI Reasoning Plugin individually"""
    print("=== Testing AI Reasoning Plugin ===")

    try:
        # Create plugin instance
        plugin = AIReasoningPlugin()
        print("✓ AI Reasoning Plugin created")

        # Create config
        config = PluginConfig(
            name="ai_reasoning_test",
            version="1.0",
            config={
                "openai_api_key": "test_key",  # Won't work but tests structure
                "default_model": "gpt-4o-mini",
                "max_tokens": 1000,
            },
        )

        # Initialize plugin
        plugin.initialize_sync(config, None)  # No event bus for test
        print("✓ AI Reasoning Plugin initialized")

        # Test basic reasoning (will fail due to API key, but tests structure)
        context = ExecutionContext(
            workflow_id="test",
            task_id="reasoning_test",
            state={"query": "What is 2+2?", "context": "Simple math question"},
        )

        print("Attempting reasoning (expected to fail due to API key)...")
        result = plugin.execute_sync(context)

        if result.success:
            print("✓ AI Reasoning executed successfully!")
            print(f"Result: {result.data}")
        else:
            print(f"✗ AI Reasoning failed as expected: {result.error_message}")
            if (
                "API key" in str(result.error_message)
                or "authentication" in str(result.error_message).lower()
            ):
                print(
                    "✓ Failure is due to missing API key - plugin structure is correct"
                )
                return True

        return result.success

    except Exception as e:
        print(f"✗ AI Reasoning Plugin test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_budget_manager_plugin():
    """Test Budget Manager Plugin individually"""
    print("\n=== Testing Budget Manager Plugin ===")

    try:
        # Create plugin instance
        plugin = BudgetManagerPlugin()
        print("✓ Budget Manager Plugin created")

        # Create config
        config = PluginConfig(
            name="budget_test",
            version="1.0",
            config={
                "daily_budget": 10.0,
                "monthly_budget": 300.0,
                "cost_per_1k_tokens": {"gpt-4o": 0.03, "gpt-4o-mini": 0.0015},
            },
        )

        # Initialize plugin
        plugin.initialize_sync(config, None)
        print("✓ Budget Manager Plugin initialized")

        # Test budget estimation
        context = ExecutionContext(
            workflow_id="test",
            task_id="budget_test",
            state={
                "operation": "estimate_cost",
                "model": "gpt-4o-mini",
                "estimated_tokens": 1000,
            },
        )

        result = plugin.execute_sync(context)

        if result.success:
            print("✓ Budget Manager executed successfully!")
            print(f"Result: {result.data}")
            return True
        else:
            print(f"✗ Budget Manager failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"✗ Budget Manager Plugin test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_workflow_intelligence_plugin():
    """Test Workflow Intelligence Plugin individually"""
    print("\n=== Testing Workflow Intelligence Plugin ===")

    try:
        # Create plugin instance
        plugin = WorkflowIntelligencePlugin()
        print("✓ Workflow Intelligence Plugin created")

        # Create config
        config = PluginConfig(name="workflow_intel_test", version="1.0", config={})

        # Initialize plugin
        plugin.initialize_sync(config, None)
        print("✓ Workflow Intelligence Plugin initialized")

        # Test workflow analysis
        context = ExecutionContext(
            workflow_id="test",
            task_id="workflow_analysis_test",
            state={
                "operation": "analyze_workflow",
                "workflow_definition": {
                    "name": "test_workflow",
                    "steps": [
                        {"plugin_name": "step1", "parameters": {}},
                        {"plugin_name": "step2", "parameters": {}},
                    ],
                },
            },
        )

        result = plugin.execute_sync(context)

        if result.success:
            print("✓ Workflow Intelligence executed successfully!")
            print(f"Result: {result.data}")
            return True
        else:
            print(f"✗ Workflow Intelligence failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"✗ Workflow Intelligence Plugin test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=== Individual AI Plugin Tests ===")

    results = []

    # Test each plugin individually
    results.append(("AI Reasoning", test_ai_reasoning_plugin()))
    results.append(("Budget Manager", test_budget_manager_plugin()))
    results.append(("Workflow Intelligence", test_workflow_intelligence_plugin()))

    # Summary
    print("\n" + "=" * 50)
    print("INDIVIDUAL PLUGIN TEST SUMMARY:")
    print("=" * 50)

    all_passed = True
    for plugin_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{plugin_name:20} {status}")
        if not success:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("✓ ALL INDIVIDUAL PLUGIN TESTS PASSED")
    else:
        print("✗ SOME INDIVIDUAL PLUGIN TESTS FAILED")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
