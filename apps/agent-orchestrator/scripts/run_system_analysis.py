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


def load_tasks_from_file(file_path: str) -> tuple:
    """Load task definitions from a JSON file and convert to AgentTask objects with parallel agent support"""
    import json

    with open(file_path, "r") as f:
        data = json.load(f)

    # Extract agent execution config
    agent_config = data.get("agent_execution_config", {})
    agent_requirements = agent_config.get("agent_requirements", {})
    max_parallel = agent_requirements.get("max_parallel_agents", 8)

    tasks = []
    for task_data in data.get("tasks", []):
        # Extract agent_config if present
        task_agent_config = task_data.pop("agent_config", {})
        agent_count = task_agent_config.get("agent_count", 1)

        # Create multiple agent instances for parallel execution
        for i in range(agent_count):
            # Create unique task ID for each agent instance
            if agent_count > 1:
                task_id = f"{task_data['task_id']}_agent_{i+1}"
                agent_prompt = f"AGENT {i+1}/{agent_count} - PARALLEL EXECUTION\n\n{task_data['prompt']}"
            else:
                task_id = task_data["task_id"]
                agent_prompt = task_data["prompt"]

            # Handle dependencies - simple mapping to _agent_1 for consistency
            dependencies = []
            for dep in task_data.get("dependencies", []):
                # Simple consistent mapping - always use _agent_1 for multi-agent dependencies
                if not dep.endswith("_agent_1"):
                    dependencies.append(f"{dep}_agent_1")
                else:
                    dependencies.append(dep)  # Already has suffix

            # Create AgentTask with core fields
            task = AgentTask(
                task_id=task_id,
                task_type=task_data["task_type"],
                prompt=agent_prompt,
                dependencies=dependencies,
            )

            # Store agent config as metadata
            if task_agent_config:
                task.metadata = task_agent_config.copy()
                task.metadata["agent_instance"] = i + 1
                task.metadata["total_agents"] = agent_count
                task.metadata["original_task_id"] = task_data["task_id"]

            tasks.append(task)

            print(f"📋 Created agent task: {task_id} ({task_data['task_type']})")

    print(f"🚀 Total agents created: {len(tasks)} (max parallel: {max_parallel})")
    return tasks, max_parallel, agent_requirements


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

    # Load tasks with parallel configuration
    print(f"\n📋 Loading analysis tasks from: {tasks_file}")
    try:
        tasks, max_parallel, agent_requirements = load_tasks_from_file(str(tasks_file))
        print(f"✅ Loaded {len(tasks)} specialized analysis tasks")
        print(f"🔧 Parallel configuration: {max_parallel} max agents")
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
        max_parallel=max_parallel,  # Use configured max parallel agents
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
        output_dir=output_dir, max_parallel=max_parallel, tokens=None
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
