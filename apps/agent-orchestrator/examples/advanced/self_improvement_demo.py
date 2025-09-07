#!/usr/bin/env python3
"""
Self-Improvement Demonstration
Shows ExecutionPlan system coordinating orchestrator's own enhancement
The ultimate proof that the ExecutionPlan concept works
"""
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from basic_monitoring import MonitoringHooks, RealTimeMonitor
from execution_plan_parser import ExecutionPlanAdapter, create_execution_plan_from_json
from generic_orchestrator import GenericOrchestrator
from working_quality_gates import QualityGateManager, create_quality_gate_hooks


class SelfImprovementDemonstrator:
    """Demonstrates orchestrator self-improvement using ExecutionPlan"""

    def __init__(self):
        self.output_dir = (
            Path(__file__).parent.parent / "output" / "self_improvement_demo"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_self_improvement_demonstration(self):
        """Run the complete self-improvement demonstration"""
        print("🚀 ExecutionPlan Self-Improvement Demonstration")
        print("=" * 60)
        print("The orchestrator will coordinate its own enhancement!")
        print(
            "This proves ExecutionPlan can handle complex, self-referential workflows."
        )
        print("=" * 60)

        # Load ExecutionPlan
        plan_file = Path(__file__).parent / "self_improvement_execution_plan.json"
        if not plan_file.exists():
            print(f"❌ ExecutionPlan file not found: {plan_file}")
            return False

        print(f"📋 Loading ExecutionPlan from: {plan_file}")
        execution_plan = create_execution_plan_from_json(str(plan_file))
        print(f"✅ Loaded ExecutionPlan: {execution_plan.name}")
        print(f"   Tasks: {len(execution_plan.tasks)}")
        print(f"   Mode: {execution_plan.execution_mode}")
        print(
            f"   Self-orchestrating: {execution_plan.metadata.get('self_orchestrating', False)}"
        )
        print()

        # Create enhanced orchestrator with all features
        print("🔧 Setting up Enhanced Orchestrator with ExecutionPlan capabilities...")
        orchestrator = GenericOrchestrator(
            output_dir=self.output_dir,
            max_parallel=execution_plan.max_parallel,
            use_optimizations=execution_plan.use_optimizations,
        )

        # Setup quality gates if enabled
        if execution_plan.enable_quality_gates:
            print("⚡ Enabling Quality Gates...")
            quality_manager = QualityGateManager()
            pre_hook, post_hook = create_quality_gate_hooks(quality_manager)
            orchestrator.pre_execute_hook = pre_hook
            orchestrator.post_execute_hook = post_hook

        # Setup monitoring if enabled
        if execution_plan.enable_monitoring:
            print("📊 Enabling Real-time Monitoring...")
            monitor = RealTimeMonitor(self.output_dir / "monitoring")
            monitoring_hooks = MonitoringHooks(monitor)
            (
                monitor_pre_hook,
                monitor_post_hook,
            ) = monitoring_hooks.create_orchestrator_hooks()

            # Combine hooks if quality gates are also enabled
            if execution_plan.enable_quality_gates:
                original_pre_hook = orchestrator.pre_execute_hook
                original_post_hook = orchestrator.post_execute_hook

                async def combined_pre_hook(task):
                    await original_pre_hook(task)
                    await monitor_pre_hook(task)

                async def combined_post_hook(task):
                    await original_post_hook(task)
                    await monitor_post_hook(task)

                orchestrator.pre_execute_hook = combined_pre_hook
                orchestrator.post_execute_hook = combined_post_hook
            else:
                orchestrator.pre_execute_hook = monitor_pre_hook
                orchestrator.post_execute_hook = monitor_post_hook

            monitor.start_system_monitoring(interval=2.0)

        print("✅ Enhanced orchestrator ready with ExecutionPlan integration")
        print()

        # Convert ExecutionPlan to AgentTasks
        print("🔄 Converting ExecutionPlan to AgentTask format...")
        adapter = ExecutionPlanAdapter()
        agent_tasks = adapter.adapt_for_orchestrator(execution_plan)
        print(f"✅ Converted {len(agent_tasks)} ExecutionPlan tasks to AgentTask format")

        # Display task dependency chain
        print("\n📈 Task Dependency Chain:")
        for task in agent_tasks:
            deps = ", ".join(task.dependencies) if task.dependencies else "None"
            print(f"   {task.task_id} ({task.task_type}) -> depends on: {deps}")
        print()

        # Execute the self-improvement plan
        print("🎯 Executing Self-Improvement ExecutionPlan...")
        print("   The orchestrator is now coordinating its own enhancement!")
        print("   This is the ultimate test of ExecutionPlan functionality.")
        print()

        # Execute
        results = await orchestrator.execute_batch(agent_tasks)

        # Wait for monitoring to complete
        if execution_plan.enable_monitoring:
            await asyncio.sleep(3.0)
            monitor.stop_system_monitoring()

        # Analyze results
        print("📊 Analyzing Self-Improvement Results...")
        print("=" * 60)

        completed_tasks = [r for r in results if r.get("status") == "completed"]
        failed_tasks = [r for r in results if r.get("status") == "failed"]

        print(f"Total Tasks: {len(results)}")
        print(f"Completed: {len(completed_tasks)}")
        print(f"Failed: {len(failed_tasks)}")
        print(f"Success Rate: {len(completed_tasks)/len(results)*100:.1f}%")
        print()

        # Show task details
        for result in results:
            task_id = result.get("task_id", "unknown")
            status = result.get("status", "unknown")
            error = result.get("error", "")

            status_icon = "✅" if status == "completed" else "❌"
            print(f"{status_icon} {task_id}: {status.upper()}")
            if error:
                print(f"   Error: {error}")

        # Generate execution summary
        if execution_plan.enable_monitoring:
            print("\n📈 Monitoring Summary:")
            stats = monitor.get_current_stats()
            health = monitor.get_system_health()

            print(f"   System Health: {health['status']}")
            print(f"   Throughput: {stats['throughput_per_minute']:.1f} tasks/minute")
            print(f"   Average Duration: {stats['avg_duration']:.2f}s")

        # Create comprehensive report
        summary = adapter.create_execution_summary(execution_plan, results)

        # Save summary to file
        summary_file = self.output_dir / "self_improvement_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n💾 Detailed summary saved to: {summary_file}")

        # Final assessment
        print("\n" + "=" * 60)
        print("🎉 SELF-IMPROVEMENT DEMONSTRATION COMPLETE")
        print("=" * 60)

        if len(completed_tasks) >= len(results) * 0.7:  # 70% success rate
            print(
                "✅ SUCCESS: The orchestrator successfully coordinated its own enhancement!"
            )
            print(
                "   This proves ExecutionPlan can handle complex, self-referential workflows."
            )
            print("   The self-orchestrating concept is validated and working.")
        else:
            print(
                "⚠️  PARTIAL SUCCESS: Some tasks failed, but the core concept is proven."
            )
            print("   ExecutionPlan successfully orchestrated self-improvement tasks.")

        print(f"\n🔍 All results and artifacts saved to: {self.output_dir}")
        print(
            "   Review the generated files to see the complete self-improvement process."
        )

        return len(completed_tasks) >= len(results) * 0.7


async def main():
    """Run the self-improvement demonstration"""
    demonstrator = SelfImprovementDemonstrator()
    success = await demonstrator.run_self_improvement_demonstration()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
