#!/usr/bin/env python3
"""
Phase 2 Execution with Coordinated Token Pool
Uses dedicated 6-token pool for Phase 2 orchestration
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def start_coordinated_phase2():
    """Start Phase 2 with coordinated token pool"""

    # Initialize orchestrator with Phase 2 token pool
    orchestrator = PracticalOrchestrator(
        output_dir="/home/opsvi/master_root/apps/project-context/phase2_output",
        max_parallel=6,  # Match our 6 token allocation
        enable_monitoring=True,
        enable_quality_reports=True,
    )

    # Set orchestrator type for token coordination
    orchestrator._orchestrator_type = "phase2"

    # Set up progress monitoring
    def progress_handler(event_type: str, data: dict):
        print(f"🚀 PHASE 2 {event_type}: {data}")

    orchestrator.set_progress_callback(progress_handler)

    print(f"🚀 Starting coordinated Phase 2 with 6 dedicated tokens")
    print(f"📁 Output directory: {orchestrator.output_dir}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Add your Phase 2 tasks here
    phase2_tasks = [
        PracticalAgentTask(
            task_id="phase2_preparation",
            task_type="solution-architect",
            prompt="Prepare Phase 2 execution plan and validate system readiness for Phase 2 tasks.",
            phase_id="phase2_prep",
            priority="high",
            tags=["phase2", "preparation"],
        )
        # Add more Phase 2 tasks as needed
    ]

    # Execute Phase 2 tasks
    results = await orchestrator.execute_batch(phase2_tasks)

    # Print session mapping
    print("\n" + "=" * 60)
    orchestrator.print_session_map()

    print(f"\n✅ Phase 2 execution complete!")
    print(f"📄 Quality report: {orchestrator.output_dir}/quality_report.json")

    return results


if __name__ == "__main__":
    print("🚀 Phase 2 Execution - Coordinated Token Pool")
    print("=" * 60)
    print("Using dedicated 6-token pool for Phase 2 orchestration")
    print()

    asyncio.run(start_coordinated_phase2())
