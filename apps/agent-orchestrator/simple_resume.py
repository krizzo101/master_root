#!/usr/bin/env python3
"""
Simple Resume - Just continue where we left off
Track state, continue execution
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from src.generic_orchestrator import AgentTask, GenericOrchestrator


async def simple_resume(output_dir: str):
    """Simple resume - just continue from existing state"""

    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"❌ Output directory not found: {output_dir}")
        return False

    tasks_dir = output_path / "tasks"
    if not tasks_dir.exists():
        print(f"❌ Tasks directory not found: {tasks_dir}")
        return False

    print(f"🔄 Resuming orchestrator execution...")
    print(f"📂 Output directory: {output_path}")

    # Load existing tasks and check state
    task_files = list(tasks_dir.glob("*.json"))
    completed_tasks = []
    pending_tasks = []

    for task_file in task_files:
        if task_file.name.endswith("_enhanced.json"):
            continue

        try:
            with open(task_file) as f:
                task_data = json.load(f)

            if task_data.get("status") == "completed" or task_data.get("success"):
                completed_tasks.append(task_file.stem)
            else:
                pending_tasks.append(task_file.stem)
        except:
            continue

    print(f"✅ Completed tasks: {len(completed_tasks)}")
    print(f"⏳ Pending tasks: {len(pending_tasks)}")

    if len(pending_tasks) == 0:
        print("🎉 All tasks already completed!")
        return True

    # Create fresh orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=output_path,
        max_parallel=18,
        master_mcp_registry_path=Path("../../.mcp.json"),
    )

    # Load original task definitions from system_analysis_tasks.json
    tasks_file = Path("system_analysis_tasks.json")
    if tasks_file.exists():
        print(f"📋 Loading task definitions from {tasks_file}")
        orchestrator.load_tasks_from_file(str(tasks_file))

    # Run orchestrator - it should skip completed tasks and continue with pending
    print("🚀 Starting orchestrator execution...")
    await orchestrator.run()

    print("✅ Resume execution completed")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_resume.py <output_directory>")
        print("\nExample:")
        print(
            "python simple_resume.py outputs/analysis/system_analysis_20250907_185730"
        )
        return

    output_dir = sys.argv[1]
    success = asyncio.run(simple_resume(output_dir))

    if success:
        print("🎉 Resume completed successfully!")
    else:
        print("❌ Resume failed!")


if __name__ == "__main__":
    main()
