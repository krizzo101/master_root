#!/usr/bin/env python3
"""
Test swarm using agent-orchestrator with 5 parallel short-lived agents
"""

import asyncio
import sys
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def create_swarm_test():
    """Create 5 parallel monitoring agents for swarm testing"""

    # Define 5 short monitoring tasks
    tasks = [
        AgentTask(
            task_id="file_counter",
            task_type="analysis",
            prompt="Count files by type in current directory. Show top 10 file types with counts. Keep it brief - just the summary table.",
            context={"timeout": 60},
        ),
        AgentTask(
            task_id="git_status",
            task_type="analysis",
            prompt="Check git status, show current branch, and list last 3 commit messages. Brief summary only.",
            context={"timeout": 30},
        ),
        AgentTask(
            task_id="system_resources",
            task_type="analysis",
            prompt="Check disk usage (df -h), memory usage (free -h), and count running processes. Brief summary only.",
            context={"timeout": 30},
        ),
        AgentTask(
            task_id="large_files",
            task_type="analysis",
            prompt="Find the 5 largest files in current directory tree. Show name, size, and location. Brief list only.",
            context={"timeout": 60},
        ),
        AgentTask(
            task_id="code_stats",
            task_type="analysis",
            prompt="Count lines of code by language in current directory. Show top 5 languages with line counts. Brief summary only.",
            context={"timeout": 90},
        ),
    ]

    # Create orchestrator
    orchestrator = GenericOrchestrator(
        max_parallel=5,  # All tasks can run in parallel
        output_dir=Path("/tmp/swarm_test_output"),
    )

    print("🐝 Starting 5-agent swarm test...")
    print(
        "📊 Tasks: File counting, Git status, System resources, Large files, Code stats"
    )
    print("⏰ Expected duration: 1-2 minutes")
    print("🔍 You can monitor with: ./chat-monitor swarm")
    print("")

    # Execute all tasks
    results = await orchestrator.execute_batch(tasks)

    print("✅ Swarm execution complete!")
    print(
        f"📈 Results: {len([r for r in results if r.get('status') == 'completed'])} completed, {len([r for r in results if r.get('status') == 'failed'])} failed"
    )

    return results


if __name__ == "__main__":
    asyncio.run(create_swarm_test())
