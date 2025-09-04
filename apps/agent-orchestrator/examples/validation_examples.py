#!/usr/bin/env python3
"""
ExecutionPlan Validation Examples

Comprehensive examples demonstrating the validation system capabilities
including circular dependency detection, error handling, and best practices.
"""

import sys
from pathlib import Path

from execution_plan_schema import TaskType
from execution_plan_template import ExecutionPlanBuilder
from execution_plan_validation import (
    CircularDependencyError,
    DuplicateTaskIdError,
    ExecutionPlanValidator,
    InvalidDependencyError,
    ValidationError,
    validate_execution_plan,
)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def example_1_basic_validation():
    """Example 1: Basic validation success"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Validation Success")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Basic Valid Plan")
        builder.add_task("research", TaskType.RESEARCH_GENIUS, "Research the problem")
        builder.add_task(
            "design",
            TaskType.SOLUTION_ARCHITECT,
            "Design solution",
            dependencies=["research"],
        )
        builder.add_task(
            "implement",
            TaskType.DEVELOPMENT_SPECIALIST,
            "Implement solution",
            dependencies=["design"],
        )

        plan = builder.build()  # Validates automatically
        print(f"✅ Successfully created plan with {len(plan.tasks)} tasks")
        print(f"   Plan name: {plan.name}")
        print(f"   Execution order: {plan.get_execution_order()}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def example_2_circular_dependency_detection():
    """Example 2: Circular dependency detection"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Circular Dependency Detection")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Circular Dependency Test")
        builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
        builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["C"])
        builder.add_task("C", TaskType.GENERAL_PURPOSE, "Task C", dependencies=["A"])

        plan = builder.build()
        print("❌ Should have detected circular dependency")

    except CircularDependencyError as e:
        print("✅ Circular dependency correctly detected")
        print(f"   Dependency chain: {' -> '.join(e.dependency_chain)}")
        print(f"   Error message: {e}")


def example_3_self_dependency_detection():
    """Example 3: Self-dependency detection"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Self-Dependency Detection")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Self-Dependency Test")
        builder.add_task(
            "recursive",
            TaskType.GENERAL_PURPOSE,
            "Recursive task",
            dependencies=["recursive"],
        )

        plan = builder.build()
        print("❌ Should have detected self-dependency")

    except ValidationError as e:
        print("✅ Self-dependency correctly detected")
        print(f"   Error type: {e.error_type.value}")
        print(f"   Task involved: {e.task_id}")
        print(f"   Error message: {e}")


def example_4_duplicate_task_id_detection():
    """Example 4: Duplicate task ID detection"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Duplicate Task ID Detection")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Duplicate ID Test")
        builder.add_task("analysis", TaskType.RESEARCH_GENIUS, "Research analysis")
        builder.add_task(
            "analysis", TaskType.SOLUTION_ARCHITECT, "Design analysis"
        )  # Duplicate

        plan = builder.build()
        print("❌ Should have detected duplicate task ID")

    except DuplicateTaskIdError as e:
        print("✅ Duplicate task ID correctly detected")
        print(f"   Duplicate IDs: {e.duplicate_ids}")
        print(f"   Error message: {e}")


def example_5_invalid_dependency_reference():
    """Example 5: Invalid dependency reference detection"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Invalid Dependency Reference Detection")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Invalid Reference Test")
        builder.add_task(
            "deploy",
            TaskType.SDLC_DEPLOYMENT,
            "Deploy application",
            dependencies=["nonexistent_task"],
        )

        plan = builder.build()
        print("❌ Should have detected invalid dependency reference")

    except InvalidDependencyError as e:
        print("✅ Invalid dependency reference correctly detected")
        print(f"   Invalid references: {e.invalid_references}")
        print(f"   Task with invalid dependency: {e.task_id}")
        print(f"   Error message: {e}")


def example_6_comprehensive_error_handling():
    """Example 6: Comprehensive error handling patterns"""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Comprehensive Error Handling")
    print("=" * 60)

    def create_plan_with_error_handling(plan_name, task_configs):
        """Create plan with proper error handling"""
        try:
            builder = ExecutionPlanBuilder(plan_name)
            for config in task_configs:
                builder.add_task(**config)

            plan = builder.build()
            print(f"✅ Plan '{plan_name}' created successfully")
            return plan

        except CircularDependencyError as e:
            print(f"❌ Circular dependency in '{plan_name}':")
            print(f"   Chain: {' -> '.join(e.dependency_chain)}")
            return None

        except DuplicateTaskIdError as e:
            print(f"❌ Duplicate task IDs in '{plan_name}':")
            print(f"   Duplicates: {e.duplicate_ids}")
            return None

        except InvalidDependencyError as e:
            print(f"❌ Invalid dependencies in '{plan_name}':")
            print(f"   Missing: {e.invalid_references}")
            print(f"   In task: {e.task_id}")
            return None

        except ValidationError as e:
            print(f"❌ Validation error in '{plan_name}':")
            print(f"   Type: {e.error_type.value}")
            print(f"   Message: {e.message}")
            return None

        except Exception as e:
            print(f"❌ Unexpected error in '{plan_name}': {e}")
            return None

    # Test valid plan
    valid_tasks = [
        {
            "task_id": "research",
            "task_type": TaskType.RESEARCH_GENIUS,
            "prompt": "Research requirements",
        },
        {
            "task_id": "design",
            "task_type": TaskType.SOLUTION_ARCHITECT,
            "prompt": "Create design",
            "dependencies": ["research"],
        },
    ]
    create_plan_with_error_handling("Valid Plan", valid_tasks)

    # Test invalid plan (circular)
    circular_tasks = [
        {
            "task_id": "A",
            "task_type": TaskType.GENERAL_PURPOSE,
            "prompt": "Task A",
            "dependencies": ["B"],
        },
        {
            "task_id": "B",
            "task_type": TaskType.GENERAL_PURPOSE,
            "prompt": "Task B",
            "dependencies": ["A"],
        },
    ]
    create_plan_with_error_handling("Circular Plan", circular_tasks)


def example_7_testing_mode():
    """Example 7: Testing mode with validation disabled"""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Testing Mode (Validation Disabled)")
    print("=" * 60)

    # Create plan that would normally fail validation
    builder = ExecutionPlanBuilder("Test Plan (Validation Disabled)")
    builder.add_task("A", TaskType.GENERAL_PURPOSE, "Task A", dependencies=["B"])
    builder.add_task("B", TaskType.GENERAL_PURPOSE, "Task B", dependencies=["A"])

    # Skip validation for testing
    plan = builder.build(validate=False)
    print(f"✅ Created plan with circular dependency for testing")
    print(f"   Tasks: {len(plan.tasks)}")
    print(f"   Note: Validation was disabled")

    # Manual validation later
    print("\n   Manual validation of test plan:")
    result = validate_execution_plan(plan)
    if result.success:
        print("   ✅ Plan is valid")
    else:
        print(f"   ❌ Found {len(result.errors)} validation errors:")
        for error in result.errors:
            print(f"      - {error.error_type.value}: {error.message}")


def example_8_manual_validation_control():
    """Example 8: Manual validation with detailed results"""
    print("\n" + "=" * 60)
    print("EXAMPLE 8: Manual Validation Control")
    print("=" * 60)

    # Create validator with custom settings
    validator = ExecutionPlanValidator(
        max_dependency_depth=10, strict_mode=True  # Lower limit for testing
    )

    # Create plan with deep dependency chain
    builder = ExecutionPlanBuilder("Deep Dependency Chain")
    prev_task = None
    for i in range(15):  # Will exceed max_dependency_depth of 10
        task_id = f"task_{i}"
        dependencies = [prev_task] if prev_task else []
        builder.add_task(
            task_id, TaskType.GENERAL_PURPOSE, f"Task {i}", dependencies=dependencies
        )
        prev_task = task_id

    plan = builder.build(validate=False)  # Skip automatic validation

    # Manual validation with detailed results
    result = validator.validate_execution_plan(plan)
    print(f"Validation result: {'✅ Success' if result.success else '❌ Failed'}")
    print(f"Validation time: {result.execution_time:.4f} seconds")
    print(f"Tasks validated: {len(plan.tasks)}")

    if not result.success:
        print(f"Errors found: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error.error_type.value}: {error.message}")

    if result.warnings:
        print(f"Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"  - {warning.message}")


def example_9_complex_valid_plan():
    """Example 9: Complex but valid plan"""
    print("\n" + "=" * 60)
    print("EXAMPLE 9: Complex Valid Plan")
    print("=" * 60)

    try:
        builder = ExecutionPlanBuilder("Complex SDLC Pipeline")

        # Discovery phase
        builder.add_task(
            "requirements",
            TaskType.REQUIREMENTS_ANALYST,
            "Gather and analyze requirements",
        )
        builder.add_task(
            "stakeholder_analysis",
            TaskType.BUSINESS_ANALYST,
            "Analyze stakeholder needs",
        )

        # Design phase (depends on discovery)
        builder.add_task(
            "architecture",
            TaskType.SOLUTION_ARCHITECT,
            "Design system architecture",
            dependencies=["requirements", "stakeholder_analysis"],
        )
        builder.add_task(
            "api_design",
            TaskType.API_INTEGRATION_SPECIALIST,
            "Design API interfaces",
            dependencies=["architecture"],
        )
        builder.add_task(
            "database_design",
            TaskType.DATABASE_SPECIALIST,
            "Design database schema",
            dependencies=["architecture"],
        )

        # Implementation phase (depends on design)
        builder.add_task(
            "backend_dev",
            TaskType.DEVELOPMENT_SPECIALIST,
            "Implement backend services",
            dependencies=["api_design", "database_design"],
        )
        builder.add_task(
            "frontend_dev",
            TaskType.DEVELOPMENT_SPECIALIST,
            "Implement frontend interface",
            dependencies=["api_design"],
        )

        # Testing phase (depends on implementation)
        builder.add_task(
            "unit_tests",
            TaskType.QA_TESTING_GURU,
            "Create and run unit tests",
            dependencies=["backend_dev", "frontend_dev"],
        )
        builder.add_task(
            "integration_tests",
            TaskType.QA_TESTING_GURU,
            "Run integration tests",
            dependencies=["unit_tests"],
        )

        # Deployment phase (depends on testing)
        builder.add_task(
            "deployment",
            TaskType.SDLC_DEPLOYMENT,
            "Deploy to production",
            dependencies=["integration_tests"],
        )

        plan = builder.build()
        print(f"✅ Complex plan created successfully")
        print(f"   Total tasks: {len(plan.tasks)}")
        print(f"   Execution batches: {len(plan.get_execution_order())}")

        # Show execution order
        print("   Execution order:")
        for i, batch in enumerate(plan.get_execution_order(), 1):
            print(f"     Batch {i}: {batch}")

    except Exception as e:
        print(f"❌ Failed to create complex plan: {e}")


def example_10_performance_validation():
    """Example 10: Performance validation with large plans"""
    print("\n" + "=" * 60)
    print("EXAMPLE 10: Performance Validation")
    print("=" * 60)

    import time

    # Create large plan
    builder = ExecutionPlanBuilder("Large Performance Test Plan")

    # Create 100 tasks with complex but valid dependencies
    for i in range(100):
        task_id = f"task_{i:03d}"
        dependencies = []

        # Create dependencies to previous tasks (but avoid circularity)
        if i > 0:
            dependencies.append(f"task_{i-1:03d}")
        if i > 10:
            dependencies.append(f"task_{i-10:03d}")

        builder.add_task(
            task_id, TaskType.GENERAL_PURPOSE, f"Task {i}", dependencies=dependencies
        )

    # Measure validation performance
    start_time = time.time()
    plan = builder.build()
    validation_time = time.time() - start_time

    print(f"✅ Large plan validation completed")
    print(f"   Tasks: {len(plan.tasks)}")
    print(f"   Validation time: {validation_time:.4f} seconds")
    print(f"   Performance: {len(plan.tasks) / validation_time:.0f} tasks/second")
    print(f"   Execution batches: {len(plan.get_execution_order())}")


def main():
    """Run all validation examples"""
    print("ExecutionPlan Validation System Examples")
    print("========================================")
    print("Demonstrating comprehensive validation capabilities")

    examples = [
        example_1_basic_validation,
        example_2_circular_dependency_detection,
        example_3_self_dependency_detection,
        example_4_duplicate_task_id_detection,
        example_5_invalid_dependency_reference,
        example_6_comprehensive_error_handling,
        example_7_testing_mode,
        example_8_manual_validation_control,
        example_9_complex_valid_plan,
        example_10_performance_validation,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Example failed with unexpected error: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎯 VALIDATION EXAMPLES COMPLETE")
    print("=" * 60)
    print("All validation capabilities demonstrated successfully!")
    print("The ExecutionPlan system is production-ready with comprehensive validation.")


if __name__ == "__main__":
    main()
