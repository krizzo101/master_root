#!/usr/bin/env python3
"""
Agent Orchestrator - Main Entry Point
Command-line interface for the agent orchestration framework
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator

try:
    from src.enhanced_orchestrator import EnhancedOrchestrator
    from src.execution_plan.adapter import create_execution_plan_from_json

    ENHANCED_AVAILABLE = True
except ImportError:
    EnhancedOrchestrator = None
    create_execution_plan_from_json = None
    ENHANCED_AVAILABLE = False


def load_tasks_from_file(file_path: str) -> list:
    """Load task definitions from a JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)

    tasks = []
    for task_data in data.get("tasks", []):
        tasks.append(AgentTask(**task_data))

    return tasks


async def main():
    parser = argparse.ArgumentParser(
        description="Agent Orchestrator - Execute parallel agent tasks"
    )

    parser.add_argument(
        "--tasks-file", type=str, help="JSON file containing task definitions"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory for results (default: ./output)",
    )

    parser.add_argument(
        "--max-parallel",
        type=int,
        default=5,
        help="Maximum number of parallel agents (default: 5)",
    )

    parser.add_argument("--example", action="store_true", help="Run with example tasks")

    parser.add_argument(
        "--execution-plan",
        type=str,
        help="JSON file containing ExecutionPlan definition",
    )

    parser.add_argument(
        "--use-enhanced",
        action="store_true",
        help="Use EnhancedOrchestrator with quality gates and monitoring",
    )

    args = parser.parse_args()

    # Prepare tasks
    if args.example:
        # Example tasks with dependencies
        tasks = [
            AgentTask(
                task_id="research",
                task_type="research",
                prompt="Research best practices for Python async programming",
            ),
            AgentTask(
                task_id="design",
                task_type="design",
                prompt="Design an async web server architecture based on the research",
                dependencies=["research"],
            ),
            AgentTask(
                task_id="implement",
                task_type="code",
                prompt="Implement a simple async web server based on the design",
                dependencies=["design"],
            ),
        ]
    elif args.tasks_file:
        tasks = load_tasks_from_file(args.tasks_file)
    else:
        print("Error: Either --tasks-file or --example must be specified")
        parser.print_help()
        return 1

    # Initialize orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=Path(args.output_dir),
        max_parallel=args.max_parallel,
        use_optimizations=True,
    )

    # Execute tasks
    print(
        f"Executing {len(tasks)} tasks with max {args.max_parallel} parallel agents..."
    )
    results = await orchestrator.execute_batch(tasks)

    # Report results
    print("\n=== Execution Results ===")
    successful = 0
    failed = 0

    for task_id, result in results.items():
        status = result.get("status", "unknown")
        if status == "completed":
            successful += 1
            print(f"✓ {task_id}: SUCCESS")
        else:
            failed += 1
            print(f"✗ {task_id}: {status.upper()}")

    print(f"\nSummary: {successful} successful, {failed} failed")
    print(f"Results saved to: {args.output_dir}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
