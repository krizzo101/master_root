#!/usr/bin/env python3
"""
System Analysis and Documentation Generator
Executes comprehensive multi-agent analysis of the agent-orchestrator system
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


def load_tasks_from_file(file_path: str) -> list:
    """Load task definitions from a JSON file and convert to AgentTask objects"""
    import json

    with open(file_path, "r") as f:
        data = json.load(f)

    tasks = []
    for task_data in data.get("tasks", []):
        tasks.append(AgentTask(**task_data))

    return tasks


async def run_system_analysis():
    """Execute comprehensive system analysis using multiple specialized agents"""

    print("🚀 AGENT-ORCHESTRATOR SYSTEM ANALYSIS & ENHANCEMENT PLANNING")
    print("=" * 80)
    print("This comprehensive analysis will:")
    print("📋 Document current system architecture and capabilities")
    print("🔍 Identify gaps, improvements, and enhancement opportunities")
    print("📊 Generate performance, security, and integration analysis")
    print("📝 Create comprehensive documentation and improvement roadmap")
    print("🛠️  Generate executable implementation plan for next iteration")
    print("=" * 80)

    # Setup paths
    tasks_file = Path(__file__).parent / "system_analysis_tasks.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path(__file__).parent / "outputs" / "analysis" / f"system_analysis_{timestamp}"
    )

    # Load tasks
    print(f"\n📋 Loading analysis tasks from: {tasks_file}")
    try:
        tasks = load_tasks_from_file(str(tasks_file))
        print(f"✅ Loaded {len(tasks)} specialized analysis tasks")
    except Exception as e:
        print(f"❌ Failed to load tasks: {e}")
        return False

    # Print task overview
    print(f"\n🎯 Analysis Workflow Overview:")
    phase_map = {
        "system_discovery": "🔍 Phase 1: System Discovery",
        "capability_analysis": "🏗️  Phase 2: Capability Analysis",
        "documentation_audit": "📝 Phase 3: Documentation Audit",
        "performance_analysis": "⚡ Phase 4: Performance Analysis",
        "security_analysis": "🔒 Phase 5: Security Analysis",
        "integration_analysis": "🔗 Phase 6: Integration Analysis",
        "testing_strategy": "🧪 Phase 7: Testing Strategy",
        "enhancement_prioritization": "📊 Phase 8: Enhancement Prioritization",
        "implementation_plan": "🛠️  Phase 9: Implementation Planning",
        "documentation_generation": "📖 Phase 10: Documentation Generation",
    }

    for task in tasks:
        phase_name = phase_map.get(task.task_id, f"📋 {task.task_id}")
        deps = (
            f" (depends on: {', '.join(task.dependencies)})"
            if task.dependencies
            else " (independent)"
        )
        print(f"  {phase_name}{deps}")

    # Create advanced unified orchestrator with all features enabled
    print(f"\n🔧 Creating Advanced UnifiedOrchestrator...")
    print(
        "Features: Quality Gates, Monitoring, Collaboration, State Persistence, Auto-Recovery"
    )

    config = UnifiedConfig(
        output_dir=output_dir,
        max_parallel=8,  # Allow high parallelism for complex analysis
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
        retry_delay=10.0,  # Allow more time between retries for complex tasks
        enable_state_persistence=True,
        checkpoint_interval=60.0,  # Save state frequently
        enable_monitoring=True,
        enable_collaboration=True,
        enable_quality_gates=True,
    )

    orchestrator = create_advanced_orchestrator(
        output_dir=output_dir, max_parallel=8, tokens=None
    )

    # Execute comprehensive analysis
    print(f"\n⚡ Executing {len(tasks)} analysis tasks with advanced orchestration...")
    print(f"📂 Results will be saved to: {output_dir}")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = datetime.now()

    try:
        # Execute all analysis tasks
        results = await orchestrator.execute_batch(tasks)
        duration = datetime.now() - start_time

        print(f"\n✅ Analysis completed in {duration.total_seconds()/60:.1f} minutes")

    except Exception as e:
        print(f"❌ Analysis execution failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Analyze results
    print("\n" + "=" * 80)
    print("📊 SYSTEM ANALYSIS RESULTS")
    print("=" * 80)

    successful = 0
    failed = 0

    # Handle both dict and list result formats
    if isinstance(results, dict):
        result_items = results.items()
    else:
        result_items = [
            (r.get("task_id", f"task_{i}"), r) for i, r in enumerate(results)
        ]

    print(f"\n📋 Analysis Task Results:")
    for task_id, result in result_items:
        status = result.get("status", "unknown")
        phase_name = phase_map.get(task_id, task_id)

        if status == "completed":
            successful += 1
            print(f"✅ {phase_name}: SUCCESS")
        else:
            failed += 1
            error = result.get("error", "")
            print(
                f"❌ {phase_name}: {status.upper()}" + (f" - {error}" if error else "")
            )

    print(f"\n📊 Overall Results: {successful} successful, {failed} failed")

    # Generate summary report
    print(f"\n📋 Generated Artifacts:")
    if output_dir.exists():
        artifacts = []

        # Check for key output directories and files
        key_paths = [
            ("tasks/", "Individual task results and analysis"),
            ("logs/", "Detailed execution logs and debugging info"),
            ("metrics/", "Performance and execution metrics"),
            ("quality_reports/", "Quality gate results and validations"),
            ("checkpoints/", "State persistence and recovery data"),
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
            print(f"  📁 {output_dir} - Complete analysis results directory")

    # Success assessment
    success_rate = successful / len(tasks) if tasks else 0

    if success_rate >= 0.9:
        print(f"\n🎉 ANALYSIS COMPLETE - HIGH SUCCESS RATE ({success_rate:.1%})")
        print(
            "✨ System analysis generated comprehensive documentation and improvement plan!"
        )
        print(f"📂 Review detailed results in: {output_dir}")
        print("\n🚀 NEXT STEPS:")
        print("1. Review generated documentation and analysis reports")
        print("2. Examine prioritized enhancement recommendations")
        print("3. Execute implementation plan using generated agent tasks")
        print("4. Monitor system improvements and iterate")

    elif success_rate >= 0.7:
        print(f"\n🎯 ANALYSIS MOSTLY COMPLETE ({success_rate:.1%} success)")
        print("📋 Review results and retry failed analyses if needed")

    else:
        print(f"\n⚠️  ANALYSIS INCOMPLETE ({success_rate:.1%} success)")
        print("🔧 Significant issues detected - review logs and retry")

    return success_rate >= 0.7


async def main():
    """Main execution function"""
    try:
        success = await run_system_analysis()
        return 0 if success else 1
    except Exception as e:
        print(f"\n💥 SYSTEM ANALYSIS FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
