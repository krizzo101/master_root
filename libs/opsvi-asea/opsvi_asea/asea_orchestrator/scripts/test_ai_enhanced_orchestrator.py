#!/usr/bin/env python3
"""
Test script for AI-enhanced orchestrator functionality.
Validates budget management, AI reasoning, and workflow intelligence.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asea_orchestrator.plugins.types import PluginConfig, ExecutionContext
from asea_orchestrator.plugins.available.budget_manager_plugin import (
    BudgetManagerPlugin,
)
from asea_orchestrator.plugins.available.ai_reasoning_plugin import AIReasoningPlugin
from asea_orchestrator.plugins.available.workflow_intelligence_plugin import (
    WorkflowIntelligencePlugin,
)


async def test_budget_manager():
    """Test Budget Manager Plugin functionality."""
    print("\\n=== Testing Budget Manager Plugin ===")

    # Initialize plugin
    plugin = BudgetManagerPlugin()
    config = PluginConfig(
        name="budget_manager",
        config={
            "budget_limits": {
                "daily_limit_usd": 5.0,
                "weekly_limit_usd": 25.0,
                "monthly_limit_usd": 100.0,
                "model_preferences": {
                    "reasoning": "o4-mini",
                    "simple": "gpt-4.1-nano",
                    "complex": "gpt-4.1",
                    "default": "gpt-4.1-mini",
                },
            }
        },
    )

    await plugin.initialize(config)

    # Test 1: Get usage stats
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={"action": "get_usage_stats"},
    )
    result = await plugin.execute(context)
    print(f"✓ Usage Stats: {result.success}")
    if result.success:
        print(f"  Daily Limit: ${result.data['daily_limit']}")
        print(f"  Current Usage: ${result.data['current_daily_usage']}")
        print(f"  Remaining: ${result.data['remaining_daily_budget']}")

    # Test 2: Cost estimation
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "estimate_cost",
            "model": "gpt-4.1-mini",
            "input_tokens": 1000,
            "estimated_output_tokens": 500,
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Cost Estimation: {result.success}")
    if result.success:
        print(f"  Estimated Cost: ${result.data['total_estimated_cost_usd']:.4f}")

    # Test 3: Budget check
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "check_budget",
            "estimated_cost_usd": 0.001,
            "period": "daily",
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Budget Check: {result.success}")
    if result.success:
        print(f"  Can Proceed: {result.data['can_proceed']}")
        print(f"  Remaining Budget: ${result.data['remaining_budget']}")

    # Test 4: Model recommendation
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "get_recommended_model",
            "task_type": "reasoning",
            "max_cost_usd": 0.01,
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Model Recommendation: {result.success}")
    if result.success:
        print(f"  Recommended Model: {result.data['recommended_model']}")
        print(f"  Reasoning: {result.data['reasoning']}")

    await plugin.cleanup()
    return True


async def test_ai_reasoning():
    """Test AI Reasoning Plugin functionality."""
    print("\\n=== Testing AI Reasoning Plugin ===")

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ Skipping AI Reasoning tests - OPENAI_API_KEY not set")
        return True

    # Initialize plugin
    plugin = AIReasoningPlugin()
    config = PluginConfig(
        name="ai_reasoning",
        config={
            "openai_api_key": api_key,
            "models": {
                "default": "gpt-4.1-mini",
                "reasoning": "o4-mini",
                "complex": "gpt-4.1",
            },
        },
    )

    try:
        await plugin.initialize(config)

        # Test 1: Basic reasoning
        context = ExecutionContext(
            workflow_id="test_workflow",
            task_id="test_task",
            state={
                "action": "reason",
                "prompt": "What are the key factors to consider when optimizing a workflow?",
                "context": {"workflow_type": "data_processing"},
                "max_tokens": 500,
            },
        )
        result = await plugin.execute(context)
        print(f"✓ Basic Reasoning: {result.success}")
        if result.success:
            print(f"  Model Used: {result.data['model_used']}")
            print(f"  Tokens Used: {result.data['tokens_used']['total']}")
            print(f"  Reasoning Preview: {result.data['reasoning'][:100]}...")
        else:
            print(f"  Error: {result.error_message}")

        # Test 2: Plugin selection
        context = ExecutionContext(
            workflow_id="test_workflow",
            task_id="test_task",
            state={
                "action": "select_plugins",
                "objective": "Search for information about AI trends and save results to database",
                "available_plugins": [
                    "web_search",
                    "arango_db",
                    "text_processing",
                    "file_system",
                ],
                "context": {"data_source": "web", "storage": "database"},
            },
        )
        result = await plugin.execute(context)
        print(f"✓ Plugin Selection: {result.success}")
        if result.success and "plugin_selection" in result.data:
            selection = result.data["plugin_selection"]
            if "selected_plugins" in selection:
                print(f"  Selected Plugins: {selection['selected_plugins']}")

        # Test 3: Error analysis
        context = ExecutionContext(
            workflow_id="test_workflow",
            task_id="test_task",
            state={
                "action": "analyze_error",
                "error_message": "Connection timeout: Unable to reach external API",
                "plugin_name": "web_search",
                "execution_context": {"timeout": 30, "retries": 3},
                "workflow_state": {"step": 2, "total_steps": 5},
            },
        )
        result = await plugin.execute(context)
        print(f"✓ Error Analysis: {result.success}")
        if result.success and "error_analysis" in result.data:
            analysis = result.data["error_analysis"]
            if "error_type" in analysis:
                print(f"  Error Type: {analysis['error_type']}")
                print(
                    f"  Retry Recommended: {analysis.get('retry_recommended', 'N/A')}"
                )

        await plugin.cleanup()
        return True

    except Exception as e:
        print(f"✗ AI Reasoning test failed: {str(e)}")
        await plugin.cleanup()
        return False


async def test_workflow_intelligence():
    """Test Workflow Intelligence Plugin functionality."""
    print("\\n=== Testing Workflow Intelligence Plugin ===")

    # Initialize plugin
    plugin = WorkflowIntelligencePlugin()
    config = PluginConfig(
        name="workflow_intelligence", config={"learning_enabled": True}
    )

    await plugin.initialize(config)

    # Test 1: Workflow analysis
    sample_workflow = {
        "name": "data_processing_workflow",
        "steps": [
            {"plugin_name": "web_search", "inputs": {}, "outputs": {}},
            {"plugin_name": "text_processing", "inputs": {}, "outputs": {}},
            {"plugin_name": "arango_db", "inputs": {}, "outputs": {}},
        ],
    }

    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "analyze",
            "workflow_definition": sample_workflow,
            "execution_data": {},
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Workflow Analysis: {result.success}")
    if result.success:
        analysis = result.data["workflow_analysis"]
        characteristics = analysis["workflow_characteristics"]
        print(f"  Step Count: {characteristics['step_count']}")
        print(f"  Complexity Score: {characteristics['complexity_score']}")
        print(f"  Estimated Duration: {characteristics['estimated_duration_seconds']}s")
        print(f"  Risk Factors: {len(characteristics['risk_factors'])}")

    # Test 2: Record execution
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "record_execution",
            "workflow_name": "data_processing_workflow",
            "execution_time": 45.5,
            "success": True,
            "step_results": [
                {"success": True, "duration": 15.0},
                {"success": True, "duration": 20.0},
                {"success": True, "duration": 10.5},
            ],
            "resource_usage": {"cpu": 0.3, "memory": 0.2},
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Record Execution: {result.success}")
    if result.success:
        print(f"  Executions Recorded: {result.data['total_executions_recorded']}")

    # Test 3: Performance prediction
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={"action": "predict_performance", "workflow_definition": sample_workflow},
    )
    result = await plugin.execute(context)
    print(f"✓ Performance Prediction: {result.success}")
    if result.success:
        prediction = result.data["prediction"]
        print(f"  Confidence: {prediction.get('confidence_score', 'N/A')}")
        print(
            f"  Predicted Duration: {prediction.get('predicted_duration_seconds', 'N/A')}s"
        )

    # Test 4: Optimization recommendations
    context = ExecutionContext(
        workflow_id="test_workflow",
        task_id="test_task",
        state={
            "action": "recommend_optimizations",
            "workflow_definition": sample_workflow,
            "performance_target": "balanced",
        },
    )
    result = await plugin.execute(context)
    print(f"✓ Optimization Recommendations: {result.success}")
    if result.success:
        recommendations = result.data["recommendations"]
        print(f"  Total Recommendations: {len(recommendations)}")
        if recommendations:
            print(f"  Top Recommendation: {recommendations[0]['description']}")

    await plugin.cleanup()
    return True


async def test_plugin_integration():
    """Test integration between AI plugins."""
    print("\\n=== Testing Plugin Integration ===")

    # Test budget-aware AI reasoning
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ Skipping integration tests - OPENAI_API_KEY not set")
        return True

    # Initialize plugins
    budget_plugin = BudgetManagerPlugin()
    ai_plugin = AIReasoningPlugin()

    budget_config = PluginConfig(
        name="budget_manager",
        config={
            "budget_limits": {
                "daily_limit_usd": 1.0,
                "model_preferences": {"default": "gpt-4.1-nano"},
            }
        },
    )

    ai_config = PluginConfig(
        name="ai_reasoning",
        config={"openai_api_key": api_key, "models": {"default": "gpt-4.1-nano"}},
    )

    await budget_plugin.initialize(budget_config)
    await ai_plugin.initialize(ai_config)

    try:
        # Step 1: Get model recommendation from budget manager
        context = ExecutionContext(
            workflow_id="integration_test",
            task_id="step1",
            state={
                "action": "get_recommended_model",
                "task_type": "simple",
                "max_cost_usd": 0.01,
            },
        )
        budget_result = await budget_plugin.execute(context)
        print(f"✓ Budget Model Recommendation: {budget_result.success}")

        if budget_result.success:
            recommended_model = budget_result.data["recommended_model"]
            print(f"  Recommended Model: {recommended_model}")

            # Step 2: Use recommended model for AI reasoning
            context = ExecutionContext(
                workflow_id="integration_test",
                task_id="step2",
                state={
                    "action": "reason",
                    "prompt": "Briefly explain the benefits of workflow automation.",
                    "model": recommended_model,
                    "max_tokens": 200,
                },
            )
            ai_result = await ai_plugin.execute(context)
            print(f"✓ AI Reasoning with Budget Model: {ai_result.success}")

            if ai_result.success:
                tokens_used = ai_result.data["tokens_used"]
                print(f"  Tokens Used: {tokens_used['total']}")

                # Step 3: Record usage in budget manager
                context = ExecutionContext(
                    workflow_id="integration_test",
                    task_id="step3",
                    state={
                        "action": "record_usage",
                        "model": recommended_model,
                        "input_tokens": tokens_used["input"],
                        "output_tokens": tokens_used["output"],
                    },
                )
                record_result = await budget_plugin.execute(context)
                print(f"✓ Usage Recording: {record_result.success}")

                if record_result.success:
                    print(
                        f"  Daily Total Cost: ${record_result.data['daily_total_cost']:.6f}"
                    )
                    print(
                        f"  Remaining Budget: ${record_result.data['remaining_daily_budget']:.6f}"
                    )

        await budget_plugin.cleanup()
        await ai_plugin.cleanup()
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {str(e)}")
        await budget_plugin.cleanup()
        await ai_plugin.cleanup()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting AI-Enhanced Orchestrator Tests")
    print("=" * 50)

    tests = [
        ("Budget Manager", test_budget_manager),
        ("AI Reasoning", test_ai_reasoning),
        ("Workflow Intelligence", test_workflow_intelligence),
        ("Plugin Integration", test_plugin_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! AI-Enhanced Orchestrator is ready.")
        return 0
    else:
        print("⚠ Some tests failed. Check configuration and dependencies.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
