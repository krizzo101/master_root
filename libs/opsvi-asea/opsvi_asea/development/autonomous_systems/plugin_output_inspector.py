#!/usr/bin/env python3
"""
Plugin Output Inspector - Check what the plugins are actually returning
"""

import json
from cognitive_enhancement_orchestrator import enhance_decision_making


def inspect_plugin_outputs():
    """Inspect what the budget_manager and workflow_intelligence plugins actually return"""

    print("🔍 PLUGIN OUTPUT INSPECTION")
    print("=" * 50)

    # Simple test context
    test_context = {
        "decision_options": [
            {"name": "Option A", "cost": 10000},
            {"name": "Option B", "cost": 20000},
        ],
        "budget_context": {
            "available_budget": 15000,
            "cost_categories": ["development", "testing"],
        },
    }

    print("Test Context:")
    print(json.dumps(test_context, indent=2))

    print("\n" + "=" * 50)
    print("RUNNING COGNITIVE ENHANCEMENT...")

    result = enhance_decision_making(test_context)

    print("\n" + "=" * 50)
    print("DETAILED PLUGIN OUTPUTS:")

    print(f"\nFull Result Structure:")
    print(json.dumps(result, indent=2))

    print(f"\n🔍 ANALYSIS:")
    print(f"Enhancement Applied: {result.get('cognitive_enhancement_applied', False)}")

    budget_analysis = result.get("budget_analysis", {})
    print(f"Budget Analysis: {budget_analysis}")
    print(f"Budget Analysis Type: {type(budget_analysis)}")
    print(f"Budget Analysis Empty: {len(str(budget_analysis)) == 0}")

    workflow_opt = result.get("workflow_optimization", {})
    print(f"Workflow Optimization: {workflow_opt}")
    print(f"Workflow Optimization Type: {type(workflow_opt)}")
    print(f"Workflow Optimization Empty: {len(str(workflow_opt)) == 0}")

    recommendations = result.get("enhanced_recommendations", [])
    print(f"Enhanced Recommendations: {recommendations}")
    print(f"Number of Recommendations: {len(recommendations)}")

    # Check if plugins are returning meaningful data or just defaults
    if not budget_analysis and not workflow_opt:
        print("\n❌ PLUGINS RETURNING EMPTY RESULTS")
        print("The plugins may not be providing real analysis")
    elif budget_analysis == {} and workflow_opt == {}:
        print("\n❌ PLUGINS RETURNING EMPTY DICTIONARIES")
        print("The plugins are executing but not returning meaningful data")
    else:
        print("\n✅ PLUGINS RETURNING DATA")
        print("Need to verify if data is meaningful or generic")


if __name__ == "__main__":
    inspect_plugin_outputs()
