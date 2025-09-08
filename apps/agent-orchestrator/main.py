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

    parser.add_argument(
        "--workflow-name",
        type=str,
        help="Custom workflow name (default: derived from tasks file)",
    )

    parser.add_argument(
        "--enable-dashboard",
        action="store_true",
        help="Enable dashboard reporting and workflow tracking",
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
        # Determine if we should use workflow-specific directory structure
        workflow_name = args.workflow_name
        task_file_path = args.tasks_file if hasattr(args, "tasks_file") else None

        # Set up dashboard callback if enabled
        dashboard_callback = None
        if args.enable_dashboard:

            def simple_dashboard_callback(state_data):
                # Simple console output for now - can be extended to actual dashboard integration
                event = state_data.get("event")
                workflow_name = state_data.get("workflow_name", "unknown")

                if event == "workflow_started":
                    print(f"🚀 Workflow '{workflow_name}' started")
                elif event == "workflow_progress":
                    progress = state_data.get("progress_percent", 0)
                    completed = state_data.get("completed_tasks", 0)
                    total = state_data.get("total_tasks", 0)
                    eta = state_data.get("eta_seconds")
                    eta_str = f", ETA: {eta}s" if eta else ""
                    print(f"📊 Progress: {progress}% ({completed}/{total}){eta_str}")
                elif event == "task_activity":
                    task_id = state_data.get("task_id")
                    activity = state_data.get("activity")
                    if activity == "started":
                        print(f"🔄 Task '{task_id}' started")
                    elif activity == "completed":
                        duration = state_data.get("details", {}).get("duration", 0)
                        print(f"✅ Task '{task_id}' completed in {duration:.2f}s")
                    elif activity == "failed":
                        error = state_data.get("details", {}).get(
                            "error", "Unknown error"
                        )
                        print(f"❌ Task '{task_id}' failed: {error}")
                elif event == "workflow_completed":
                    metrics = state_data.get("metrics", {})
                    duration = metrics.get("total_duration", 0)
                    print(f"🎉 Workflow '{workflow_name}' completed in {duration:.2f}s")

            dashboard_callback = simple_dashboard_callback

        if args.use_enhanced and ENHANCED_AVAILABLE:
            orchestrator = EnhancedOrchestrator(
                output_dir=Path(args.output_dir),
                max_parallel=args.max_parallel,
                use_optimizations=True,
                workflow_name=workflow_name,
                task_file_path=task_file_path,
                enable_dashboard_reporting=args.enable_dashboard,
                dashboard_state_callback=dashboard_callback,
            )
        else:
            orchestrator = GenericOrchestrator(
                output_dir=Path(args.output_dir),
                max_parallel=args.max_parallel,
                use_optimizations=False,
                workflow_name=workflow_name,
                task_file_path=task_file_path,
                enable_dashboard_reporting=args.enable_dashboard,
                dashboard_state_callback=dashboard_callback,
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

    # Show the actual output directory used by the orchestrator
    actual_output_dir = getattr(orchestrator, "output_dir", args.output_dir)
    print(f"Results saved to: {actual_output_dir}")

    # Show workflow information if dashboard is enabled
    if args.enable_dashboard and hasattr(orchestrator, "workflow_name"):
        print(
            f"Workflow: {orchestrator.workflow_name} (ID: {getattr(orchestrator, 'workflow_id', 'unknown')})"
        )
        if (
            hasattr(orchestrator, "workflow_base_dir")
            and orchestrator.workflow_base_dir
        ):
            print(f"Workflow history: {orchestrator.workflow_base_dir}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
