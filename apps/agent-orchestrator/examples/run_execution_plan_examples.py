#!/usr/bin/env python3
"""
Examples demonstrating ExecutionPlan usage with the agent orchestrator.

This script shows various ways to create and execute ExecutionPlans,
from simple parallel tasks to complex SDLC pipelines.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.execution_plan import (
    ExecutionMode,
    ExecutionPlanBuilder,
    TaskType,
    ValidationLevel,
    create_sdlc_pipeline_plan,
    create_simple_parallel_plan,
)
from src.execution_plan.adapter import (
    create_execution_plan_from_json,
    save_execution_plan_to_json,
)


async def example_1_simple_parallel():
    """Example 1: Simple parallel task execution"""

    print("=== Example 1: Simple Parallel Execution ===")

    # Create simple parallel plan using template
    tasks = [
        {
            "task_id": "analyze_performance",
            "task_type": "performance-optimizer",
            "prompt": "Analyze application performance and identify bottlenecks",
        },
        {
            "task_id": "review_security",
            "task_type": "security-architect",
            "prompt": "Review codebase for security vulnerabilities and best practices",
        },
        {
            "task_id": "document_architecture",
            "task_type": "technical-writer",
            "prompt": "Document the current system architecture and components",
        },
    ]

    plan = create_simple_parallel_plan(
        name="Code Review Pipeline",
        tasks=tasks,
        description="Parallel code analysis and documentation",
    )

    print(f"Created plan: {plan.name}")
    print(f"Tasks: {len(plan.tasks)}")
    print(f"Execution mode: {plan.execution_mode.value}")

    # Save plan for later use
    output_dir = Path("./output/examples")
    output_dir.mkdir(parents=True, exist_ok=True)
    save_execution_plan_to_json(plan, output_dir / "simple_parallel_plan.json")

    return plan


async def example_2_dependency_chain():
    """Example 2: Sequential tasks with dependencies"""

    print("\n=== Example 2: Dependency Chain ===")

    # Build plan with dependencies using builder
    builder = ExecutionPlanBuilder(
        name="Database Migration Pipeline",
        description="Sequential database operations with dependencies",
    )

    builder.set_execution_mode(ExecutionMode.SEQUENTIAL)

    # Step 1: Analyze current database
    builder.add_task(
        task_id="analyze_database",
        task_type=TaskType.DATABASE_SPECIALIST,
        prompt="Analyze current database schema, performance, and identify migration needs",
        validation_level=ValidationLevel.STRICT,
    )

    # Step 2: Plan migration (depends on analysis)
    builder.add_task(
        task_id="plan_migration",
        task_type=TaskType.DATABASE_SPECIALIST,
        prompt="Create detailed migration plan with rollback strategy based on database analysis",
        dependencies=["analyze_database"],
        validation_level=ValidationLevel.STRICT,
    )

    # Step 3: Execute migration (depends on plan)
    builder.add_task(
        task_id="execute_migration",
        task_type=TaskType.DATABASE_SPECIALIST,
        prompt="Execute database migration according to the migration plan",
        dependencies=["plan_migration"],
        validation_level=ValidationLevel.STRICT,
    )

    # Step 4: Validate migration (depends on execution)
    builder.add_task(
        task_id="validate_migration",
        task_type=TaskType.QA_TESTING_GURU,
        prompt="Validate migration success and run comprehensive database tests",
        dependencies=["execute_migration"],
        validation_level=ValidationLevel.STRICT,
    )

    plan = builder.build()

    print(f"Created plan: {plan.name}")
    print(f"Tasks: {len(plan.tasks)}")

    # Show execution order
    execution_order = plan.get_execution_order()
    print(f"Execution order: {execution_order}")

    # Save plan
    output_dir = Path("./output/examples")
    save_execution_plan_to_json(plan, output_dir / "database_migration_plan.json")

    return plan


async def example_3_sdlc_pipeline():
    """Example 3: Complete SDLC pipeline with phases and quality gates"""

    print("\n=== Example 3: SDLC Pipeline ===")

    # Create SDLC pipeline using template
    plan = create_sdlc_pipeline_plan(
        project_name="E-commerce API",
        requirements="""
        Build a RESTful API for e-commerce with:
        - Product catalog management
        - User registration and authentication
        - Shopping cart functionality
        - Order processing and payment integration
        - Inventory management
        - Admin dashboard APIs
        """,
    )

    print(f"Created plan: {plan.name}")
    print(f"Tasks: {len(plan.tasks)}")
    print(f"Quality gates: {len(plan.quality_gates)}")
    print(f"Phases: {len(plan.phases)}")
    print(f"Execution mode: {plan.execution_mode.value}")

    # Show phases
    print("\nPhases:")
    for phase in plan.phases:
        print(f"  - {phase.name}: {len(phase.gates)} gates")

    # Show some quality gates
    print("\nQuality gates:")
    for gate in plan.quality_gates[:3]:  # Show first 3
        print(f"  - {gate.name}: {gate.description}")

    # Save plan
    output_dir = Path("./output/examples")
    save_execution_plan_to_json(plan, output_dir / "ecommerce_sdlc_plan.json")

    return plan


async def example_4_custom_quality_gates():
    """Example 4: Custom plan with quality gates"""

    print("\n=== Example 4: Custom Quality Gates ===")

    builder = ExecutionPlanBuilder(
        name="API Development with Quality Gates",
        description="API development with automated quality validation",
    )

    builder.set_execution_mode(ExecutionMode.MIXED)

    # Add quality gates
    builder.add_quality_gate(
        gate_id="tests_passing",
        name="All Tests Pass",
        description="All unit and integration tests must pass",
        gate_type="test_results",
        config={
            "test_command": "npm test",
            "coverage_threshold": 80,
            "required_suites": ["unit", "integration"],
        },
    )

    builder.add_quality_gate(
        gate_id="api_responding",
        name="API Health Check",
        description="API endpoints must be responding correctly",
        gate_type="http",
        config={
            "url": "http://localhost:3000/health",
            "method": "GET",
            "expected_status": [200],
            "timeout": 30,
        },
    )

    # Add tasks with quality gate dependencies
    builder.add_task(
        task_id="implement_api",
        task_type=TaskType.API_INTEGRATION_SPECIALIST,
        prompt="Implement REST API with user management endpoints",
        quality_gates=["tests_passing"],
    )

    builder.add_task(
        task_id="deploy_staging",
        task_type=TaskType.SDLC_DEPLOYMENT,
        prompt="Deploy API to staging environment",
        dependencies=["implement_api"],
        quality_gates=["api_responding"],
    )

    builder.add_task(
        task_id="integration_tests",
        task_type=TaskType.QA_TESTING_GURU,
        prompt="Run comprehensive integration tests against staging API",
        dependencies=["deploy_staging"],
        quality_gates=["tests_passing", "api_responding"],
    )

    plan = builder.build()

    print(f"Created plan: {plan.name}")
    print(f"Tasks: {len(plan.tasks)}")
    print(f"Quality gates: {len(plan.quality_gates)}")

    # Show quality gate dependencies
    print("\nQuality gate dependencies:")
    for task in plan.tasks:
        if task.quality_gates:
            print(f"  - {task.task_id}: depends on gates {task.quality_gates}")

    # Save plan
    output_dir = Path("./output/examples")
    save_execution_plan_to_json(plan, output_dir / "quality_gates_plan.json")

    return plan


async def example_5_load_and_execute():
    """Example 5: Load plan from JSON and execute (dry run)"""

    print("\n=== Example 5: Load and Execute Plan ===")

    # Load existing plan
    examples_dir = Path(__file__).parent
    plan_file = examples_dir / "simple_execution_plan.json"

    if plan_file.exists():
        plan = create_execution_plan_from_json(plan_file)
        print(f"Loaded plan: {plan.name}")
        print(f"Description: {plan.description}")

        # Create orchestrator (dry run mode - no actual execution)
        output_dir = Path("./output/example_5")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Note: In a real scenario, you would uncomment this and have proper
        # Claude tokens configured for actual execution
        """
        orchestrator = EnhancedOrchestrator(
            output_dir=output_dir,
            max_parallel=plan.max_parallel_tasks,
            enable_quality_gates=plan.enable_quality_gates,
            enable_monitoring=plan.enable_monitoring
        )

        # Execute the plan
        result = await orchestrator.execute_plan(plan)

        print(f"Execution completed: {result['plan_name']}")
        print(f"Total tasks: {result['total_tasks']}")
        print(f"Results: {len(result['results'])} task results")
        """

        print("(Dry run - actual execution commented out)")
        print(
            "To execute: uncomment the orchestrator code and ensure Claude tokens are configured"
        )

    else:
        print(f"Plan file not found: {plan_file}")
        print("Run the other examples first to generate the plan file")


async def main():
    """Run all examples"""

    print("ExecutionPlan Examples - Agent Orchestrator")
    print("=" * 50)

    try:
        # Run examples
        await example_1_simple_parallel()
        await example_2_dependency_chain()
        await example_3_sdlc_pipeline()
        await example_4_custom_quality_gates()
        await example_5_load_and_execute()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nGenerated files in ./output/examples/:")

        output_dir = Path("./output/examples")
        if output_dir.exists():
            for file in output_dir.glob("*.json"):
                print(f"  - {file.name}")

        print("\nTo execute plans:")
        print(
            "  python main.py --execution-plan ./output/examples/simple_parallel_plan.json"
        )
        print("  python main.py --execution-plan examples/simple_execution_plan.json")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
