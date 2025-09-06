#!/usr/bin/env python3
"""
Workflow Templates Validation Script

Validates that all workflow templates are properly configured and can be instantiated.
Run this script to verify the workflow system is working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.orchestration.sleuth_orchestrator import (
        SleuthIntelOrchestrator,
        WorkflowConfig,
        WorkflowType,
    )
    from src.orchestration.workflow_templates import (
        InvestigationDepth,
        OutputFormat,
        WorkflowBudget,
        WorkflowCustomization,
        WorkflowTemplateManager,
        address_analysis_workflow,
        bulk_processing_workflow,
        business_due_diligence_workflow,
        person_investigation_workflow,
        phone_investigation_workflow,
    )

    print("✓ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Make sure you're running from the sleuth-intel directory")
    sys.exit(1)


def validate_enums():
    """Validate that all enums have expected values"""
    print("\n📋 Validating Enums...")

    # InvestigationDepth
    expected_depths = ["basic", "comprehensive", "deep", "forensic"]
    actual_depths = [d.value for d in InvestigationDepth]
    assert set(expected_depths).issubset(
        set(actual_depths)
    ), f"Missing depths: {set(expected_depths) - set(actual_depths)}"
    print("✓ InvestigationDepth enum valid")

    # OutputFormat
    expected_formats = ["json", "pdf", "csv", "html", "markdown"]
    actual_formats = [f.value for f in OutputFormat]
    assert set(expected_formats).issubset(
        set(actual_formats)
    ), f"Missing formats: {set(expected_formats) - set(actual_formats)}"
    print("✓ OutputFormat enum valid")

    # WorkflowType
    expected_types = [
        "single_source",
        "multi_source_parallel",
        "investigation_chain",
        "bulk_processing",
        "adaptive_enrichment",
    ]
    actual_types = [t.value for t in WorkflowType]
    assert set(expected_types).issubset(
        set(actual_types)
    ), f"Missing types: {set(expected_types) - set(actual_types)}"
    print("✓ WorkflowType enum valid")


def validate_data_classes():
    """Validate that data classes can be instantiated"""
    print("\n🏗️  Validating Data Classes...")

    # WorkflowBudget
    budget = WorkflowBudget(max_cost_usd=10.00, max_time_minutes=15, max_credits=100)
    assert budget.max_cost_usd == 10.00
    print("✓ WorkflowBudget instantiated")

    # WorkflowCustomization
    customization = WorkflowCustomization(
        skip_agents=["email_search_agent"],
        additional_agents=["analysis_agent"],
        custom_config={"max_parallel_agents": 5},
    )
    assert "email_search_agent" in customization.skip_agents
    print("✓ WorkflowCustomization instantiated")

    # WorkflowConfig
    config = WorkflowConfig(
        max_parallel_agents=3, timeout_seconds=120, enable_caching=True
    )
    assert config.max_parallel_agents == 3
    print("✓ WorkflowConfig instantiated")


def validate_orchestrator():
    """Validate orchestrator can be instantiated"""
    print("\n🎯 Validating Orchestrator...")

    try:
        orchestrator = SleuthIntelOrchestrator()
        print("✓ SleuthIntelOrchestrator instantiated")

        # Test workflow template manager
        manager = WorkflowTemplateManager(orchestrator)
        print("✓ WorkflowTemplateManager instantiated")

        # Check templates are loaded
        templates = manager.get_available_templates()
        expected_template_types = [
            "phone_investigation",
            "person_investigation",
            "business_due_diligence",
            "address_analysis",
            "bulk_processing",
        ]

        for template_type in expected_template_types:
            assert template_type in templates, f"Missing template: {template_type}"

            # Check depths available
            for depth in ["basic", "comprehensive", "deep"]:
                assert (
                    depth in templates[template_type]
                ), f"Missing depth {depth} in {template_type}"

        print(f"✓ All {len(expected_template_types)} workflow templates loaded")
        print(f"✓ Templates have required depths: basic, comprehensive, deep")

    except Exception as e:
        print(f"❌ Orchestrator validation failed: {e}")
        return False

    return True


def validate_cost_estimation():
    """Validate cost estimation functionality"""
    print("\n💰 Validating Cost Estimation...")

    try:
        orchestrator = SleuthIntelOrchestrator()
        manager = WorkflowTemplateManager(orchestrator)

        # Test cost estimation for each template type
        test_cases = [
            ("phone_investigation", "basic", 1),
            ("person_investigation", "comprehensive", 1),
            ("business_due_diligence", "deep", 1),
            ("bulk_processing", "basic", 10),
        ]

        for template_type, depth, record_count in test_cases:
            estimate = manager.estimate_workflow_cost(
                template_type, depth, record_count
            )

            # Validate estimate structure
            required_keys = [
                "base_cost",
                "time_cost",
                "total_estimated_cost",
                "per_record_cost",
            ]
            for key in required_keys:
                assert key in estimate, f"Missing key {key} in cost estimate"

            # Validate values are reasonable
            assert estimate["total_estimated_cost"] > 0, "Total cost should be positive"
            assert estimate["per_record_cost"] > 0, "Per record cost should be positive"

        print("✓ Cost estimation working for all template types")

    except Exception as e:
        print(f"❌ Cost estimation validation failed: {e}")
        return False

    return True


def validate_template_structure():
    """Validate that all templates have proper structure"""
    print("\n🏗️  Validating Template Structure...")

    try:
        orchestrator = SleuthIntelOrchestrator()
        manager = WorkflowTemplateManager(orchestrator)

        templates = manager.get_available_templates()

        for template_type, depths in templates.items():
            print(f"  Validating {template_type}...")

            for depth, template_info in depths.items():
                # Check required fields
                required_fields = [
                    "name",
                    "description",
                    "estimated_cost",
                    "estimated_time_minutes",
                    "required_agents",
                    "optional_agents",
                ]

                for field in required_fields:
                    assert (
                        field in template_info
                    ), f"Missing field {field} in {template_type}/{depth}"

                # Validate field types
                assert isinstance(
                    template_info["estimated_cost"], (int, float)
                ), "estimated_cost should be numeric"
                assert isinstance(
                    template_info["estimated_time_minutes"], int
                ), "estimated_time_minutes should be int"
                assert isinstance(
                    template_info["required_agents"], list
                ), "required_agents should be list"
                assert isinstance(
                    template_info["optional_agents"], list
                ), "optional_agents should be list"

                # Validate agents are strings
                for agent in (
                    template_info["required_agents"] + template_info["optional_agents"]
                ):
                    assert isinstance(
                        agent, str
                    ), f"Agent name should be string: {agent}"

            print(f"    ✓ {len(depths)} depths validated")

        print("✓ All template structures valid")

    except Exception as e:
        print(f"❌ Template structure validation failed: {e}")
        return False

    return True


def validate_workflow_functions():
    """Validate that workflow functions are properly defined"""
    print("\n⚙️  Validating Workflow Functions...")

    # Check function signatures
    workflow_functions = [
        phone_investigation_workflow,
        person_investigation_workflow,
        business_due_diligence_workflow,
        address_analysis_workflow,
        bulk_processing_workflow,
    ]

    for func in workflow_functions:
        assert callable(func), f"{func.__name__} is not callable"
        assert hasattr(func, "__doc__"), f"{func.__name__} missing docstring"
        print(f"✓ {func.__name__} properly defined")

    print("✓ All workflow functions validated")


def run_integration_test():
    """Run a simple integration test"""
    print("\n🧪 Running Integration Test...")

    try:
        # Test template instantiation
        orchestrator = SleuthIntelOrchestrator()
        manager = WorkflowTemplateManager(orchestrator)

        # Test cost estimation
        estimate = manager.estimate_workflow_cost("phone_investigation", "basic", 1)
        assert estimate["total_estimated_cost"] > 0

        # Test customization
        customization = WorkflowCustomization(custom_config={"max_parallel_agents": 2})

        # Test budget
        budget = WorkflowBudget(max_cost_usd=5.00)

        print("✓ Integration test passed")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

    return True


def main():
    """Run all validation tests"""
    print("SLEUTH INTEL WORKFLOW TEMPLATES VALIDATION")
    print("=" * 50)

    all_passed = True

    try:
        validate_enums()
        validate_data_classes()

        if not validate_orchestrator():
            all_passed = False

        if not validate_cost_estimation():
            all_passed = False

        if not validate_template_structure():
            all_passed = False

        validate_workflow_functions()

        if not run_integration_test():
            all_passed = False

    except Exception as e:
        print(f"❌ Validation failed with exception: {e}")
        all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\nWorkflow templates are ready for use.")
        print("\nNext steps:")
        print("- Run: python examples/simple_workflow_demo.py")
        print("- Try: python examples/workflow_usage_examples.py interactive")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("\nPlease fix the issues above before using workflow templates.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
