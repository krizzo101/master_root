#!/usr/bin/env python3
"""
Quality Gate Examples and Usage Patterns

This module demonstrates how to use the Quality Gate system for common scenarios
in the unified context system and other complex projects.
"""

import asyncio
import os
from pathlib import Path
from typing import List

from src.enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
from src.quality_gates import (
    QualityGateManager,
    create_api_ready_gate,
    create_database_ready_gate,
    create_file_ready_gate,
    create_migration_complete_gate,
)


async def example_unified_context_system():
    """
    Example: Unified Context System with Quality Gates

    This demonstrates the complex dependency chain needed for the unified context system:
    Database Setup → Migration → Population → Testing → Validation
    """

    print("=== Unified Context System Quality Gate Example ===")

    # Create orchestrator
    output_dir = Path("/tmp/unified_context_quality_gates")
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir, max_parallel=3, enable_quality_gates=True
    )

    # Define quality gates for the unified context system
    qg_manager = orchestrator.quality_gate_manager

    # 1. Database ready gate
    await create_database_ready_gate(
        qg_manager,
        connection_string=os.environ.get(
            "DATABASE_URL", "postgresql://localhost/context_db"
        ),
    )

    # 2. Migration complete gate
    await create_migration_complete_gate(
        qg_manager,
        connection_string=os.environ.get(
            "DATABASE_URL", "postgresql://localhost/context_db"
        ),
        min_records=633,
    )

    # 3. API ready gate
    await create_api_ready_gate(qg_manager, "ws://localhost:8080/ide-bridge")

    # 4. Configuration files ready
    await create_file_ready_gate(
        qg_manager,
        "/home/opsvi/master_root/docker-compose.postgres.yml",
        contains="pgvector",
    )

    # 5. Embedding service ready
    await qg_manager.define_gate(
        gate_id="embedding_service_ready",
        name="Embedding Service Ready",
        description="Embedding service is running and accessible",
        validator_type="http",
        config={
            "url": "http://localhost:8001/health",
            "method": "GET",
            "expected_status": [200],
        },
        dependencies=["database_ready"],
    )

    # 6. Define execution phases
    await orchestrator.define_phase(
        phase_id="infrastructure",
        name="Infrastructure Setup",
        description="Database and core services",
        gates=["database_ready", "file_ready_docker-compose.postgres.yml"],
    )

    await orchestrator.define_phase(
        phase_id="migration",
        name="Data Migration",
        description="Migrate and populate data",
        gates=["migration_complete", "embedding_service_ready"],
    )

    await orchestrator.define_phase(
        phase_id="services",
        name="Service Validation",
        description="Validate all services are running",
        gates=["api_responding"],
    )

    # Define tasks with quality gate dependencies
    def generate_unified_context_tasks() -> List[EnhancedAgentTask]:
        tasks = []

        # Infrastructure tasks
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="setup_database",
                task_type="infrastructure",
                prompt="Set up PostgreSQL database with pgvector extension",
                quality_gates=["database_ready"],
                phase_id="infrastructure",
            )
        )

        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="deploy_embedding_service",
                task_type="service",
                prompt="Deploy and start embedding service",
                dependencies=["setup_database"],
                quality_gates=["database_ready", "embedding_service_ready"],
                phase_id="infrastructure",
            )
        )

        # Migration tasks
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="migrate_context_data",
                task_type="migration",
                prompt="Migrate context items to PostgreSQL with vector embeddings",
                dependencies=["deploy_embedding_service"],
                quality_gates=["migration_complete", "embedding_service_ready"],
                phase_id="migration",
            )
        )

        # Service validation tasks
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="validate_ide_bridge",
                task_type="validation",
                prompt="Validate IDE context bridge WebSocket API",
                dependencies=["migrate_context_data"],
                quality_gates=["api_responding"],
                phase_id="services",
            )
        )

        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="run_integration_tests",
                task_type="testing",
                prompt="Run full integration tests on unified context system",
                dependencies=["validate_ide_bridge"],
                quality_gates=["api_responding", "migration_complete"],
                phase_id="services",
            )
        )

        return tasks

    # Run orchestration
    results = await orchestrator.run(generate_unified_context_tasks)

    # Print results
    print(f"\nExecution Results:")
    print(f"Total tasks: {results['metrics']['total']}")
    print(f"Completed: {results['metrics']['completed']}")
    print(f"Failed: {results['metrics']['failed']}")

    if "quality_metrics" in results:
        qm = results["quality_metrics"]
        print(f"Quality gates validated: {qm['gates_validated']}")
        print(f"Quality gate wait time: {qm['quality_gate_wait_time']:.2f}s")

    return results


async def example_simple_dependency_chain():
    """
    Example: Simple dependency chain with quality gates
    Demonstrates basic usage patterns
    """

    print("\n=== Simple Dependency Chain Example ===")

    output_dir = Path("/tmp/simple_quality_gates")
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir, max_parallel=2, enable_quality_gates=True
    )

    qg_manager = orchestrator.quality_gate_manager

    # Define a simple file-based quality gate
    await qg_manager.define_gate(
        gate_id="config_ready",
        name="Configuration Ready",
        description="Configuration file exists and is valid",
        validator_type="file",
        config={"path": "/tmp/app_config.json", "exists": True, "contains": "version"},
    )

    # Define command-based quality gate
    await qg_manager.define_gate(
        gate_id="service_healthy",
        name="Service Health Check",
        description="Health check command succeeds",
        validator_type="command",
        config={"command": ["echo", "healthy"], "expected_return_code": 0},
        dependencies=["config_ready"],
    )

    def generate_simple_tasks() -> List[EnhancedAgentTask]:
        tasks = []

        # Task that creates the config file
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="create_config",
                task_type="setup",
                prompt="Create application configuration file at /tmp/app_config.json with version field",
                quality_gates=[],  # No dependencies
            )
        )

        # Task that waits for config to be ready
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="validate_config",
                task_type="validation",
                prompt="Validate the configuration file is properly formatted",
                dependencies=["create_config"],
                quality_gates=["config_ready"],
            )
        )

        # Task that waits for service health
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="start_service",
                task_type="service",
                prompt="Start the application service",
                dependencies=["validate_config"],
                quality_gates=["service_healthy"],
            )
        )

        return tasks

    results = await orchestrator.run(generate_simple_tasks)

    print(
        f"Simple example - Completed: {results['metrics']['completed']}/{results['metrics']['total']}"
    )

    return results


async def example_parallel_validation():
    """
    Example: Parallel tasks with shared quality gates
    Shows how multiple tasks can depend on the same gates
    """

    print("\n=== Parallel Validation Example ===")

    output_dir = Path("/tmp/parallel_quality_gates")
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir, max_parallel=4, enable_quality_gates=True
    )

    qg_manager = orchestrator.quality_gate_manager

    # Shared quality gate that multiple tasks depend on
    await qg_manager.define_gate(
        gate_id="shared_resource_ready",
        name="Shared Resource Ready",
        description="Shared resource is available for all tasks",
        validator_type="command",
        config={
            "command": ["test", "-f", "/tmp/shared_resource.txt"],
            "expected_return_code": 0,
        },
    )

    def generate_parallel_tasks() -> List[EnhancedAgentTask]:
        tasks = []

        # Task that creates the shared resource
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="create_shared_resource",
                task_type="setup",
                prompt="Create shared resource file at /tmp/shared_resource.txt",
                quality_gates=[],
            )
        )

        # Multiple tasks that depend on the shared resource
        for i in range(3):
            tasks.append(
                orchestrator.create_enhanced_task(
                    task_id=f"consumer_task_{i}",
                    task_type="processing",
                    prompt=f"Process data using shared resource (task {i})",
                    dependencies=["create_shared_resource"],  # Task dependency
                    quality_gates=["shared_resource_ready"],  # Quality gate dependency
                )
            )

        return tasks

    results = await orchestrator.run(generate_parallel_tasks)

    print(
        f"Parallel example - Completed: {results['metrics']['completed']}/{results['metrics']['total']}"
    )

    return results


async def example_phase_based_execution():
    """
    Example: Phase-based execution with quality gates
    Demonstrates how to organize complex workflows into phases
    """

    print("\n=== Phase-Based Execution Example ===")

    output_dir = Path("/tmp/phase_quality_gates")
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir, max_parallel=2, enable_quality_gates=True
    )

    qg_manager = orchestrator.quality_gate_manager

    # Define gates for different phases
    await qg_manager.define_gate(
        gate_id="phase1_complete",
        name="Phase 1 Complete",
        description="All Phase 1 deliverables are ready",
        validator_type="file",
        config={"path": "/tmp/phase1_complete.marker", "exists": True},
    )

    await qg_manager.define_gate(
        gate_id="phase2_complete",
        name="Phase 2 Complete",
        description="All Phase 2 deliverables are ready",
        validator_type="file",
        config={"path": "/tmp/phase2_complete.marker", "exists": True},
        dependencies=["phase1_complete"],
    )

    # Define phases
    await orchestrator.define_phase(
        phase_id="phase1",
        name="Foundation Phase",
        description="Set up foundational components",
        gates=["phase1_complete"],
    )

    await orchestrator.define_phase(
        phase_id="phase2",
        name="Integration Phase",
        description="Integrate and test components",
        gates=["phase2_complete"],
    )

    def generate_phase_tasks() -> List[EnhancedAgentTask]:
        tasks = []

        # Phase 1 tasks
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="phase1_setup",
                task_type="setup",
                prompt="Set up foundational components and create marker file /tmp/phase1_complete.marker",
                phase_id="phase1",
                quality_gates=[],
            )
        )

        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="phase1_validation",
                task_type="validation",
                prompt="Validate Phase 1 setup is complete",
                dependencies=["phase1_setup"],
                phase_id="phase1",
                quality_gates=["phase1_complete"],
            )
        )

        # Phase 2 tasks (depend on Phase 1 completion)
        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="phase2_integration",
                task_type="integration",
                prompt="Integrate components and create marker file /tmp/phase2_complete.marker",
                dependencies=["phase1_validation"],
                phase_id="phase2",
                quality_gates=["phase1_complete"],
            )
        )

        tasks.append(
            orchestrator.create_enhanced_task(
                task_id="phase2_testing",
                task_type="testing",
                prompt="Run comprehensive tests on integrated system",
                dependencies=["phase2_integration"],
                phase_id="phase2",
                quality_gates=["phase2_complete"],
            )
        )

        return tasks

    results = await orchestrator.run(generate_phase_tasks)

    print(
        f"Phase example - Completed: {results['metrics']['completed']}/{results['metrics']['total']}"
    )

    # Show phase completion status
    if "quality_status" in results:
        phases = results["quality_status"].get("phases", {})
        for phase_id, phase_info in phases.items():
            print(f"  {phase_info['name']}: {phase_info['gates_passed']} gates passed")

    return results


async def main():
    """Run all examples"""

    print("Quality Gate System Examples")
    print("=" * 50)

    # Ensure required dependencies are available (mock for examples)
    os.makedirs("/tmp", exist_ok=True)

    try:
        # Run examples (comment out any that require actual services)
        # await example_unified_context_system()  # Requires actual database
        await example_simple_dependency_chain()
        await example_parallel_validation()
        await example_phase_based_execution()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    except Exception as e:
        print(f"Example execution failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
