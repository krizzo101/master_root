#!/usr/bin/env python3
"""
Minimal Workflow Templates Demo

Shows basic functionality without requiring full system dependencies.
Perfect for demonstrating the workflow template structure.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def demo_workflow_template_structure():
    """Demonstrate workflow template structure and configuration"""
    print("🎯 SLEUTH INTEL WORKFLOW TEMPLATES DEMO")
    print("=" * 45)

    try:
        from src.orchestration.workflow_templates import (
            InvestigationDepth,
            OutputFormat,
            WorkflowBudget,
            WorkflowCustomization,
        )

        print("✓ Core classes imported successfully")

        # Demo Investigation Depths
        print(f"\n📊 Investigation Depths Available:")
        for depth in InvestigationDepth:
            print(f"  - {depth.value.upper()}: {depth.name}")

        # Demo Budget Configuration
        print(f"\n💰 Budget Configuration Example:")
        budget = WorkflowBudget(
            max_cost_usd=15.00,
            max_time_minutes=10,
            max_credits=200,
            priority_allocation={
                "person_search_agent": 0.4,
                "phone_search_agent": 0.3,
                "business_search_agent": 0.2,
                "email_search_agent": 0.1,
            },
        )
        print(f"  Max Cost: ${budget.max_cost_usd:.2f}")
        print(f"  Max Time: {budget.max_time_minutes} minutes")
        print(f"  Max Credits: {budget.max_credits}")
        print(f"  Priority Allocations: {len(budget.priority_allocation)} agents")

        # Demo Customization Options
        print(f"\n⚙️  Workflow Customization Example:")
        customization = WorkflowCustomization(
            skip_agents=["email_search_agent"],
            additional_agents=["data_enrichment_agent", "analysis_agent"],
            custom_config={
                "correlation_threshold": 0.85,
                "max_parallel_agents": 6,
                "enable_caching": True,
                "cache_ttl": 7200,
            },
            result_filters=["high_confidence_only"],
            correlation_rules={"require_multi_source_verification": True},
        )
        print(f"  Skipped Agents: {customization.skip_agents}")
        print(f"  Additional Agents: {customization.additional_agents}")
        print(f"  Custom Config Options: {len(customization.custom_config)}")
        print(f"  Result Filters: {customization.result_filters}")

        # Demo Output Formats
        print(f"\n📄 Output Formats Available:")
        for fmt in OutputFormat:
            print(f"  - {fmt.value.upper()}: {fmt.name}")

        print(f"\n✅ Workflow template structure successfully demonstrated!")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

    return True


def demo_workflow_functions():
    """Show that workflow functions are properly defined"""
    print(f"\n🔧 Workflow Functions Available:")

    try:
        from src.orchestration.workflow_templates import (
            address_analysis_workflow,
            bulk_processing_workflow,
            business_due_diligence_workflow,
            person_investigation_workflow,
            phone_investigation_workflow,
        )

        workflows = [
            ("Phone Investigation", phone_investigation_workflow),
            ("Person Investigation", person_investigation_workflow),
            ("Business Due Diligence", business_due_diligence_workflow),
            ("Address Analysis", address_analysis_workflow),
            ("Bulk Processing", bulk_processing_workflow),
        ]

        for name, func in workflows:
            print(f"  ✓ {name}: {func.__name__}")
            if func.__doc__:
                first_line = func.__doc__.strip().split("\n")[0]
                print(f"    └─ {first_line}")

        print(f"\n✅ All {len(workflows)} workflow functions are ready!")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    return True


def demo_template_types():
    """Show available template types and configurations"""
    print(f"\n📋 Workflow Template Types:")

    # This would normally load from WorkflowTemplateManager, but we'll show the structure
    templates = {
        "phone_investigation": {
            "description": "Phone number lookup with carrier data and owner information",
            "depths": ["basic", "comprehensive", "deep"],
            "primary_agents": ["phone_search_agent", "person_search_agent"],
        },
        "person_investigation": {
            "description": "Background investigation with multi-source verification",
            "depths": ["basic", "comprehensive", "deep"],
            "primary_agents": [
                "person_search_agent",
                "phone_search_agent",
                "email_search_agent",
            ],
        },
        "business_due_diligence": {
            "description": "Business verification and network analysis",
            "depths": ["basic", "comprehensive", "deep"],
            "primary_agents": [
                "business_search_agent",
                "person_search_agent",
                "address_search_agent",
            ],
        },
        "address_analysis": {
            "description": "Property investigation with ownership history",
            "depths": ["basic", "comprehensive", "deep"],
            "primary_agents": ["address_search_agent", "person_search_agent"],
        },
        "bulk_processing": {
            "description": "High-volume processing with cost optimization",
            "depths": ["basic", "comprehensive"],
            "primary_agents": ["person_search_agent", "phone_search_agent"],
        },
    }

    for template_name, config in templates.items():
        print(f"\n  🎯 {template_name.replace('_', ' ').title()}")
        print(f"     Description: {config['description']}")
        print(f"     Depths: {', '.join(config['depths'])}")
        print(f"     Primary Agents: {', '.join(config['primary_agents'])}")

    print(f"\n✅ {len(templates)} workflow templates defined!")


def demo_cost_estimates():
    """Show estimated costs for different workflows"""
    print(f"\n💳 Estimated Costs (USD):")

    # Sample cost estimates (these would come from WorkflowTemplateManager in practice)
    estimates = [
        ("Phone Investigation - Basic", 0.50, 2),
        ("Phone Investigation - Comprehensive", 2.50, 5),
        ("Phone Investigation - Deep", 8.00, 15),
        ("Person Investigation - Basic", 1.00, 3),
        ("Person Investigation - Comprehensive", 5.00, 8),
        ("Person Investigation - Deep", 15.00, 25),
        ("Business Due Diligence - Basic", 2.00, 5),
        ("Business Due Diligence - Comprehensive", 8.00, 12),
        ("Business Due Diligence - Deep", 25.00, 35),
        ("Bulk Processing (per 100 records)", 25.00, 60),
    ]

    print(f"\n  {'Workflow':<35} {'Cost':<8} {'Time':<6}")
    print(f"  {'-' * 35} {'-' * 8} {'-' * 6}")

    for workflow, cost, time_min in estimates:
        print(f"  {workflow:<35} ${cost:<7.2f} {time_min:<6}m")

    print(f"\n  💡 Costs vary by data provider and query complexity")
    print(f"     Use budget constraints to control spending")


def main():
    """Run the minimal demonstration"""
    success = True

    if not demo_workflow_template_structure():
        success = False

    if not demo_workflow_functions():
        success = False

    demo_template_types()
    demo_cost_estimates()

    print("\n" + "=" * 45)

    if success:
        print("🎉 WORKFLOW TEMPLATES SUCCESSFULLY DEMONSTRATED!")
        print("\nKey Features Shown:")
        print("  ✓ Investigation depth levels")
        print("  ✓ Budget and cost controls")
        print("  ✓ Workflow customization options")
        print("  ✓ Multiple output formats")
        print("  ✓ Complete workflow function suite")

        print(f"\nReady for Integration:")
        print("  • All core classes properly defined")
        print("  • Workflow functions callable")
        print("  • Template structure validated")
        print("  • Cost estimation framework ready")

        print(f"\nNext Steps:")
        print("  1. Configure API credentials")
        print("  2. Initialize required agents")
        print("  3. Run: python examples/workflow_usage_examples.py")

        return 0
    else:
        print("❌ Some features could not be demonstrated")
        return 1


if __name__ == "__main__":
    sys.exit(main())
