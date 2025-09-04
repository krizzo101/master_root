#!/usr/bin/env python3
"""
Execute the Unified Context System Phase 3 ExecutionPlan with maximum optimization
Advanced Features & Intelligence Implementation with deterministic session IDs
"""
import asyncio
import os
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from unified_context_phase3_plan import create_unified_context_phase3_plan

from src.enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
from src.execution_plan.adapter import ExecutionPlanAdapter
from src.token_loader import TokenLoader


async def convert_execution_plan_to_enhanced_agent_tasks(execution_plan):
    """Convert ExecutionPlan to EnhancedAgentTasks with deterministic session IDs"""

    # Use the ExecutionPlanAdapter for proper conversion
    adapter = ExecutionPlanAdapter()

    # Convert ExecutionPlan to EnhancedAgentTasks with deterministic UUIDs
    enhanced_tasks = adapter.convert_execution_plan(execution_plan)

    # Enable monitoring for all tasks to get deterministic session IDs
    for task in enhanced_tasks:
        task.monitoring_enabled = True
        task.priority_level = getattr(task, "priority_level", "MEDIUM")

        # Add Phase 3 specific context
        if not task.context:
            task.context = {}

        task.context.update(
            {
                "phase": "phase3",
                "phase_description": "Advanced Features & Intelligence Implementation",
                "base_directory": "/home/opsvi/master_root/apps/project-context",
                "phase1_outputs": "phase1_execution_output/",
                "phase2_outputs": "phase2_execution_output/",
                "database_container": "unified_context_postgres",
                "quality_requirements": [
                    "Implement advanced features and intelligence capabilities",
                    "Integrate with Phase 1 database schema and Phase 2 ingestion",
                    "Focus on ML/AI features and advanced analytics",
                    "Ensure production-ready, scalable implementation",
                ],
            }
        )

    return enhanced_tasks


async def main():
    """Execute Phase 3 with optimized parallelization and deterministic session IDs"""
    print("🚀 UNIFIED CONTEXT SYSTEM - PHASE 3 EXECUTION")
    print("=" * 60)
    print("Mission: Advanced Features & Intelligence Implementation")
    print("Optimization: Maximum parallel execution with deterministic session IDs")
    print()

    # Dynamic token-based optimization
    token_loader = TokenLoader()
    available_tokens = token_loader.load_tokens()
    token_count = len(available_tokens)

    print(f"🎯 Available tokens: {token_count}")

    # Set max_parallel to maximize throughput with available tokens
    max_parallel = min(
        token_count, 10
    )  # Use up to 10 parallel executions for maximum velocity

    print(f"⚡ Optimized parallel execution: max_parallel={max_parallel}")
    print()

    # Load Phase 3 execution plan
    print("📋 Loading Phase 3 ExecutionPlan...")
    execution_plan = create_unified_context_phase3_plan()
    print(f"   Tasks: {len(execution_plan.tasks)}")
    print(f"   Quality Gates: {len(execution_plan.quality_gates)}")

    # Show task breakdown
    print("\n📊 Task breakdown by specialist:")
    task_types = {}
    for task in execution_plan.tasks:
        agent_type = task.task_type.value
        task_types[agent_type] = task_types.get(agent_type, 0) + 1

    for agent_type, count in sorted(task_types.items()):
        print(f"   {agent_type}: {count} tasks")

    # Convert to EnhancedAgentTask format with deterministic session IDs
    print(
        f"\n🔄 Converting {len(execution_plan.tasks)} ExecutionPlan tasks to EnhancedAgentTask format..."
    )
    enhanced_tasks = await convert_execution_plan_to_enhanced_agent_tasks(
        execution_plan
    )

    # Show deterministic session IDs
    print("\n🎯 DETERMINISTIC SESSION ID MAPPING:")
    for task in enhanced_tasks:
        print(f"   {task.task_id} → {task.agent_uuid}")

    # Set up optimized output directory
    output_dir = Path(
        "/home/opsvi/master_root/apps/project-context/phase3_execution_output"
    )
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {output_dir}")

    # Initialize EnhancedOrchestrator with MAXIMUM parallelization
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,  # Use all available tokens for maximum speed!
        use_optimizations=True,  # Enable performance optimizations
        enable_monitoring=True,  # Enable session monitoring with deterministic UUIDs
    )

    print(f"\n⚡ Starting Phase 3 execution with max_parallel={max_parallel}")
    print("🎯 Expected 60%+ time savings vs sequential execution")
    print("🎯 Session logs available at: ~/.claude/projects/*/[session-id].jsonl")
    print()

    # Execute all tasks with automatic dependency resolution and parallel optimization
    try:
        results = await orchestrator.execute_batch(enhanced_tasks)

        print("\n✅ PHASE 3 EXECUTION COMPLETED!")
        print("=" * 50)

        # Analyze results
        successful_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        print(f"✅ Successful tasks: {len(successful_tasks)}")
        print(f"❌ Failed tasks: {len(failed_tasks)}")

        if failed_tasks:
            print("\n❌ Failed Tasks:")
            for task in failed_tasks:
                print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

        print(f"\n📊 Results saved to: {output_dir}")

        # Show session monitoring info
        print("\n🎯 SESSION MONITORING:")
        print("   Each task has a deterministic session ID for easy log tracking")
        print(
            "   Monitor sessions with: tail -f ~/.claude/projects/*/[session-id].jsonl"
        )
        print("   Or use: python monitor_multi_phase.py --watch")

        # Success criteria
        success_rate = len(successful_tasks) / len(results) if results else 0
        if success_rate >= 0.8:  # 80% success rate
            print("\n🎉 Phase 3 execution meets success criteria!")
            print("🚀 Advanced features successfully implemented!")
        else:
            print("\n⚠️  Phase 3 execution below success threshold")
            print("🔧 Review failed tasks before moving to final phases")

    except Exception as e:
        print(f"\n❌ PHASE 3 EXECUTION ERROR: {str(e)}")
        print("🔧 Check logs and retry with individual task debugging")
        raise


if __name__ == "__main__":
    asyncio.run(main())
