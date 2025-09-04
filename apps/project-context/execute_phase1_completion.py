#!/usr/bin/env python3
"""
Execute Phase 1 Completion Plan - Final 5 Tasks with Stage Dependencies
Uses EnhancedOrchestrator with proper phase-based execution control
"""
import asyncio
import sys
from pathlib import Path

# Add paths for imports
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")
sys.path.append("/home/opsvi/master_root/apps/project-context")

from enhanced_orchestrator import EnhancedOrchestrator
from execution_plan.adapter import ExecutionPlanAdapter
from phase1_completion_plan import create_phase1_completion_plan
from token_loader import TokenLoader


async def convert_to_enhanced_tasks(execution_plan):
    """Convert ExecutionPlan to EnhancedAgentTasks with deterministic session IDs"""

    adapter = ExecutionPlanAdapter()
    conversion_result = adapter.convert_execution_plan(execution_plan)

    # Extract tasks from the conversion result
    enhanced_tasks = conversion_result["tasks"]

    # Enable monitoring for deterministic session IDs
    for task in enhanced_tasks:
        # Tasks are EnhancedAgentTask objects, set attributes properly
        if hasattr(task, "monitoring_enabled"):
            task.monitoring_enabled = True
        if hasattr(task, "priority_level"):
            task.priority_level = getattr(task, "priority_level", "HIGH")

        # Add Phase 1 completion context
        if not hasattr(task, "context") or not task.context:
            task.context = {}

        task.context.update(
            {
                "phase": "phase1_completion",
                "mission": "Complete final 5 tasks of Phase 1 implementation",
                "foundation_status": "6/11 tasks COMPLETE - all dependencies satisfied",
                "database": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
                "base_directory": "/home/opsvi/master_root/apps/project-context",
                "completed_tasks": [
                    "research_timescale_pgvector",
                    "analyze_existing_systems",
                    "design_unified_schema",
                    "implement_core_schema",
                    "design_ingestion_pipeline",
                    "implement_base_pipeline",
                ],
                "available_resources": [
                    "Working PostgreSQL database with TimescaleDB + pgvector",
                    "Complete base pipeline implementation in src/ingestion/",
                    "Phase 1 execution outputs in phase1_execution_output/",
                    "Production-ready database schema with 30+ indexes",
                ],
            }
        )

    return enhanced_tasks


async def main():
    """Execute Phase 1 completion with stage-based dependencies"""

    print("🚀 PHASE 1 COMPLETION - FINAL 5 TASKS")
    print("=" * 60)
    print("Foundation Status: ✅ 6/11 tasks complete, all dependencies satisfied")
    print("Mission: Complete Phase 1 implementation with stage-based execution")
    print()

    # Load execution plan
    print("📋 Loading Phase 1 completion plan...")
    execution_plan = create_phase1_completion_plan()
    print(f"   Tasks: {len(execution_plan.tasks)}")
    print(f"   Phases: {len(execution_plan.phases)}")
    print(f"   Quality Gates: {len(execution_plan.quality_gates)}")

    # Show phase execution strategy
    print("\n📊 STAGE-BASED EXECUTION STRATEGY:")
    for i, phase in enumerate(execution_plan.phases, 1):
        tasks_in_phase = [
            t for t in execution_plan.tasks if t.phase_id == phase.phase_id
        ]
        deps = (
            f" (depends on: {', '.join(phase.depends_on_phases)})"
            if phase.depends_on_phases
            else ""
        )
        print(f"   Stage {i}: {phase.name}{deps}")
        print(f"      Max Parallel: {phase.max_parallel} tasks")
        print(f"      Tasks: {[t.task_id for t in tasks_in_phase]}")

    # Dynamic token optimization
    token_loader = TokenLoader()
    available_tokens = token_loader.load_tokens()
    token_count = len(available_tokens)

    # Set max_parallel to maximize throughput
    max_parallel = min(token_count, 5)  # Up to 5 parallel for completion velocity

    print(f"\n🎯 Available tokens: {token_count}")
    print(f"⚡ Optimized execution: max_parallel={max_parallel}")

    # Convert to enhanced tasks with deterministic session IDs
    print(f"\n🔄 Converting to EnhancedAgentTasks with deterministic session IDs...")
    enhanced_tasks = await convert_to_enhanced_tasks(execution_plan)

    # Show session ID mappings
    print("\n🎯 DETERMINISTIC SESSION ID MAPPING:")
    for task in enhanced_tasks:
        print(f"   {task.task_id} → {task.agent_uuid}")

    # Set up output directory
    output_dir = Path(
        "/home/opsvi/master_root/apps/project-context/phase1_completion_output"
    )
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {output_dir}")

    # Initialize EnhancedOrchestrator with stage support
    orchestrator = EnhancedOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,  # Use optimal parallelization
        use_optimizations=True,  # Enable performance optimizations
        enable_monitoring=True,  # Enable deterministic session IDs
        enable_quality_gates=True,  # Enable quality gate validation
    )

    print(f"\n⚡ Starting Phase 1 completion with stage-based execution")
    print("🎯 Stage dependencies will be enforced automatically")
    print("🎯 Session logs: ~/.claude/projects/*/[session-id].jsonl")
    print()

    # Execute with stage-based dependencies
    try:
        results = await orchestrator.execute_batch(enhanced_tasks)

        print("\n✅ PHASE 1 COMPLETION EXECUTED!")
        print("=" * 50)

        # Analyze results
        successful = [r for r in results if r.get("status") == "completed"]
        failed = [r for r in results if r.get("status") == "failed"]

        print(f"✅ Successful tasks: {len(successful)}")
        print(f"❌ Failed tasks: {len(failed)}")

        if failed:
            print("\n❌ Failed Tasks:")
            for task in failed:
                print(f"   - {task['task_id']}: {task.get('error', 'Unknown error')}")

        # Success analysis
        completion_rate = len(successful) / len(enhanced_tasks) if enhanced_tasks else 0

        if completion_rate >= 0.8:  # 80% success rate
            total_completed = 6 + len(successful)  # 6 from original + new completions
            print(f"\n🎉 PHASE 1 COMPLETION SUCCESS!")
            print(f"   Phase 1 Status: {total_completed}/11 tasks complete")

            if len(successful) == 5:  # All 5 completion tasks succeeded
                print("   🚀 PHASE 1 FULLY COMPLETE (11/11 tasks)!")
                print("   ✅ Ready for Phase 2 execution")
            else:
                remaining = 5 - len(successful)
                print(f"   ⚠️  {remaining} tasks still need completion")
        else:
            print(f"\n⚠️  Completion rate below target: {completion_rate:.1%}")
            print("   🔧 Review failed tasks and retry")

        print(f"\n📊 Detailed results: {output_dir}")
        print("💡 Monitor sessions: python monitor_multi_phase.py --watch")

    except Exception as e:
        print(f"\n❌ EXECUTION ERROR: {str(e)}")
        print("🔧 Check logs and configuration")
        raise


if __name__ == "__main__":
    asyncio.run(main())
