#!/usr/bin/env python3
"""
Run parallel documentation update workflow
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def run_parallel_doc_update():
    # Load task definition
    task_file = Path(__file__).parent / "parallel_doc_update_tasks.json"
    with open(task_file, "r") as f:
        workflow = json.load(f)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"doc_update_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create orchestrator
    orchestrator = GenericOrchestrator(
        output_dir=output_dir, max_parallel=workflow["max_parallel"]
    )

    # Convert JSON tasks to AgentTask objects
    tasks = []
    for task_def in workflow["tasks"]:
        task = AgentTask(
            task_id=task_def["task_id"],
            task_type=task_def["task_type"],
            prompt=task_def["prompt"],
            context=task_def.get("context", {}),
            dependencies=task_def.get("dependencies", []),
        )
        tasks.append(task)

    print(f"Starting parallel documentation update with {len(tasks)} agents...")
    print(f"Max parallel: {workflow['max_parallel']}")
    print(f"Output directory: {output_dir}")

    # Execute workflow - use execute_batch for list of tasks
    results = await orchestrator.execute_batch(tasks)

    print(f"\nWorkflow completed!")
    print(f"Total tasks: {len(results)}")

    # Print summary
    successful = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    # Show failed tasks
    if failed > 0:
        print("\nFailed tasks:")
        for result in results:
            if result.get("status") == "failed":
                print(
                    f"  - {result.get('task_id', 'unknown')}: {result.get('error', 'unknown error')}"
                )
    else:
        print("\n✅ All documentation updates completed successfully!")
        print(f"📁 Results saved to: {output_dir}")

    return results


if __name__ == "__main__":
    asyncio.run(run_parallel_doc_update())
