#!/usr/bin/env python3
"""
Demonstrate cognitive enhancement using the ASEA Orchestrator
"""
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from asea_orchestrator.core import Orchestrator
from asea_orchestrator.workflow import WorkflowManager
from asea_orchestrator.plugins.types import PluginConfig


def create_cognitive_enhancement_workflow():
    """Create a workflow that demonstrates cognitive enhancement through multiple AI plugins"""

    workflow_definitions = {
        "cognitive_enhancement_demo": {
            "steps": [
                {
                    "plugin_name": "budget_manager",
                    "parameters": {"operation": "start_session"},
                    "inputs": {},
                    "outputs": {"budget_status": "initial_budget"},
                },
                {
                    "plugin_name": "cognitive_pre_analysis",
                    "parameters": {
                        "analysis_type": "request_analysis",
                        "context": "Demonstrate cognitive enhancement capabilities",
                    },
                    "inputs": {"initial_budget": "budget_context"},
                    "outputs": {"analysis_result": "pre_analysis"},
                },
                {
                    "plugin_name": "workflow_intelligence",
                    "parameters": {"operation": "analyze_workflow"},
                    "inputs": {"pre_analysis": "context"},
                    "outputs": {"workflow_analysis": "intelligence_analysis"},
                },
                {
                    "plugin_name": "cognitive_critic",
                    "parameters": {
                        "critique_type": "analysis_review",
                        "focus": "cognitive_enhancement_effectiveness",
                    },
                    "inputs": {"intelligence_analysis": "analysis_to_critique"},
                    "outputs": {"critique_result": "critic_feedback"},
                },
                {
                    "plugin_name": "budget_manager",
                    "parameters": {"operation": "final_report"},
                    "inputs": {"critic_feedback": "session_context"},
                    "outputs": {"final_budget": "budget_summary"},
                },
            ]
        }
    }

    return workflow_definitions


async def demonstrate_cognitive_enhancement():
    """Run the cognitive enhancement demonstration"""
    print("=== COGNITIVE ENHANCEMENT DEMONSTRATION ===")

    # Setup
    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )
    workflow_definitions = create_cognitive_enhancement_workflow()

    workflow_manager = WorkflowManager(workflow_definitions)
    orchestrator = Orchestrator(
        plugin_dir=plugin_dir, workflow_manager=workflow_manager
    )

    # Configure plugins
    plugin_configs = {
        "budget_manager": PluginConfig(
            name="budget_demo",
            version="1.0",
            config={"daily_budget": 5.0, "cost_per_1k_tokens": {"gpt-4o-mini": 0.0015}},
        ),
        "cognitive_pre_analysis": PluginConfig(
            name="pre_analysis_demo",
            version="1.0",
            config={"analysis_depth": "comprehensive"},
        ),
        "workflow_intelligence": PluginConfig(
            name="workflow_intel_demo", version="1.0", config={"learning_enabled": True}
        ),
        "cognitive_critic": PluginConfig(
            name="critic_demo", version="1.0", config={"critique_style": "constructive"}
        ),
    }

    orchestrator.temp_configure_plugins(plugin_configs)

    # Execute workflow
    print("\nExecuting cognitive enhancement workflow...")
    print(
        "This demonstrates multiple AI plugins working together for compound cognitive effects"
    )

    try:
        result = await orchestrator.run_workflow(
            "cognitive_enhancement_demo",
            {
                "user_request": "Demonstrate how multiple AI plugins can enhance cognitive processing",
                "enhancement_goal": "Show compound intelligence effects",
            },
        )

        print(f"\n✓ Cognitive enhancement workflow completed successfully!")
        print("\nWorkflow Results:")
        for key, value in result.items():
            if key != "run_id":
                print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"\n✗ Cognitive enhancement workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def demonstrate_simple_ai_workflow():
    """Run a simpler workflow to show basic AI plugin coordination"""
    print("\n=== SIMPLE AI COORDINATION DEMONSTRATION ===")

    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )

    simple_workflow = {
        "ai_coordination_demo": {
            "steps": [
                {
                    "plugin_name": "budget_manager",
                    "parameters": {
                        "operation": "estimate_cost",
                        "model": "gpt-4o-mini",
                        "estimated_tokens": 500,
                    },
                    "inputs": {},
                    "outputs": {"cost_estimate": "budget_estimate"},
                },
                {
                    "plugin_name": "workflow_intelligence",
                    "parameters": {"operation": "analyze_workflow"},
                    "inputs": {"budget_estimate": "cost_context"},
                    "outputs": {"analysis": "workflow_analysis"},
                },
            ]
        }
    }

    workflow_manager = WorkflowManager(simple_workflow)
    orchestrator = Orchestrator(
        plugin_dir=plugin_dir, workflow_manager=workflow_manager
    )

    # Configure plugins
    configs = {
        "budget_manager": PluginConfig(
            name="simple_budget",
            version="1.0",
            config={
                "daily_budget": 10.0,
                "cost_per_1k_tokens": {"gpt-4o-mini": 0.0015},
            },
        ),
        "workflow_intelligence": PluginConfig(
            name="simple_workflow", version="1.0", config={}
        ),
    }

    orchestrator.temp_configure_plugins(configs)

    try:
        result = await orchestrator.run_workflow(
            "ai_coordination_demo", {"task": "Demonstrate AI plugin coordination"}
        )

        print(f"✓ AI coordination workflow completed!")
        print(f"Budget Analysis: {result.get('budget_estimate', 'Not available')}")
        print(
            f"Workflow Intelligence: {result.get('workflow_analysis', 'Not available')}"
        )

        return True

    except Exception as e:
        print(f"✗ Simple workflow failed: {e}")
        return False


async def main():
    """Main demonstration function"""
    print("ASEA Orchestrator Cognitive Enhancement Demonstration")
    print("=" * 60)

    # Run simple demonstration first
    simple_success = await demonstrate_simple_ai_workflow()

    if simple_success:
        print("\n" + "=" * 60)
        # Run advanced cognitive enhancement demonstration
        advanced_success = await demonstrate_cognitive_enhancement()

        if advanced_success:
            print("\n" + "=" * 60)
            print("🎉 DEMONSTRATION COMPLETE: ASEA Orchestrator successfully")
            print("   coordinates multiple AI plugins for cognitive enhancement!")
            print("\nKey Capabilities Demonstrated:")
            print("✓ Budget-aware AI operations")
            print("✓ Workflow intelligence and optimization")
            print("✓ Multi-plugin cognitive processing")
            print("✓ Distributed task execution")
            print("✓ Compound AI effects through orchestration")
        else:
            print("\n⚠️  Advanced workflow had issues, but basic coordination works")
    else:
        print("\n❌ Basic workflow failed - orchestrator may need debugging")


if __name__ == "__main__":
    asyncio.run(main())
