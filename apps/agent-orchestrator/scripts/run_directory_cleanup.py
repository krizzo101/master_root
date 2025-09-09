#!/usr/bin/env python3
"""
Execute the agent-orchestrator directory cleanup workflow
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def run_directory_cleanup():
    # Load cleanup task specification
    task_file = Path(__file__).parent / "directory_cleanup_tasks.json"
    with open(task_file, "r") as f:
        workflow = json.load(f)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"directory_cleanup_{timestamp}"
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

    print("=" * 80)
    print("🧹 AGENT-ORCHESTRATOR DIRECTORY CLEANUP WORKFLOW")
    print("=" * 80)
    print(f"📋 Cleanup phases: {len(tasks)} specialized agents")
    print(f"🚀 Max parallel: {workflow['max_parallel']}")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 80)

    print("🔍 CLEANUP PHASES:")
    phases = [
        "📊 Directory Structure Analysis",
        "🎯 Core Application Identification",
        "🗑️ Obsolete Content Identification",
        "📦 Archive Strategy Design",
        "🏗️ Production Organization Plan",
        "📋 Cleanup Execution Plan",
        "🛡️ Safety Validation System",
        "📄 Cleanup Coordination Report",
    ]

    for i, phase in enumerate(phases, 1):
        print(f"   {i:2}. {phase}")

    print("=" * 80)

    # Execute workflow
    print("🚀 Starting directory cleanup analysis...")
    results = await orchestrator.execute_batch(tasks)

    print("\n" + "=" * 80)
    print("🎉 DIRECTORY CLEANUP WORKFLOW COMPLETED")
    print("=" * 80)

    # Print summary
    successful = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    print(f"✅ Successful phases: {successful}")
    print(f"❌ Failed phases: {failed}")
    print(f"📈 Success rate: {(successful/len(results)*100):.1f}%")

    # Show failed tasks
    if failed > 0:
        print(f"\n❌ FAILED PHASES:")
        for result in results:
            if result.get("status") == "failed":
                print(
                    f"   • {result.get('task_id', 'unknown')}: {result.get('error', 'unknown error')}"
                )
        print(f"\n💡 Check logs in: {output_dir}/orchestrator.log")
    else:
        print(f"\n🎉 DIRECTORY CLEANUP ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"📁 Complete analysis available in: {output_dir}/")

        # Show key deliverables
        deliverable_files = list(output_dir.glob("**/*.md")) + list(
            output_dir.glob("**/*.json")
        )
        if deliverable_files:
            print(f"\n📦 KEY ANALYSIS REPORTS:")
            for deliverable in sorted(deliverable_files)[:10]:  # Show first 10
                rel_path = deliverable.relative_to(output_dir)
                print(f"   📄 {rel_path}")
            if len(deliverable_files) > 10:
                print(f"   ... and {len(deliverable_files) - 10} more files")

    print("=" * 80)
    print("🎯 NEXT STEPS:")
    print("   1. Review cleanup analysis reports")
    print("   2. Validate recommendations and safety procedures")
    print("   3. Execute approved cleanup actions")
    print("   4. Monitor and validate system functionality")
    print("=" * 80)

    return results


if __name__ == "__main__":
    asyncio.run(run_directory_cleanup())
