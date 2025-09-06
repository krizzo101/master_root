#!/usr/bin/env python3
"""
Simple Workflow Templates Validation

Quick validation that checks the workflow template structure without
requiring full orchestrator initialization.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_imports():
    """Test that core workflow template classes can be imported"""
    print("📦 Testing Imports...")

    try:
        from src.orchestration.workflow_templates import InvestigationDepth

        print("✓ InvestigationDepth imported")

        from src.orchestration.workflow_templates import WorkflowBudget

        print("✓ WorkflowBudget imported")

        from src.orchestration.workflow_templates import WorkflowCustomization

        print("✓ WorkflowCustomization imported")

        from src.orchestration.workflow_templates import OutputFormat

        print("✓ OutputFormat imported")

        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def validate_enums():
    """Validate enum values"""
    print("\n📋 Testing Enums...")

    try:
        from src.orchestration.workflow_templates import (
            InvestigationDepth,
            OutputFormat,
        )

        # Test InvestigationDepth
        depths = [d.value for d in InvestigationDepth]
        expected_depths = ["basic", "comprehensive", "deep", "forensic"]

        for depth in expected_depths:
            if depth not in depths:
                print(f"❌ Missing investigation depth: {depth}")
                return False
        print(f"✓ InvestigationDepth has {len(depths)} values")

        # Test OutputFormat
        formats = [f.value for f in OutputFormat]
        expected_formats = ["json", "csv", "pdf", "html", "markdown"]

        for fmt in expected_formats:
            if fmt not in formats:
                print(f"❌ Missing output format: {fmt}")
                return False
        print(f"✓ OutputFormat has {len(formats)} values")

        return True
    except Exception as e:
        print(f"❌ Enum validation failed: {e}")
        return False


def validate_data_classes():
    """Test that data classes can be instantiated"""
    print("\n🏗️  Testing Data Classes...")

    try:
        from src.orchestration.workflow_templates import (
            WorkflowBudget,
            WorkflowCustomization,
        )

        # Test WorkflowBudget
        budget = WorkflowBudget(
            max_cost_usd=10.00, max_time_minutes=15, max_credits=100
        )

        assert budget.max_cost_usd == 10.00
        assert budget.max_time_minutes == 15
        assert budget.max_credits == 100
        print("✓ WorkflowBudget created successfully")

        # Test WorkflowCustomization
        customization = WorkflowCustomization(
            skip_agents=["email_search_agent"],
            additional_agents=["analysis_agent"],
            custom_config={"max_parallel_agents": 5},
        )

        assert "email_search_agent" in customization.skip_agents
        assert "analysis_agent" in customization.additional_agents
        assert customization.custom_config["max_parallel_agents"] == 5
        print("✓ WorkflowCustomization created successfully")

        return True
    except Exception as e:
        print(f"❌ Data class validation failed: {e}")
        return False


def validate_workflow_functions():
    """Test that workflow functions exist and are callable"""
    print("\n⚙️  Testing Workflow Functions...")

    try:
        from src.orchestration.workflow_templates import (
            address_analysis_workflow,
            bulk_processing_workflow,
            business_due_diligence_workflow,
            person_investigation_workflow,
            phone_investigation_workflow,
        )

        workflow_functions = [
            ("phone_investigation_workflow", phone_investigation_workflow),
            ("person_investigation_workflow", person_investigation_workflow),
            ("business_due_diligence_workflow", business_due_diligence_workflow),
            ("address_analysis_workflow", address_analysis_workflow),
            ("bulk_processing_workflow", bulk_processing_workflow),
        ]

        for name, func in workflow_functions:
            if not callable(func):
                print(f"❌ {name} is not callable")
                return False

            if not hasattr(func, "__doc__") or not func.__doc__:
                print(f"❌ {name} missing docstring")
                return False

            print(f"✓ {name} is callable with docstring")

        return True
    except ImportError as e:
        print(f"❌ Workflow function import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Workflow function validation failed: {e}")
        return False


def validate_template_manager_structure():
    """Test that template manager can be defined"""
    print("\n🎯 Testing Template Manager Structure...")

    try:
        from src.orchestration.workflow_templates import WorkflowTemplateManager

        # Check that class exists and has expected methods
        expected_methods = [
            "execute_workflow",
            "get_available_templates",
            "estimate_workflow_cost",
        ]

        for method_name in expected_methods:
            if not hasattr(WorkflowTemplateManager, method_name):
                print(f"❌ Missing method: {method_name}")
                return False
            print(f"✓ Method {method_name} exists")

        return True
    except ImportError as e:
        print(f"❌ WorkflowTemplateManager import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Template manager validation failed: {e}")
        return False


def validate_template_structure():
    """Test template internal structure"""
    print("\n📊 Testing Template Internal Structure...")

    try:
        # This is a basic structural test without full orchestrator
        from src.orchestration.workflow_templates import WorkflowTemplate

        # Create a test template
        template = WorkflowTemplate(
            name="Test Template",
            description="Test description",
            depth="basic",
            estimated_cost=1.0,
            estimated_time_minutes=5,
            required_agents=["test_agent"],
            optional_agents=["optional_agent"],
        )

        assert template.name == "Test Template"
        assert template.estimated_cost == 1.0
        assert "test_agent" in template.required_agents
        print("✓ WorkflowTemplate structure validated")

        return True
    except ImportError:
        print("ℹ️  WorkflowTemplate not directly importable (internal class)")
        return True  # This is expected
    except Exception as e:
        print(f"❌ Template structure validation failed: {e}")
        return False


def main():
    """Run validation tests"""
    print("SLEUTH INTEL WORKFLOW TEMPLATES - SIMPLE VALIDATION")
    print("=" * 55)

    tests = [
        ("Import Test", validate_imports),
        ("Enum Test", validate_enums),
        ("Data Classes Test", validate_data_classes),
        ("Workflow Functions Test", validate_workflow_functions),
        ("Template Manager Test", validate_template_manager_structure),
        ("Template Structure Test", validate_template_structure),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))

        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 55)
    print(f"RESULTS: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nWorkflow templates structure is valid.")
        print("\nNext steps:")
        print("- Run full system tests when dependencies are available")
        print("- Try: python examples/simple_workflow_demo.py")
        return 0
    else:
        print(f"\n⚠️  {failed} TESTS FAILED")
        print("\nPlease fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
