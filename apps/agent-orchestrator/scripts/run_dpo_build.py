#!/usr/bin/env python3
"""
Execute the Development Process Orchestrator (DPO) build workflow
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def run_dpo_build():
    # Load DPO implementation request
    task_file = Path(__file__).parent / "dpo_implementation_request.json"
    with open(task_file, "r") as f:
        workflow = json.load(f)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"dpo_build_{timestamp}"
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
    print("🚀 DEVELOPMENT PROCESS ORCHESTRATOR (DPO) BUILD")
    print("=" * 80)
    print(f"📋 Build phases: {len(tasks)} specialized agents")
    print(f"🚀 Max parallel: {workflow['max_parallel']}")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 80)

    print("🏗️ BUILD PHASES:")
    phases = [
        "📋 Requirements Analysis",
        "🏗️ System Architecture Design",
        "🧠 Request Analyzer Implementation",
        "✨ Intelligence Review Engine",
        "📝 SDLC Template System",
        "🔧 Context Injection System",
        "🔗 Orchestrator Integration Layer",
        "🎛️ DPO Main Controller",
        "🧪 Testing & Validation Suite",
        "📚 Documentation Package",
        "🚀 Deployment Integration",
        "✅ Final Validation Report",
    ]

    for i, phase in enumerate(phases, 1):
        print(f"   {i:2}. {phase}")

    print("=" * 80)

    # Execute workflow
    print("🚀 Starting DPO system build...")
    results = await orchestrator.execute_batch(tasks)

    print("\n" + "=" * 80)
    print("🎉 DPO BUILD WORKFLOW COMPLETED")
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
        print(f"\n🎉 DPO SYSTEM BUILD COMPLETED SUCCESSFULLY!")
        print(f"📁 Complete implementation available in: {output_dir}/")

        # Show key deliverables
        deliverable_files = (
            list(output_dir.glob("**/*.py"))
            + list(output_dir.glob("**/*.json"))
            + list(output_dir.glob("**/*.md"))
        )
        if deliverable_files:
            print(f"\n📦 KEY DELIVERABLES:")
            for deliverable in sorted(deliverable_files)[:10]:  # Show first 10
                rel_path = deliverable.relative_to(output_dir)
                print(f"   📄 {rel_path}")
            if len(deliverable_files) > 10:
                print(f"   ... and {len(deliverable_files) - 10} more files")

    print("=" * 80)
    print("🎯 NEXT STEPS:")
    print("   1. Review implementation in output directory")
    print("   2. Run validation tests")
    print("   3. Deploy to master_root ecosystem")
    print("   4. Test with sample development requests")
    print("=" * 80)

    return results


if __name__ == "__main__":
    asyncio.run(run_dpo_build())
