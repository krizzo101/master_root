#!/usr/bin/env python3
"""
Apps Directory Comprehensive Audit
Uses 15-agent swarm to analyze all apps in /apps/ directory
Identifies what works, what doesn't, and what's close to adding value
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.generic_orchestrator import AgentTask
from src.unified.unified_orchestrator import (
    FeatureFlag,
    UnifiedConfig,
    create_advanced_orchestrator,
)


def load_tasks_from_file(file_path: str) -> tuple:
    """Load app audit task definitions"""
    import json

    with open(file_path, "r") as f:
        data = json.load(f)

    agent_config = data.get("agent_execution_config", {})
    agent_requirements = agent_config.get("agent_requirements", {})
    max_parallel = agent_requirements.get("max_parallel_agents", 15)

    tasks = []
    for task_data in data.get("tasks", []):
        task = AgentTask(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            prompt=task_data["prompt"],
            dependencies=task_data.get("dependencies", []),
        )
        tasks.append(task)
        print(f"📋 Loaded: {task.task_id} ({task.task_type})")

    print(f"🚀 Total audit tasks: {len(tasks)} (max parallel: {max_parallel})")
    return tasks, max_parallel, agent_requirements


async def run_apps_audit():
    """Execute comprehensive apps directory audit"""

    print("🔍 APPS DIRECTORY COMPREHENSIVE AUDIT")
    print("=" * 80)
    print("🎯 Analyzing all apps in /apps/ directory using 15-agent swarm")
    print("📊 Determining what works, what doesn't, and what's close to value")
    print("🏠 Cleaning house and prioritizing completion targets")
    print("=" * 80)

    # Setup paths
    tasks_file = Path(__file__).parent / "apps_audit_tasks.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "outputs" / "apps_audit" / f"audit_{timestamp}"

    # Load audit tasks
    print(f"\n📋 Loading audit tasks from: {tasks_file}")
    try:
        tasks, max_parallel, agent_requirements = load_tasks_from_file(str(tasks_file))
        print(f"✅ Loaded {len(tasks)} audit tasks")
        print(f"⚡ Parallel configuration: {max_parallel} max agents")
    except Exception as e:
        print(f"❌ Failed to load tasks: {e}")
        return False

    # Task overview
    print(f"\n🎯 Apps Audit Workflow Overview:")
    for i, task in enumerate(tasks, 1):
        deps = (
            f" (depends on: {', '.join(task.dependencies)})"
            if task.dependencies
            else " (independent)"
        )
        print(f"  {i:2d}. {task.task_id} ({task.task_type}){deps}")

    # Create advanced unified orchestrator
    print(f"\n🔧 Creating Advanced UnifiedOrchestrator...")
    print("✨ Features: All advanced capabilities enabled")

    config = UnifiedConfig(
        output_dir=output_dir,
        max_parallel=max_parallel,
        enabled_features={
            FeatureFlag.ENHANCED_METRICS,
            FeatureFlag.QUALITY_GATES,
            FeatureFlag.AGENT_MONITORING,
            FeatureFlag.COLLABORATION,
            FeatureFlag.AUTO_RECOVERY,
            FeatureFlag.STATE_PERSISTENCE,
            FeatureFlag.BACKGROUND_EXECUTION,
            FeatureFlag.EXECUTION_PLAN,
        },
        enable_auto_recovery=True,
        max_retries=3,
        retry_delay=10.0,
        enable_state_persistence=True,
        checkpoint_interval=60.0,
        enable_monitoring=True,
        enable_collaboration=True,
        enable_quality_gates=True,
    )

    orchestrator = create_advanced_orchestrator(
        output_dir=output_dir, max_parallel=max_parallel, tokens=None
    )

    # Execute comprehensive audit
    print(f"\n⚡ Executing {len(tasks)} audit tasks with 15-agent swarm...")
    print(f"📂 Results will be saved to: {output_dir}")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = datetime.now()

    try:
        results = await orchestrator.execute_batch(tasks)
        duration = datetime.now() - start_time

        print(f"\n✅ Apps audit completed in {duration.total_seconds()/60:.1f} minutes")

    except Exception as e:
        print(f"❌ Audit execution failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Analyze results
    print("\n" + "=" * 80)
    print("📊 APPS AUDIT RESULTS")
    print("=" * 80)

    successful = 0
    failed = 0

    if isinstance(results, dict):
        result_items = results.items()
    else:
        result_items = [
            (r.get("task_id", f"task_{i}"), r) for i, r in enumerate(results)
        ]

    print(f"\n📋 Audit Task Results:")
    for task_id, result in result_items:
        status = result.get("status", "unknown")

        if status == "completed":
            successful += 1
            print(f"✅ {task_id}: SUCCESS")
        else:
            failed += 1
            error = result.get("error", "")
            print(f"❌ {task_id}: {status.upper()}" + (f" - {error}" if error else ""))

    print(f"\n📊 Overall Results: {successful} successful, {failed} failed")

    # Generate summary
    print(f"\n📋 Generated Analysis Artifacts:")
    if output_dir.exists():
        artifacts = []
        key_paths = [
            ("tasks/", "Individual audit results and recommendations"),
            ("logs/", "Detailed execution logs"),
            ("metrics/", "Performance and execution metrics"),
            ("quality_reports/", "Quality gate results"),
            ("checkpoints/", "State persistence data"),
        ]

        for path_name, description in key_paths:
            full_path = output_dir / path_name
            if full_path.exists():
                file_count = len(list(full_path.glob("*"))) if full_path.is_dir() else 1
                artifacts.append(
                    f"  📁 {path_name} - {description} ({file_count} files)"
                )

        if artifacts:
            print("\n".join(artifacts))
        else:
            print(f"  📁 {output_dir} - Complete audit results directory")

    # Success assessment
    success_rate = successful / len(tasks) if tasks else 0

    if success_rate >= 0.9:
        print(f"\n🎉 APPS AUDIT COMPLETE - HIGH SUCCESS RATE ({success_rate:.1%})")
        print("✨ Comprehensive analysis completed! Review results for next steps.")
        print(f"📂 Detailed results in: {output_dir}")
        print("\n🚀 NEXT STEPS:")
        print("1. Review master recommendations in tasks/master_recommendations")
        print("2. Check quick wins identification for immediate actions")
        print("3. Execute consolidation strategy based on findings")
        print("4. Focus resources on highest-value applications")

    elif success_rate >= 0.7:
        print(f"\n🎯 AUDIT MOSTLY COMPLETE ({success_rate:.1%} success)")
        print("📋 Review results and retry failed analyses if needed")

    else:
        print(f"\n⚠️  AUDIT INCOMPLETE ({success_rate:.1%} success)")
        print("🔧 Significant issues detected - review logs and retry")

    return success_rate >= 0.7


async def main():
    """Main execution function"""
    try:
        success = await run_apps_audit()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 APPS AUDIT FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
