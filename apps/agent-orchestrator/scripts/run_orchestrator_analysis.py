#!/usr/bin/env python3
"""
Run comprehensive orchestrator capability analysis workflow
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def run_orchestrator_analysis():
    # Load task definition
    task_file = Path(__file__).parent / "orchestrator_analysis_tasks.json"
    with open(task_file, "r") as f:
        workflow = json.load(f)

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / f"orchestrator_analysis_{timestamp}"
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
    print("🔍 ORCHESTRATOR COMPREHENSIVE CAPABILITY ANALYSIS")
    print("=" * 80)
    print(f"📊 Analysis agents: {len(tasks)}")
    print(f"🚀 Max parallel: {workflow['max_parallel']}")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 80)

    print("🎯 ANALYSIS DOMAINS:")
    analysis_domains = [
        "🏗️  Architecture Analysis (solution-architect)",
        "⚡ Performance Analysis (performance-optimizer)",
        "🔒 Security Analysis (security-architect)",
        "👥 Usability Analysis (business-analyst)",
        "📋 Feature Analysis (requirements-analyst)",
        "💻 Code Quality Analysis (code-analyzer)",
        "🏆 Competitive Analysis (research-genius)",
        "📈 Scalability Analysis (devops-automation)",
        "🚀 Innovation Analysis (excellence-optimizer)",
        "📝 Strategic Synthesis (reviewer-critic)",
    ]

    for domain in analysis_domains:
        print(f"   {domain}")

    print("=" * 80)

    # Execute workflow
    print("🚀 Starting comprehensive orchestrator analysis...")
    results = await orchestrator.execute_batch(tasks)

    print("\n" + "=" * 80)
    print("📊 ANALYSIS WORKFLOW COMPLETED")
    print("=" * 80)

    # Print summary
    successful = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    print(f"✅ Successful analyses: {successful}")
    print(f"❌ Failed analyses: {failed}")
    print(f"📈 Success rate: {(successful/len(results)*100):.1f}%")

    # Show failed tasks
    if failed > 0:
        print("\n❌ FAILED ANALYSES:")
        for result in results:
            if result.get("status") == "failed":
                print(
                    f"   • {result.get('task_id', 'unknown')}: {result.get('error', 'unknown error')}"
                )
        print(f"\n💡 Check logs in: {output_dir}/orchestrator.log")
    else:
        print(f"\n🎉 ALL ANALYSES COMPLETED SUCCESSFULLY!")
        print(f"📁 Detailed reports available in: {output_dir}/agents/")

        # List generated analysis reports
        analysis_files = list((output_dir / "agents").glob("*.json"))
        if analysis_files:
            print(f"\n📊 GENERATED ANALYSIS REPORTS:")
            for analysis_file in sorted(analysis_files):
                domain = analysis_file.stem.replace("_", " ").title()
                print(f"   📋 {domain}")

    print("=" * 80)

    return results


if __name__ == "__main__":
    asyncio.run(run_orchestrator_analysis())
