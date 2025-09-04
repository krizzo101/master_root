#!/usr/bin/env python3
"""
Execute the Unified Context System Phase 1 ExecutionPlan using GenericOrchestrator
Converts ExecutionPlan tasks to AgentTask format and runs them in parallel
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


def convert_execution_plan_to_agent_tasks(execution_plan):
    """
    Convert ExecutionPlan tasks to AgentTask format for GenericOrchestrator
    """
    agent_tasks = []

    for task in execution_plan.tasks:
        # Create comprehensive prompt that includes task context
        prompt_parts = [
            f"TASK: {task.prompt}",
            "",
            f"SPECIALIST ROLE: You are acting as a {task.task_type.value} agent.",
            "",
        ]

        if task.context:
            prompt_parts.append("CONTEXT:")
            context_dict = (
                task.context.to_dict()
                if hasattr(task.context, "to_dict")
                else task.context.__dict__
            )
            for key, value in context_dict.items():
                if isinstance(value, list) and value:  # Only show non-empty lists
                    prompt_parts.append(f"- {key}:")
                    for item in value:
                        prompt_parts.append(f"  • {item}")
                elif value and not isinstance(
                    value, (list, dict)
                ):  # Show non-empty simple values
                    prompt_parts.append(f"- {key}: {value}")
                elif isinstance(value, dict) and value:  # Show non-empty dicts
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
                "PROJECT CONTEXT: You are implementing Phase 1 of the Unified Context System - a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.",
            ]
        )

        full_prompt = "\n".join(prompt_parts)

        agent_task = AgentTask(
            task_id=task.task_id,
            task_type=task.task_type.value,
            prompt=full_prompt,
            dependencies=task.dependencies,
            context={
                "execution_plan_id": execution_plan.plan_id,
                "original_context": task.context,
                "phase": "Phase 1: Foundation",
                "project": "Unified Context System",
            },
        )
        agent_tasks.append(agent_task)

    return agent_tasks


async def execute_phase1_plan():
    """
    Execute the Phase 1 plan using the GenericOrchestrator
    """
    print("🚀 Executing Unified Context System Phase 1 Implementation Plan...")

    # Create the execution plan
    execution_plan = create_unified_context_phase1_plan()
    print(f"📋 ExecutionPlan loaded: {len(execution_plan.tasks)} tasks")

    # Convert to AgentTask format
    agent_tasks = convert_execution_plan_to_agent_tasks(execution_plan)
    print(f"🔄 Converted to {len(agent_tasks)} AgentTask objects")

    # Set up output directory
    output_dir = Path(
        "/home/opsvi/master_root/apps/project-context/phase1_execution_output"
    )
    output_dir.mkdir(exist_ok=True)

    # Initialize GenericOrchestrator with parallel execution
    orchestrator = GenericOrchestrator(
        output_dir=output_dir,
        max_parallel=3,  # Run up to 3 specialist agents simultaneously
    )

    print(f"⚡ Starting parallel execution with max_parallel=3")
    print(f"📁 Output directory: {output_dir}")
    print()

    try:
        # Execute all tasks with automatic dependency resolution
        print("🎯 Executing tasks with dependency resolution...")
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

        # Show successful completions
        if successful_tasks:
            print("\n✅ Successful Completions:")
            for task in successful_tasks:
                print(f"   - {task['task_id']} ({task.get('agent_type', 'unknown')})")

        # Summary by agent type
        agent_type_results = {}
        for result in results:
            agent_type = result.get("agent_type", "unknown")
            status = result.get("status", "unknown")
            if agent_type not in agent_type_results:
                agent_type_results[agent_type] = {"completed": 0, "failed": 0}
            agent_type_results[agent_type][status] += 1

        print(f"\n📊 Results by Specialist Agent:")
        for agent_type, counts in sorted(agent_type_results.items()):
            total = counts["completed"] + counts["failed"]
            success_rate = (counts["completed"] / total * 100) if total > 0 else 0
            print(
                f"   {agent_type}: {counts['completed']}/{total} ({success_rate:.1f}% success)"
            )

        return results

    except Exception as e:
        print(f"❌ Execution failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Main execution function"""
    print("=" * 80)
    print("UNIFIED CONTEXT SYSTEM - PHASE 1 IMPLEMENTATION")
    print("High-Velocity Development using ExecutionPlan + GenericOrchestrator")
    print("=" * 80)
    print()

    # Run the async execution
    results = asyncio.run(execute_phase1_plan())

    if results:
        print(f"\n🎯 Phase 1 Implementation COMPLETED!")
        print(
            f"   Check outputs in: /home/opsvi/master_root/apps/project-context/phase1_execution_output/"
        )
        print(f"   Next: Review results and proceed to Phase 2 (Core Ingestion)")
    else:
        print(f"\n❌ Phase 1 Implementation FAILED!")
        print(f"   Check logs for debugging information")


if __name__ == "__main__":
    main()
