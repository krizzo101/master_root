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

    # Prepare tasks and orchestrator
    orchestrator = None
    tasks = None
    execution_plan = None

    if args.execution_plan:
        # ExecutionPlan mode
        if not ENHANCED_AVAILABLE:
            print("Error: ExecutionPlan requires enhanced orchestrator features")
            print("Install missing dependencies: execution_plan package")
            return 1

        try:
            execution_plan = create_execution_plan_from_json(args.execution_plan)
            print(f"Loaded ExecutionPlan: {execution_plan.name}")
            print(
                f"Tasks: {len(execution_plan.tasks)}, Mode: {execution_plan.execution_mode.value}"
            )

            # Create enhanced orchestrator
            orchestrator = EnhancedOrchestrator(
                output_dir=Path(args.output_dir),
                max_parallel=args.max_parallel,
                enable_quality_gates=execution_plan.enable_quality_gates,
                enable_monitoring=execution_plan.enable_monitoring,
                use_optimizations=execution_plan.use_optimizations,
            )

        except Exception as e:
            print(f"Error loading ExecutionPlan: {e}")
            return 1

    elif args.example:
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
        print(
            "Error: Must specify one of: --execution-plan, --tasks-file, or --example"
        )
        parser.print_help()
        return 1

    # Initialize orchestrator if not already created
    if not orchestrator:
        if args.use_enhanced and ENHANCED_AVAILABLE:
            orchestrator = EnhancedOrchestrator(
                output_dir=Path(args.output_dir),
                max_parallel=args.max_parallel,
                use_optimizations=True,
            )
        else:
            orchestrator = GenericOrchestrator(
                output_dir=Path(args.output_dir),
                max_parallel=args.max_parallel,
                use_optimizations=True,
            )

    # Execute tasks
    if execution_plan:
        # Execute ExecutionPlan
        print(f"Executing ExecutionPlan: {execution_plan.name}")
        result = await orchestrator.execute_plan(execution_plan)
        results = result["results"]

        # Additional ExecutionPlan reporting
        print(f"Execution Mode: {result['execution_mode']}")
        if result.get("quality_metrics"):
            print(f"Quality Gates: {result['quality_metrics']}")
    else:
        # Execute regular tasks
        print(
            f"Executing {len(tasks)} tasks with max {args.max_parallel} parallel agents..."
        )
        results = await orchestrator.execute_batch(tasks)

    # Report results
    print("\n=== Execution Results ===")
    successful = 0
    failed = 0

    # Handle both dict and list result formats
    if isinstance(results, dict):
        result_items = results.items()
    else:
        result_items = [
            (r.get("task_id", f"task_{i}"), r) for i, r in enumerate(results)
        ]

    for task_id, result in result_items:
        status = result.get("status", "unknown")
        if status == "completed":
            successful += 1
            print(f"✓ {task_id}: SUCCESS")
        else:
            failed += 1
            error = result.get("error", "")
            print(f"✗ {task_id}: {status.upper()}" + (f" - {error}" if error else ""))

    print(f"\nSummary: {successful} successful, {failed} failed")
    print(f"Results saved to: {args.output_dir}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
