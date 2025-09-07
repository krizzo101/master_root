#!/usr/bin/env python3
"""
UnifiedOrchestrator Demonstration Examples
=========================================

This file provides comprehensive examples of how to use the UnifiedOrchestrator
with different configurations, features, and use cases. Each example demonstrates
specific capabilities and best practices.

Based on validation results from the comprehensive testing suite.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# from typing import List  # Unused import removed

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.unified.enhanced_agent_task import EnhancedAgentTask, TaskFactory
from src.unified.unified_orchestrator import (
    FeatureFlag,
    UnifiedConfig,
    UnifiedOrchestrator,
    create_advanced_orchestrator,
    create_minimal_orchestrator,
    create_standard_orchestrator,
)


class UnifiedOrchestratorDemos:
    """Collection of demonstration examples for UnifiedOrchestrator usage"""

    def __init__(self, base_output_dir: Path):
        self.base_output_dir = base_output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    async def demo_01_minimal_configuration(self):
        """
        Demo 1: Minimal Configuration

        Shows the simplest way to use the orchestrator with no enhanced features.
        Perfect for basic task orchestration without complexity.
        """
        print("\n🔵 DEMO 1: Minimal Configuration")
        print("=" * 50)

        # Create minimal orchestrator (no enhanced features)
        orchestrator = create_minimal_orchestrator(
            output_dir=self.base_output_dir / "demo_01_minimal",
            max_parallel=3,
            tokens=None,  # Use default token management
        )

        # Create simple tasks
        tasks = [
            EnhancedAgentTask(
                task_id="minimal_task_1",
                task_type="general-purpose",
                prompt="Create a simple hello world Python script and run it.",
                validation_required=False,
                monitoring_enabled=False,
            ),
            EnhancedAgentTask(
                task_id="minimal_task_2",
                task_type="general-purpose",
                prompt="List the current directory contents and create a simple text file.",
                dependencies=["minimal_task_1"],
                validation_required=False,
                monitoring_enabled=False,
            ),
            EnhancedAgentTask(
                task_id="minimal_task_3",
                task_type="general-purpose",
                prompt="Read the text file created by task 2 and display its contents.",
                dependencies=["minimal_task_2"],
                validation_required=False,
                monitoring_enabled=False,
            ),
        ]

        print(f"📋 Executing {len(tasks)} simple tasks with minimal orchestrator...")

        try:
            # Execute tasks
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Minimal configuration demo completed successfully!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            return result

        except Exception as e:
            print(f"❌ Minimal demo failed: {e}")
            return None

    async def demo_02_standard_configuration(self):
        """
        Demo 2: Standard Configuration

        Shows the standard orchestrator with enhanced metrics, background execution,
        and auto-recovery. Good for production use.
        """
        print("\n🟡 DEMO 2: Standard Configuration")
        print("=" * 50)

        # Create standard orchestrator with common features
        orchestrator = create_standard_orchestrator(
            output_dir=self.base_output_dir / "demo_02_standard",
            max_parallel=4,
            tokens=None,
        )

        # Create tasks with enhanced features
        tasks = []

        # Task with auto-recovery capability
        tasks.append(
            EnhancedAgentTask(
                task_id="standard_task_resilient",
                task_type="qa-testing-guru",
                prompt="""
            Test resilience and auto-recovery:
            1. Create a Python script that might fail initially
            2. Implement retry logic and error handling
            3. Demonstrate successful recovery
            4. Generate a resilience report
            """,
                validation_required=True,
                monitoring_enabled=True,
                metadata={"max_retries": 3, "expected_failures": 1},
            )
        )

        # Background task
        tasks.append(
            EnhancedAgentTask(
                task_id="standard_task_background",
                task_type="general-purpose",
                prompt="""
            Background processing demonstration:
            1. Create a long-running simulation (use sleep)
            2. Generate progress reports every 30 seconds
            3. Create final summary when complete
            """,
                background_execution=True,
                monitoring_enabled=True,
                metadata={"estimated_duration": 120},
            )
        )

        # Metrics collection task
        tasks.append(
            EnhancedAgentTask(
                task_id="standard_task_metrics",
                task_type="general-purpose",
                prompt="""
            Enhanced metrics demonstration:
            1. Create several small subtasks with different durations
            2. Collect timing and performance metrics
            3. Generate a performance analysis report
            4. Test metrics export functionality
            """,
                dependencies=["standard_task_resilient"],
                validation_required=True,
                monitoring_enabled=True,
            )
        )

        print(f"📋 Executing {len(tasks)} tasks with standard orchestrator...")
        print(
            "🔧 Features enabled: Enhanced Metrics, Background Execution, Auto-Recovery"
        )

        try:
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Standard configuration demo completed!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            if "enhanced_metrics" in result:
                print("📈 Enhanced metrics collected:")
                print(
                    f"  - Task types: {result['enhanced_metrics'].get('tasks_by_type', {})}"
                )
                print(
                    f"  - Recovery attempts: {result['enhanced_metrics'].get('recovery_attempts', 0)}"
                )

            return result

        except Exception as e:
            print(f"❌ Standard demo failed: {e}")
            return None

    async def demo_03_advanced_configuration(self):
        """
        Demo 3: Advanced Configuration

        Shows the full-featured orchestrator with all capabilities enabled.
        Demonstrates quality gates, collaboration, monitoring, and state persistence.
        """
        print("\n🔴 DEMO 3: Advanced Configuration")
        print("=" * 50)

        # Create advanced orchestrator with all features
        orchestrator = create_advanced_orchestrator(
            output_dir=self.base_output_dir / "demo_03_advanced",
            max_parallel=5,
            tokens=None,
        )

        # Create advanced tasks with teams and quality gates
        tasks = []

        # Research team task
        tasks.append(
            EnhancedAgentTask(
                task_id="advanced_research_task",
                task_type="research-genius",
                prompt="""
            Research Phase - Advanced Orchestrator Demo:
            1. Research best practices for agent orchestration
            2. Analyze performance optimization techniques
            3. Create comprehensive research report
            4. Provide recommendations for implementation
            """,
                team_id="research_team",
                phase_id="research_phase",
                validation_required=True,
                quality_gates=["research_quality", "documentation_quality"],
                metadata={
                    "collaboration_mode": "shared",
                    "quality_threshold": 8.0,
                    "deliverable_type": "research_report",
                },
            )
        )

        # Development team task
        tasks.append(
            EnhancedAgentTask(
                task_id="advanced_development_task",
                task_type="development-specialist",
                prompt="""
            Development Phase - Advanced Orchestrator Demo:
            1. Implement orchestrator optimization features based on research
            2. Create comprehensive test suite
            3. Implement monitoring and logging enhancements
            4. Generate development documentation
            """,
                dependencies=["advanced_research_task"],
                team_id="development_team",
                phase_id="development_phase",
                validation_required=True,
                quality_gates=[
                    "code_quality",
                    "test_coverage",
                    "performance_standards",
                ],
                metadata={
                    "collaboration_mode": "handoff",
                    "quality_threshold": 9.0,
                    "deliverable_type": "working_code",
                },
            )
        )

        # Quality assurance task
        tasks.append(
            EnhancedAgentTask(
                task_id="advanced_qa_task",
                task_type="qa-testing-guru",
                prompt="""
            Quality Assurance Phase - Advanced Orchestrator Demo:
            1. Perform comprehensive testing of developed features
            2. Validate performance improvements
            3. Test error handling and edge cases
            4. Generate QA report with recommendations
            """,
                dependencies=["advanced_development_task"],
                team_id="qa_team",
                phase_id="qa_phase",
                validation_required=True,
                quality_gates=[
                    "test_completeness",
                    "bug_detection",
                    "performance_validation",
                ],
                metadata={
                    "collaboration_mode": "review",
                    "quality_threshold": 9.5,
                    "deliverable_type": "qa_report",
                },
            )
        )

        # Integration task (uses multiple teams)
        tasks.append(
            EnhancedAgentTask(
                task_id="advanced_integration_task",
                task_type="solution-architect",
                prompt="""
            Integration Phase - Advanced Orchestrator Demo:
            1. Integrate all deliverables from research, development, and QA
            2. Create unified deployment package
            3. Validate end-to-end functionality
            4. Generate final integration report
            """,
                dependencies=[
                    "advanced_research_task",
                    "advanced_development_task",
                    "advanced_qa_task",
                ],
                team_id="integration_team",
                phase_id="integration_phase",
                validation_required=True,
                quality_gates=["integration_completeness", "deployment_readiness"],
                background_execution=False,
                metadata={
                    "collaboration_mode": "hybrid",
                    "quality_threshold": 10.0,
                    "deliverable_type": "deployment_package",
                    "requires_all_dependencies": True,
                },
            )
        )

        print(f"📋 Executing {len(tasks)} advanced tasks with full orchestrator...")
        print(
            "🚀 Features enabled: ALL - Quality Gates, Monitoring, Collaboration, State Persistence, Auto-Recovery"
        )
        print("👥 Teams: research_team, development_team, qa_team, integration_team")

        try:
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Advanced configuration demo completed!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            if "enhanced_metrics" in result:
                enhanced = result["enhanced_metrics"]
                print("🔬 Advanced metrics collected:")
                print(f"  - Team performance: {enhanced.get('team_performance', {})}")
                print(
                    f"  - Quality gate results: {enhanced.get('quality_gate_results', {})}"
                )
                print(f"  - Checkpoint saves: {enhanced.get('checkpoint_saves', 0)}")
                print(f"  - Recovery attempts: {enhanced.get('recovery_attempts', 0)}")

            if "module_status" in result:
                print("🔧 Module status:")
                for module, status in result["module_status"].items():
                    print(f"  - {module}: {status}")

            return result

        except Exception as e:
            print(f"❌ Advanced demo failed: {e}")
            return None

    async def demo_04_custom_configuration(self):
        """
        Demo 4: Custom Configuration

        Shows how to create custom configurations for specific use cases.
        Demonstrates fine-tuned feature selection and custom settings.
        """
        print("\n🟢 DEMO 4: Custom Configuration")
        print("=" * 50)

        # Create custom configuration for specific needs
        custom_config = UnifiedConfig(
            output_dir=self.base_output_dir / "demo_04_custom",
            max_parallel=6,
            # Enable specific features only
            enabled_features={
                FeatureFlag.ENHANCED_METRICS,
                FeatureFlag.BACKGROUND_EXECUTION,
                FeatureFlag.AUTO_RECOVERY,
                FeatureFlag.STATE_PERSISTENCE,
            },
            # Custom settings
            enable_auto_recovery=True,
            max_retries=5,
            retry_delay=2.0,
            enable_state_persistence=True,
            checkpoint_interval=30.0,
            # Monitoring disabled for this demo
            enable_monitoring=False,
            enable_collaboration=False,
            enable_quality_gates=False,
        )

        orchestrator = UnifiedOrchestrator(custom_config)

        # Create tasks demonstrating custom features
        tasks = []

        # High-reliability task with custom retry settings
        tasks.append(
            EnhancedAgentTask(
                task_id="custom_reliable_task",
                task_type="qa-testing-guru",
                prompt="""
            High Reliability Test:
            1. Create a task that simulates intermittent failures
            2. Test the custom retry configuration (5 retries, 2-second delay)
            3. Demonstrate successful completion after retries
            4. Generate reliability metrics
            """,
                validation_required=True,
                metadata={
                    "failure_simulation": True,
                    "expected_retries": 2,
                    "success_probability": 0.6,
                },
            )
        )

        # State persistence demonstration
        tasks.append(
            EnhancedAgentTask(
                task_id="custom_persistence_task",
                task_type="general-purpose",
                prompt="""
            State Persistence Test:
            1. Create a long-running task that updates state frequently
            2. Test checkpoint creation (every 30 seconds)
            3. Simulate interruption and recovery
            4. Validate state consistency after recovery
            """,
                background_execution=True,
                validation_required=True,
                metadata={
                    "checkpoints_expected": 3,
                    "state_updates": 10,
                    "recovery_test": True,
                },
            )
        )

        # Performance optimization task
        tasks.append(
            EnhancedAgentTask(
                task_id="custom_performance_task",
                task_type="performance-optimizer",
                prompt="""
            Performance Optimization Test:
            1. Create multiple parallel subtasks to test max_parallel=6
            2. Measure resource utilization and throughput
            3. Test enhanced metrics collection
            4. Generate performance analysis report
            """,
                dependencies=["custom_reliable_task"],
                validation_required=True,
                metadata={
                    "subtasks_count": 12,
                    "parallel_limit_test": True,
                    "metrics_focus": "performance",
                },
            )
        )

        print(f"📋 Executing {len(tasks)} tasks with custom configuration...")
        print(
            "⚙️ Custom settings: max_parallel=6, max_retries=5, checkpoint_interval=30s"
        )
        print("🎯 Focus: Reliability, Performance, State Management")

        try:
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Custom configuration demo completed!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            # Show custom configuration effectiveness
            if "enhanced_metrics" in result:
                enhanced = result["enhanced_metrics"]
                print("⚡ Custom configuration metrics:")
                print(f"  - Recovery attempts: {enhanced.get('recovery_attempts', 0)}")
                print(f"  - Checkpoint saves: {enhanced.get('checkpoint_saves', 0)}")
                print(
                    f"  - Average duration by type: {enhanced.get('average_duration_by_type', {})}"
                )

            return result

        except Exception as e:
            print(f"❌ Custom demo failed: {e}")
            return None

    async def demo_05_task_factory_patterns(self):
        """
        Demo 5: Task Factory Patterns

        Demonstrates the TaskFactory utility for creating common task patterns.
        Shows best practices for different types of tasks.
        """
        print("\n🟣 DEMO 5: Task Factory Patterns")
        print("=" * 50)

        orchestrator = create_standard_orchestrator(
            output_dir=self.base_output_dir / "demo_05_factory", max_parallel=4
        )

        tasks = []

        # Simple task using factory
        simple_task = TaskFactory.create_simple_task(
            task_id="factory_simple",
            task_type="general-purpose",
            prompt="Create and execute a simple data processing script.",
            dependencies=[],
        )
        tasks.append(simple_task)

        # Monitored task using factory
        monitored_task = TaskFactory.create_monitored_task(
            task_id="factory_monitored",
            task_type="general-purpose",
            prompt="Perform monitored data analysis with real-time tracking.",
            team_id="analytics_team",
            dependencies=["factory_simple"],
        )
        tasks.append(monitored_task)

        # Quality-gated task using factory
        quality_task = TaskFactory.create_quality_gated_task(
            task_id="factory_quality",
            task_type="development-specialist",
            prompt="Create high-quality code with comprehensive testing.",
            quality_gates=["code_standards", "test_coverage", "documentation"],
            phase_id="quality_phase",
            dependencies=["factory_monitored"],
        )
        tasks.append(quality_task)

        # Background task using factory
        background_task = TaskFactory.create_background_task(
            task_id="factory_background",
            task_type="general-purpose",
            prompt="Run background data processing and report generation.",
            team_id="background_team",
            dependencies=[],
        )
        tasks.append(background_task)

        print(f"📋 Executing {len(tasks)} factory-created tasks...")
        print("🏭 Factory patterns: Simple, Monitored, Quality-Gated, Background")

        try:
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Task factory patterns demo completed!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            # Show factory pattern effectiveness
            print("🏭 Factory pattern analysis:")
            for task in tasks:
                print(
                    f"  - {task.task_id}: {task.__class__.__name__} with UUID {task.agent_uuid[:8]}..."
                )
                print(
                    f"    Monitoring: {task.monitoring_enabled}, Validation: {task.validation_required}"
                )

            return result

        except Exception as e:
            print(f"❌ Factory patterns demo failed: {e}")
            return None

    async def demo_06_error_handling_showcase(self):
        """
        Demo 6: Error Handling Showcase

        Demonstrates robust error handling, recovery mechanisms,
        and graceful degradation capabilities.
        """
        print("\n🔥 DEMO 6: Error Handling Showcase")
        print("=" * 50)

        # Configure orchestrator with strong error handling
        config = UnifiedConfig(
            output_dir=self.base_output_dir / "demo_06_error_handling",
            max_parallel=3,
            enabled_features={
                FeatureFlag.AUTO_RECOVERY,
                FeatureFlag.ENHANCED_METRICS,
                FeatureFlag.STATE_PERSISTENCE,
            },
            enable_auto_recovery=True,
            max_retries=4,
            retry_delay=1.0,
        )

        orchestrator = UnifiedOrchestrator(config)

        tasks = []

        # Task designed to fail and recover
        tasks.append(
            EnhancedAgentTask(
                task_id="error_recovery_test",
                task_type="qa-testing-guru",
                prompt="""
            Error Recovery Demonstration:
            1. Create a script that fails 70% of the time initially
            2. Implement progressive improvement in success rate
            3. Demonstrate successful completion after retries
            4. Log all recovery attempts with detailed analysis
            """,
                validation_required=True,
                metadata={
                    "intended_failures": 2,
                    "success_progression": [0.3, 0.5, 0.8, 1.0],
                    "recovery_demo": True,
                },
            )
        )

        # Task with dependency on potentially failing task
        tasks.append(
            EnhancedAgentTask(
                task_id="error_dependent_task",
                task_type="general-purpose",
                prompt="""
            Dependency Error Handling:
            1. Wait for error_recovery_test to complete
            2. Handle case where dependency might have failed
            3. Implement fallback strategies
            4. Generate resilience report
            """,
                dependencies=["error_recovery_test"],
                validation_required=True,
                metadata={"fallback_enabled": True, "dependency_tolerance": "high"},
            )
        )

        # Task to test system stability under errors
        tasks.append(
            EnhancedAgentTask(
                task_id="error_stability_test",
                task_type="qa-testing-guru",
                prompt="""
            System Stability Under Errors:
            1. Generate multiple controlled error conditions
            2. Test system response to various failure modes
            3. Validate error isolation and containment
            4. Verify system continues operating normally
            """,
                validation_required=True,
                metadata={
                    "error_types": [
                        "timeout",
                        "memory",
                        "file_not_found",
                        "permission",
                    ],
                    "stability_test": True,
                },
            )
        )

        print(f"📋 Testing error handling with {len(tasks)} challenging tasks...")
        print("💪 Recovery settings: max_retries=4, retry_delay=1.0s")
        print("🛡️ Focus: Auto-recovery, Error isolation, System stability")

        try:
            result = await orchestrator.run(
                task_generator=lambda: tasks, result_processor=None
            )

            print("✅ Error handling showcase completed!")
            print(
                f"📊 Results: {result['metrics']['completed']}/{result['metrics']['total']} tasks completed"
            )

            # Analyze error handling effectiveness
            if "enhanced_metrics" in result:
                recovery_attempts = result["enhanced_metrics"].get(
                    "recovery_attempts", 0
                )
                print(f"🔧 Recovery attempts made: {recovery_attempts}")
                print("🛡️ Error handling demonstrated successfully!")

            return result

        except Exception as e:
            print(f"❌ Error handling demo failed: {e}")
            print(
                "📝 Note: Some failures are expected in this demo to test recovery mechanisms"
            )
            return None

    async def run_all_demos(self):
        """Run all demonstration examples in sequence"""

        print("🚀 UNIFIED ORCHESTRATOR COMPREHENSIVE DEMO SUITE")
        print("=" * 80)
        print("This demo suite showcases all major features and configurations")
        print("of the UnifiedOrchestrator system through practical examples.")
        print("=" * 80)

        demos = [
            ("Minimal Configuration", self.demo_01_minimal_configuration),
            ("Standard Configuration", self.demo_02_standard_configuration),
            ("Advanced Configuration", self.demo_03_advanced_configuration),
            ("Custom Configuration", self.demo_04_custom_configuration),
            ("Task Factory Patterns", self.demo_05_task_factory_patterns),
            ("Error Handling Showcase", self.demo_06_error_handling_showcase),
        ]

        results = {}

        for demo_name, demo_func in demos:
            print(f"\n▶️ Starting: {demo_name}")
            try:
                start_time = datetime.now()
                result = await demo_func()
                duration = datetime.now() - start_time

                results[demo_name] = {
                    "success": result is not None,
                    "duration": duration.total_seconds(),
                    "result": result,
                }

                if result:
                    print(f"✅ {demo_name} completed in {duration.total_seconds():.1f}s")
                else:
                    print(f"⚠️ {demo_name} completed with issues")

            except Exception as e:
                print(f"💥 {demo_name} failed: {e}")
                results[demo_name] = {"success": False, "error": str(e), "duration": 0}

        # Generate summary report
        print("\n" + "=" * 80)
        print("📊 DEMO SUITE EXECUTION SUMMARY")
        print("=" * 80)

        successful_demos = sum(1 for r in results.values() if r["success"])
        total_demos = len(demos)

        print(f"✅ Successful demos: {successful_demos}/{total_demos}")
        print(
            f"⏱️ Total execution time: {sum(r.get('duration', 0) for r in results.values()):.1f}s"
        )

        for demo_name, result in results.items():
            status = "✅" if result["success"] else "❌"
            duration = result.get("duration", 0)
            print(f"{status} {demo_name}: {duration:.1f}s")

        # Save comprehensive results
        results_file = self.base_output_dir / "demo_suite_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📋 Complete results saved to: {results_file}")

        if successful_demos == total_demos:
            print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
            print(
                "✨ UnifiedOrchestrator is fully functional and ready for production use!"
            )
        elif successful_demos >= total_demos * 0.8:
            print("🎯 Most demos completed successfully - system is largely functional")
        else:
            print("⚠️ Multiple demo failures - system may need additional work")

        return results


async def main():
    """Main execution function"""

    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path(__file__).parent.parent / f"unified_orchestrator_demos_{timestamp}"
    )

    # Create and run demo suite
    demo_suite = UnifiedOrchestratorDemos(output_dir)

    try:
        results = await demo_suite.run_all_demos()

        # Return success if most demos passed
        success_rate = sum(1 for r in results.values() if r["success"]) / len(results)
        return success_rate >= 0.8

    except Exception as e:
        print(f"\n💥 DEMO SUITE FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
