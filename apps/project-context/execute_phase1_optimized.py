#!/usr/bin/env python3
"""
Optimized execution script for Unified Context System Phase 1
Uses maximum available tokens for parallel execution
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from unified_context_phase1_plan import create_unified_context_phase1_plan

from src.generic_orchestrator import AgentTask, GenericOrchestrator
from src.token_loader import TokenLoader


def convert_execution_plan_to_agent_tasks(execution_plan):
    """Convert ExecutionPlan tasks to AgentTask format"""
    agent_tasks = []

    for task in execution_plan.tasks:
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
                if isinstance(value, list) and value:
                    prompt_parts.append(f"- {key}:")
                    for item in value:
                        prompt_parts.append(f"  • {item}")
                elif value and not isinstance(value, (list, dict)):
                    prompt_parts.append(f"- {key}: {value}")
                elif isinstance(value, dict) and value:
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


async def execute_phase1_optimized():
    """Execute Phase 1 with maximum parallelization"""
    print("🚀 Executing Unified Context System Phase 1 - OPTIMIZED VERSION")

    # Check available tokens
    token_loader = TokenLoader()
    available_tokens = token_loader.load_tokens()
    token_count = len(available_tokens)

    print(f"🎯 Available tokens: {token_count}")

    # Set max_parallel to maximize throughput with available tokens
    max_parallel = min(
        token_count, 10
    )  # Use up to 10 parallel executions for maximum velocity

    print(f"⚡ Optimized parallel execution: max_parallel={max_parallel}")

    # Create execution plan
    execution_plan = create_unified_context_phase1_plan()
    print(f"📋 ExecutionPlan loaded: {len(execution_plan.tasks)} tasks")

    # Convert to AgentTask format
    agent_tasks = convert_execution_plan_to_agent_tasks(execution_plan)

    # Set up output directory
    output_dir = Path(
        "/home/opsvi/master_root/apps/project-context/phase1_optimized_output"
    )
    output_dir.mkdir(exist_ok=True)

    # Initialize GenericOrchestrator with OPTIMIZED parallelization
    orchestrator = GenericOrchestrator(
        output_dir=output_dir, max_parallel=max_parallel  # Use all available tokens!
    )

    print(f"🏗️  Orchestrator configured for maximum throughput")
    print(f"📁 Output directory: {output_dir}")
    print()

    try:
        print("🎯 Starting OPTIMIZED execution with full token utilization...")
        results = await orchestrator.execute_batch(agent_tasks)

        print(f"\n✅ Execution completed! {len(results)} tasks processed")

        # Analyze results
        successful_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        print(f"   ✅ Successful: {len(successful_tasks)}")
        print(f"   ❌ Failed: {len(failed_tasks)}")

        # Calculate time savings from parallelization
        total_time = max([r.get("duration_ms", 0) for r in results]) / 1000
        sequential_time = sum([r.get("duration_ms", 0) for r in results]) / 1000
        time_savings = (
            ((sequential_time - total_time) / sequential_time * 100)
            if sequential_time > 0
            else 0
        )

        print(f"\n⚡ PARALLELIZATION EFFICIENCY:")
        print(f"   Sequential time: {sequential_time:.1f}s")
        print(f"   Parallel time: {total_time:.1f}s")
        print(f"   Time savings: {time_savings:.1f}%")
        print(f"   Throughput multiplier: {sequential_time/total_time:.1f}x")

        return results

    except Exception as e:
        print(f"❌ Execution failed: {str(e)}")
        return None


def main():
    """Main execution with optimization focus"""
    print("=" * 80)
    print("UNIFIED CONTEXT SYSTEM - PHASE 1 OPTIMIZED IMPLEMENTATION")
    print("Maximum Token Utilization for 10x Development Velocity")
    print("=" * 80)
    print()

    results = asyncio.run(execute_phase1_optimized())

    if results:
        print(f"\n🎯 OPTIMIZED Phase 1 Implementation COMPLETED!")
        print(f"   Maximum parallelization achieved with available token pool")
        print(f"   Check outputs in phase1_optimized_output/ directory")
    else:
        print(f"\n❌ Optimized execution failed - check logs")


if __name__ == "__main__":
    main()
