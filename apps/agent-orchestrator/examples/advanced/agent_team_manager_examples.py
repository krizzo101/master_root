#!/usr/bin/env python3
"""
AgentTeamManager Usage Examples

Demonstrates common usage patterns for management agents using the AgentTeamManager.
Shows how to launch and monitor teams with the simplified unified interface.
"""

import asyncio
import json
import logging

# Import the AgentTeamManager
import sys
import time
from pathlib import Path
from typing import Dict, List

sys.path.append(str(Path(__file__).parent.parent / "src"))
from agent_team_manager import AgentTeamManager, create_database_migration_team_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_team_launch_example():
    """Basic example of launching and monitoring a team"""

    print("=== Basic Team Launch Example ===")

    # Initialize team manager
    output_dir = Path("/tmp/team_manager_example")
    manager = AgentTeamManager(
        output_dir=output_dir,
        max_parallel=3,
        enable_quality_gates=False,  # Simplified for this example
        enable_monitoring=True,
    )

    # Define task definitions
    task_definitions = [
        {
            "task_id": "research_task",
            "task_type": "researcher",
            "prompt": "Research the current state of vector databases and their applications",
            "dependencies": [],
        },
        {
            "task_id": "analysis_task",
            "task_type": "analyzer",
            "prompt": "Analyze the research findings and identify key trends",
            "dependencies": ["research_task"],
        },
        {
            "task_id": "documentation_task",
            "task_type": "documenter",
            "prompt": "Create comprehensive documentation based on analysis",
            "dependencies": ["analysis_task"],
        },
    ]

    # Launch monitored team
    team_id = manager.launch_monitored_team(task_definitions)
    print(f"Launched team: {team_id}")

    # Monitor team progress
    async for status in manager.monitor_continuously(team_id, interval=10):
        print(f"\nTeam Status Update:")
        print(f"  Status: {status.status}")
        print(f"  Progress: {status.overall_progress_percentage:.1f}%")
        print(
            f"  Agents: {status.agents_running} running, {status.agents_completed} completed, {status.agents_failed} failed"
        )

        if status.status in ["completed", "failed"]:
            break

    # Get final results
    final_results = await manager.get_final_results(team_id)
    print(f"\nFinal Results:")
    print(f"  Status: {final_results.status}")
    print(f"  Success Rate: {final_results.success_rate:.1f}%")
    print(f"  Execution Time: {final_results.execution_time:.2f}s")
    print(f"  Deliverables: {len(final_results.deliverables_created)}")

    # Cleanup
    await manager.cleanup_team(team_id)
    await manager.shutdown()


async def quality_gates_example():
    """Example with quality gates for dependency management"""

    print("\n=== Quality Gates Example ===")

    # Initialize with quality gates enabled
    output_dir = Path("/tmp/quality_gates_example")
    manager = AgentTeamManager(
        output_dir=output_dir,
        max_parallel=3,
        enable_quality_gates=True,
        enable_monitoring=True,
    )

    # Setup quality gates
    gates_config = [
        {
            "gate_id": "environment_ready",
            "name": "Environment Ready",
            "description": "Development environment is set up",
            "validator_type": "file",
            "config": {"path": "/tmp/environment_ready.flag", "exists": True},
        },
        {
            "gate_id": "dependencies_installed",
            "name": "Dependencies Installed",
            "description": "Required dependencies are installed",
            "validator_type": "command",
            "config": {
                "command": ["python3", "-c", "import sys; print('Dependencies OK')"],
                "expected_return_code": 0,
            },
            "dependencies": ["environment_ready"],
        },
    ]

    await manager.setup_quality_gates(gates_config)

    # Create environment flag (simulate environment setup)
    Path("/tmp/environment_ready.flag").touch()

    # Define tasks with quality gate dependencies
    task_definitions = [
        {
            "task_id": "setup_task",
            "task_type": "setup_specialist",
            "prompt": "Set up the development environment and install dependencies",
            "quality_gates": ["environment_ready", "dependencies_installed"],
            "dependencies": [],
        },
        {
            "task_id": "development_task",
            "task_type": "development_specialist",
            "prompt": "Develop the core functionality",
            "dependencies": ["setup_task"],
        },
        {
            "task_id": "testing_task",
            "task_type": "testing_specialist",
            "prompt": "Run comprehensive tests on the developed functionality",
            "dependencies": ["development_task"],
        },
    ]

    # Launch team
    team_id = manager.launch_monitored_team(task_definitions)
    print(f"Launched team with quality gates: {team_id}")

    # Monitor with quality gate awareness
    async for status in manager.monitor_continuously(team_id, interval=15):
        print(f"\nTeam Status Update:")
        print(f"  Status: {status.status}")
        print(f"  Progress: {status.overall_progress_percentage:.1f}%")
        print(f"  Blocked by gates: {status.blocked_by_gates}")
        print(f"  Quality gates: {status.quality_gates_status}")

        if status.status in ["completed", "failed"]:
            break

    # Get results with quality metrics
    final_results = await manager.get_final_results(team_id)
    print(f"\nQuality Gate Results:")
    print(f"  Gates Passed: {final_results.quality_gates_passed}")
    print(f"  Gates Failed: {final_results.quality_gates_failed}")
    print(f"  Validation Errors: {final_results.validation_errors}")

    # Cleanup
    Path("/tmp/environment_ready.flag").unlink(missing_ok=True)
    await manager.cleanup_team(team_id)
    await manager.shutdown()


async def database_team_example():
    """Example using pre-configured database migration team"""

    print("\n=== Database Migration Team Example ===")

    # Use factory function for database teams
    output_dir = Path("/tmp/database_team_example")
    database_url = "postgresql://user:pass@localhost:5432/testdb"

    manager = create_database_migration_team_manager(
        output_dir=output_dir, database_url=database_url
    )

    # Define database migration tasks
    task_definitions = [
        {
            "task_id": "db_analysis",
            "task_type": "database_analyst",
            "prompt": "Analyze the current database schema and identify migration requirements",
            "quality_gates": ["database_ready"],
        },
        {
            "task_id": "migration_script",
            "task_type": "migration_specialist",
            "prompt": "Create SQLite to PostgreSQL migration scripts",
            "dependencies": ["db_analysis"],
            "quality_gates": ["migration_ready"],
        },
        {
            "task_id": "data_migration",
            "task_type": "data_migration_specialist",
            "prompt": "Execute data migration with validation",
            "dependencies": ["migration_script"],
        },
    ]

    # Launch database team
    team_id = manager.launch_monitored_team(task_definitions)
    print(f"Launched database migration team: {team_id}")

    # Monitor database-specific progress
    async for status in manager.monitor_continuously(team_id, interval=20):
        print(f"\nDatabase Team Status:")
        print(f"  Status: {status.status}")
        print(
            f"  Agents: {status.agent_count} total, {status.agents_completed} completed"
        )

        # Show agent-specific status
        for agent_uuid, agent_info in status.agent_statuses.items():
            print(
                f"    Agent {agent_uuid[:8]}: {agent_info.get('status', 'unknown')} "
                f"({agent_info.get('progress', 0):.1f}%)"
            )

        if status.status in ["completed", "failed"]:
            break

    # Get database migration results
    final_results = await manager.get_final_results(team_id)
    print(f"\nDatabase Migration Results:")
    print(final_results.execution_summary)

    # Cleanup
    await manager.cleanup_team(team_id)
    await manager.shutdown()


async def real_time_monitoring_example():
    """Example showing detailed real-time monitoring capabilities"""

    print("\n=== Real-Time Monitoring Example ===")

    output_dir = Path("/tmp/realtime_monitoring_example")
    manager = AgentTeamManager(
        output_dir=output_dir, max_parallel=4, enable_monitoring=True
    )

    # Define parallel tasks for monitoring
    task_definitions = [
        {
            "task_id": "parallel_task_1",
            "task_type": "processor",
            "prompt": "Process data set A with comprehensive analysis",
            "agent_uuid": "team-monitor-001-processor-a",
        },
        {
            "task_id": "parallel_task_2",
            "task_type": "processor",
            "prompt": "Process data set B with comprehensive analysis",
            "agent_uuid": "team-monitor-001-processor-b",
        },
        {
            "task_id": "parallel_task_3",
            "task_type": "processor",
            "prompt": "Process data set C with comprehensive analysis",
            "agent_uuid": "team-monitor-001-processor-c",
        },
        {
            "task_id": "aggregation_task",
            "task_type": "aggregator",
            "prompt": "Aggregate results from all processors",
            "dependencies": ["parallel_task_1", "parallel_task_2", "parallel_task_3"],
            "agent_uuid": "team-monitor-001-aggregator",
        },
    ]

    # Launch team
    team_id = manager.launch_monitored_team(task_definitions)
    print(f"Launched monitored team: {team_id}")

    # Detailed monitoring loop
    start_time = time.time()
    async for status in manager.monitor_continuously(team_id, interval=8):
        elapsed = time.time() - start_time
        print(f"\n[{elapsed:.1f}s] Detailed Team Status:")
        print(f"  Overall: {status.status} ({status.overall_progress_percentage:.1f}%)")
        print(
            f"  Breakdown: {status.agents_running} running, {status.agents_completed} done, "
            f"{status.agents_failed} failed, {status.agents_stuck} stuck"
        )

        # Show detailed agent information
        if status.agent_statuses:
            print("  Agent Details:")
            for agent_uuid, info in status.agent_statuses.items():
                if isinstance(info, dict):
                    print(
                        f"    {agent_uuid[:8]}: {info.get('status', 'unknown')} "
                        f"| Progress: {info.get('progress', 0):.1f}% "
                        f"| Current: {info.get('current_task', 'N/A')[:50]}..."
                    )

                    if info.get("errors", 0) > 0:
                        print(f"      ⚠️  Errors: {info['errors']}")

        if status.status in ["completed", "failed"]:
            break

    print(f"\nMonitoring completed in {time.time() - start_time:.1f} seconds")

    # Final results
    final_results = await manager.get_final_results(team_id)
    print(f"Final execution time: {final_results.execution_time:.2f}s")

    # Cleanup
    await manager.cleanup_team(team_id)
    await manager.shutdown()


def synchronous_usage_example():
    """Example showing synchronous usage pattern for compatibility"""

    print("\n=== Synchronous Usage Example ===")

    # This demonstrates how management agents can use the interface synchronously
    output_dir = Path("/tmp/sync_example")
    manager = AgentTeamManager(
        output_dir=output_dir, max_parallel=2, enable_monitoring=True
    )

    # Define simple tasks
    task_definitions = [
        {
            "task_id": "sync_task_1",
            "task_type": "worker",
            "prompt": "Complete synchronous work task 1",
        },
        {
            "task_id": "sync_task_2",
            "task_type": "worker",
            "prompt": "Complete synchronous work task 2",
        },
    ]

    # Launch team
    team_id = manager.launch_monitored_team(task_definitions)
    print(f"Launched synchronous team: {team_id}")

    # Use synchronous monitoring
    for status in manager.monitor_continuously_sync(team_id, interval=10):
        print(
            f"Sync monitoring - Status: {status.status}, Progress: {status.overall_progress_percentage:.1f}%"
        )

        if status.status in ["completed", "failed"]:
            break

    print("Synchronous monitoring completed")


async def main():
    """Run all examples"""
    print("AgentTeamManager Usage Examples")
    print("=" * 50)

    # Run examples
    await basic_team_launch_example()
    await quality_gates_example()

    # Note: Database example requires actual database - skip in demo
    # await database_team_example()

    await real_time_monitoring_example()

    # Synchronous example
    synchronous_usage_example()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
