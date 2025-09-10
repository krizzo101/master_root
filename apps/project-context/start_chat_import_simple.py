#!/usr/bin/env python3
"""
Simplified Chat Import with Coordinated Token Pool
Removes potential hanging points for debugging
"""

import asyncio
import sys
from pathlib import Path

# Add orchestrator path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator/src")

from practical_orchestrator import PracticalAgentTask, PracticalOrchestrator


async def start_simple_chat_import():
    """Start chat import with minimal complexity for debugging"""

    print("🚀 Starting SIMPLE coordinated chat import with 7 dedicated tokens")

    # Initialize orchestrator with chat import token pool
    orchestrator = PracticalOrchestrator(
        output_dir="/home/opsvi/master_root/apps/project-context/chat_import_output",
        max_parallel=7,  # Match our 7 token allocation
        enable_monitoring=True,
        enable_quality_reports=True,
        orchestrator_type="chat_import",  # Set type for token coordination
    )

    print("✅ Orchestrator initialized")

    # Simple test task instead of complex Phase 1 tasks
    simple_tasks = [
        PracticalAgentTask(
            task_id="simple_test_task",
            task_type="development-specialist",
            prompt="Create a simple test file to verify the coordinated chat import orchestrator is working correctly.",
            phase_id="test",
            priority="high",
            tags=["test", "coordination"],
        )
    ]

    print(f"📋 Created {len(simple_tasks)} simple test tasks")

    # Execute test tasks with coordinated tokens
    print("🔄 Starting task execution...")
    results = await orchestrator.execute_batch(simple_tasks)

    print("✅ Task execution completed!")

    # Show results
    for i, result in enumerate(results):
        status = (
            result.get("status", "unknown") if isinstance(result, dict) else "error"
        )
        print(f"  Task {i+1}: {status}")

    return results


if __name__ == "__main__":
    print("🧪 Simple Chat Import - Coordinated Token Pool Test")
    print("=" * 60)
    print("Testing with minimal complexity to isolate issues")
    print()

    asyncio.run(start_simple_chat_import())
