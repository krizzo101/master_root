#!/usr/bin/env python3
"""
Chat Import with Coordinated Token Pool
Uses dedicated 15-token pool for chat import orchestration
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def start_coordinated_chat_import():
    """Start chat import with coordinated token pool"""

    # Initialize orchestrator with chat import token pool
    orchestrator = PracticalOrchestrator(
        output_dir="/home/opsvi/master_root/apps/project-context/chat_import_output",
        max_parallel=7,  # Match our 7 token allocation
        enable_monitoring=True,
        enable_quality_reports=True,
        orchestrator_type="chat_import",  # Set type for token coordination
    )

    # Skip progress callback to avoid potential hanging
    # def progress_handler(event_type: str, data: dict):
    #     print(f"📊 CHAT IMPORT {event_type}: {data}")
    # orchestrator.set_progress_callback(progress_handler)

    print(f"🚀 Starting coordinated chat import with 15 dedicated tokens")
    print(f"📁 Output directory: {orchestrator.output_dir}")
    print(f"⚡ Max parallel: {orchestrator.max_parallel}")
    print()

    # Create simple test tasks first - Phase 1 import was hanging
    tasks = [
        PracticalAgentTask(
            task_id="chat_import_test",
            task_type="development-specialist",
            prompt="Test that coordinated chat import orchestrator is working with proper token allocation.",
            phase_id="test_phase",
            priority="high",
            tags=["coordination", "test"],
        )
    ]

    print(f"📋 Created {len(tasks)} Phase 1 infrastructure tasks:")
    for task in tasks:
        print(f"  • {task.task_id} ({task.task_type})")
    print()

    # Execute Phase 1 tasks with coordinated tokens
    results = await orchestrator.execute_batch(tasks)

    # Print session mapping
    print("\n" + "=" * 60)
    orchestrator.print_session_map()

    print(f"\n✅ Chat import token coordination test complete!")
    print(f"📄 Quality report: {orchestrator.output_dir}/quality_report.json")

    return results


if __name__ == "__main__":
    print("📊 Chat Import - Coordinated Token Pool Test")
    print("=" * 60)
    print("Using dedicated 15-token pool for chat import orchestration")
    print()

    asyncio.run(start_coordinated_chat_import())
