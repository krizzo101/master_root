#!/usr/bin/env python3
"""
Simple execution of remaining 5 Phase 1 tasks using GenericOrchestrator
Based on working execute_phase1_plan.py pattern
"""
import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from unified_context_phase1_plan import create_unified_context_phase1_plan

from src.generic_orchestrator import AgentTask, GenericOrchestrator


def get_remaining_tasks():
    """Get the 5 remaining tasks that need completion"""
    plan = create_unified_context_phase1_plan()
    completed_files = []

    output_dir = Path("phase1_execution_output/tasks")
    if output_dir.exists():
        completed_files = [f.stem for f in output_dir.glob("*.json")]

    remaining_tasks = [
        task for task in plan.tasks if task.task_id not in completed_files
    ]
    return remaining_tasks


def convert_to_agent_tasks(execution_plan_tasks):
    """Convert ExecutionPlan tasks to AgentTask format"""
    agent_tasks = []

    for task in execution_plan_tasks:
        # Create comprehensive prompt
        prompt_parts = [
            f"TASK: {task.prompt}",
            "",
            f"SPECIALIST ROLE: You are acting as a {task.task_type.value} agent.",
            "",
        ]

        if task.context:
            prompt_parts.append("CONTEXT:")
            context_dict = (
                task.context.__dict__
                if hasattr(task.context, "__dict__")
                else task.context
            )
            for key, value in context_dict.items():
                if isinstance(value, list) and value:
                    prompt_parts.append(f"- {key}:")
                    for item in value:
                        prompt_parts.append(f"  • {item}")
                elif value and not isinstance(value, (list, dict)):
                    prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        if task.dependencies:
            prompt_parts.append(
                f"DEPENDENCIES: This task depends on completion of: {', '.join(task.dependencies)}"
            )
            prompt_parts.append("")

        prompt_parts.extend(
            [
                "DELIVERABLES: Provide detailed implementation, code, documentation, or analysis as appropriate for your specialist role.",
                "",
                "WORKING DIRECTORY: /home/opsvi/master_root/apps/project-context",
                "",
                "PROJECT CONTEXT: You are completing Phase 1 of the Unified Context System. The foundation work is complete (database schema, base pipeline) and you are implementing the remaining adapters, integration, testing, and documentation.",
            ]
        )

        full_prompt = "\n".join(prompt_parts)

        agent_task = AgentTask(
            task_id=task.task_id,
            task_type=task.task_type.value,
            prompt=full_prompt,
            dependencies=task.dependencies,
            context={
                "phase": "Phase 1: Completion",
                "project": "Unified Context System",
                "foundation_complete": True,
            },
        )
        agent_tasks.append(agent_task)

    return agent_tasks


async def execute_remaining_tasks():
    """Execute the 5 remaining Phase 1 tasks"""
    print("🚀 PHASE 1 COMPLETION - Executing Final 5 Tasks")
    print("=" * 60)

    # Get remaining tasks
    remaining_tasks = get_remaining_tasks()
    print(f"📋 Found {len(remaining_tasks)} remaining tasks:")
    for task in remaining_tasks:
        deps = ", ".join(task.dependencies) if task.dependencies else "none"
        print(f"   - {task.task_id} ({task.task_type.value}) [deps: {deps}]")
    print()

    # Convert to AgentTask format
    agent_tasks = convert_to_agent_tasks(remaining_tasks)

    # Set up output directory
    output_dir = Path("phase1_completion_output")
    output_dir.mkdir(exist_ok=True)

    # Initialize GenericOrchestrator with higher parallelization
    orchestrator = GenericOrchestrator(
        output_dir=output_dir,
        max_parallel=5,  # All 5 tasks can run as dependencies allow
    )

    print(f"⚡ Starting execution with max_parallel=5")
    print(f"📁 Output directory: {output_dir}")
    print()

    try:
        # Execute all tasks with dependency resolution
        print("🎯 Executing remaining tasks with dependency resolution...")
        results = await orchestrator.execute_batch(agent_tasks)

        print(f"\n✅ Execution completed! {len(results)} tasks processed")

        # Analyze results
        successful_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        print(f"   ✅ Successful: {len(successful_tasks)}")
        print(f"   ❌ Failed: {len(failed_tasks)}")

        if failed_tasks:
            print("\n❌ Failed Tasks:")
            for task in failed_tasks:
                print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

        if successful_tasks:
            print("\n✅ Successful Completions:")
            for task in successful_tasks:
                duration = task.get("duration_ms", 0) / 1000 / 60
                print(
                    f"   - {task['task_id']} ({task.get('agent_type', 'unknown')}) - {duration:.1f}min"
                )

        # Check final Phase 1 status
        all_completed = len(successful_tasks) == len(agent_tasks)
        if all_completed:
            print(
                f"\n🎉 PHASE 1 COMPLETE! All {len(successful_tasks)} remaining tasks successful!"
            )
            print("   📊 Final Status: 11/11 tasks completed")
            print("   🚀 Ready for Phase 2 execution!")
        else:
            print(
                f"\n⚠️  Phase 1 partially complete: {len(successful_tasks)}/{len(agent_tasks)} remaining tasks"
            )

        return results

    except Exception as e:
        print(f"❌ Execution failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Main execution function"""
    print("UNIFIED CONTEXT SYSTEM - PHASE 1 COMPLETION")
    print("Completing final 5 tasks using GenericOrchestrator")
    print("=" * 60)
    print()

    # Run the async execution
    results = asyncio.run(execute_remaining_tasks())

    if results:
        print(f"\n🎯 Phase 1 Completion Results Available!")
        print(f"   Check outputs in: phase1_completion_output/")
    else:
        print(f"\n❌ Phase 1 Completion FAILED!")
        print(f"   Check logs for debugging information")


if __name__ == "__main__":
    main()
