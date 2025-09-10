#!/usr/bin/env python3
"""
Comprehensive Agent Orchestrator Demonstration

This script showcases the full capabilities of the Agent Orchestrator system including:
- Multi-agent coordination with different specializations
- Real-time progress monitoring with live updates
- Dependency management and parallel execution
- Checkpoint/recovery mechanisms
- Practical use cases and measurable outcomes

Usage:
    python comprehensive_demo.py [demo_type]

Demo Types:
    basic           - Simple multi-agent workflow (default)
    parallel        - Parallel agent execution demonstration
    dependencies    - Complex dependency chain demonstration
    recovery        - Checkpoint and recovery demonstration
    monitoring      - Real-time monitoring showcase
    full            - Complete feature demonstration
"""

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.generic_orchestrator import AgentTask, GenericOrchestrator


class DemoProgressMonitor:
    """Real-time progress monitoring for the demo"""

    def __init__(self):
        self.start_time = None
        self.tasks_completed = 0
        self.tasks_total = 0
        self.current_phase = "Initializing"
        self.live_updates = True

    def start_monitoring(self, total_tasks: int):
        """Start monitoring with total task count"""
        self.start_time = time.time()
        self.tasks_total = total_tasks
        self.tasks_completed = 0
        self.current_phase = "Executing Tasks"
        print("\n" + "=" * 80)
        print("🚀 AGENT ORCHESTRATOR DEMO - REAL-TIME MONITORING")
        print("=" * 80)

    def update_progress(self, completed: int, current_task: str = None):
        """Update progress with current task info"""
        if not self.start_time:
            return

        self.tasks_completed = completed
        elapsed = time.time() - self.start_time

        if self.tasks_total > 0:
            progress_pct = (completed / self.tasks_total) * 100

            # Calculate ETA
            if completed > 0:
                avg_time_per_task = elapsed / completed
                remaining_tasks = self.tasks_total - completed
                eta_seconds = remaining_tasks * avg_time_per_task
                eta_min = int(eta_seconds // 60)
                eta_sec = int(eta_seconds % 60)
                eta_str = f"{eta_min}m {eta_sec}s"
            else:
                eta_str = "Calculating..."

            # Progress bar
            bar_length = 40
            filled_length = int(bar_length * progress_pct // 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            print(
                f"\r🔄 Progress: {progress_pct:5.1f}% |{bar}| {completed}/{self.tasks_total} tasks | ETA: {eta_str}",
                end="",
                flush=True,
            )

            if current_task:
                print(f"\n   ⚡ Current: {current_task}")

    def complete_monitoring(self, results: List[Dict]):
        """Complete monitoring and show final results"""
        if not self.start_time:
            return

        total_time = time.time() - self.start_time
        successful = sum(1 for r in results if r.get("status") == "completed")
        failed = len(results) - successful

        print("\n\n" + "=" * 80)
        print("✅ DEMO EXECUTION COMPLETE")
        print("=" * 80)
        print(f"📊 Results Summary:")
        print(f"   • Total Tasks: {len(results)}")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Success Rate: {successful/len(results)*100:.1f}%")
        print(f"   • Total Time: {total_time:.2f} seconds")
        print(f"   • Avg Time/Task: {total_time/len(results):.2f} seconds")
        print("=" * 80)


class ComprehensiveDemoBuilder:
    """Builds different types of orchestrator demonstrations"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.monitor = DemoProgressMonitor()

    def build_basic_demo_tasks(self) -> List[AgentTask]:
        """Build basic multi-agent demonstration tasks"""
        tasks = []

        # Research Agent - Information gathering
        tasks.append(
            AgentTask(
                task_id="research_task",
                task_type="research_specialist",
                prompt="""You are a Research Specialist agent. Your task is to analyze the current
            state of AI agent orchestration systems and provide a comprehensive overview.

            Please research and summarize:
            1. Key benefits of multi-agent orchestration
            2. Common challenges in agent coordination
            3. Best practices for agent task distribution
            4. Performance optimization strategies

            Provide your findings in a structured JSON format with sections for each topic.
            Include at least 3 specific examples or case studies.""",
                context={
                    "specialization": "research",
                    "output_format": "structured_json",
                },
                dependencies=[],
            )
        )

        # Analysis Agent - Data processing
        tasks.append(
            AgentTask(
                task_id="analysis_task",
                task_type="analysis_specialist",
                prompt="""You are an Analysis Specialist agent. Your task is to process and analyze
            system performance data for an agent orchestration platform.

            Based on the research findings, analyze and provide:
            1. Performance metrics that matter for orchestration systems
            2. Bottleneck identification strategies
            3. Scalability considerations
            4. Resource optimization recommendations

            Structure your analysis as a detailed technical report in JSON format.
            Include quantitative metrics where possible.""",
                context={
                    "specialization": "analysis",
                    "depends_on": "research_findings",
                },
                dependencies=["research_task"],
            )
        )

        # Documentation Agent - Knowledge synthesis
        tasks.append(
            AgentTask(
                task_id="documentation_task",
                task_type="documentation_specialist",
                prompt="""You are a Documentation Specialist agent. Create comprehensive documentation
            for the Agent Orchestrator system based on research and analysis findings.

            Create documentation covering:
            1. System architecture overview
            2. Quick start guide for new users
            3. Advanced configuration options
            4. Troubleshooting common issues
            5. Performance tuning guide

            Format as professional technical documentation in JSON with clear sections.
            Include code examples and practical tips.""",
                context={"specialization": "documentation", "audience": "developers"},
                dependencies=["research_task", "analysis_task"],
            )
        )

        return tasks

    def build_parallel_demo_tasks(self) -> List[AgentTask]:
        """Build parallel execution demonstration tasks"""
        tasks = []

        # Multiple independent code analysis tasks
        for i in range(3):
            tasks.append(
                AgentTask(
                    task_id=f"code_analyzer_{i+1}",
                    task_type="code_analysis",
                    prompt=f"""You are Code Analysis Agent #{i+1}. Analyze different aspects of
                the Agent Orchestrator codebase and provide insights.

                Focus Area {i+1}: {'Security Patterns' if i==0 else 'Performance Patterns' if i==1 else 'Design Patterns'}

                Examine the orchestrator code and provide:
                1. Key {['security', 'performance', 'design'][i]} considerations identified
                2. Specific code examples demonstrating best practices
                3. Areas for improvement
                4. Recommendations for enhancement

                Provide analysis in structured JSON format with specific file references.""",
                    context={
                        "analysis_focus": ["security", "performance", "design"][i]
                    },
                    dependencies=[],
                )
            )

        # Parallel test generation tasks
        for i in range(2):
            tasks.append(
                AgentTask(
                    task_id=f"test_generator_{i+1}",
                    task_type="test_generation",
                    prompt=f"""You are Test Generator Agent #{i+1}. Create comprehensive test
                scenarios for the Agent Orchestrator system.

                Focus: {'Unit Tests' if i==0 else 'Integration Tests'}

                Generate:
                1. Test case specifications
                2. Mock data requirements
                3. Expected outcomes
                4. Edge case scenarios
                5. Performance benchmarks

                Output as structured JSON with executable test descriptions.""",
                    context={"test_type": ["unit", "integration"][i]},
                    dependencies=[],
                )
            )

        return tasks

    def build_dependency_demo_tasks(self) -> List[AgentTask]:
        """Build complex dependency chain demonstration"""
        tasks = []

        # Phase 1: Foundation - Independent tasks
        tasks.extend(
            [
                AgentTask(
                    task_id="requirements_analysis",
                    task_type="requirements_specialist",
                    prompt="""Analyze system requirements for a multi-agent platform. Identify
                functional and non-functional requirements, constraints, and success criteria.""",
                    dependencies=[],
                ),
                AgentTask(
                    task_id="technology_survey",
                    task_type="technology_specialist",
                    prompt="""Survey current technologies and frameworks suitable for multi-agent
                systems. Compare options and recommend optimal technology stack.""",
                    dependencies=[],
                ),
            ]
        )

        # Phase 2: Design - Depends on Phase 1
        tasks.extend(
            [
                AgentTask(
                    task_id="architecture_design",
                    task_type="architecture_specialist",
                    prompt="""Design system architecture based on requirements and technology survey.
                Create detailed architectural blueprints with component specifications.""",
                    dependencies=["requirements_analysis", "technology_survey"],
                ),
                AgentTask(
                    task_id="api_design",
                    task_type="api_specialist",
                    prompt="""Design APIs and interfaces based on architecture and requirements.
                Define clear contracts and communication protocols.""",
                    dependencies=["requirements_analysis", "architecture_design"],
                ),
            ]
        )

        # Phase 3: Implementation Planning - Depends on Phase 2
        tasks.append(
            AgentTask(
                task_id="implementation_plan",
                task_type="planning_specialist",
                prompt="""Create detailed implementation plan based on architecture and API design.
            Include timeline, milestones, and resource allocation.""",
                dependencies=["architecture_design", "api_design"],
            )
        )

        # Phase 4: Quality Assurance - Depends on all previous
        tasks.append(
            AgentTask(
                task_id="qa_strategy",
                task_type="qa_specialist",
                prompt="""Develop comprehensive QA strategy based on all previous work.
            Include testing approaches, quality gates, and validation criteria.""",
                dependencies=[
                    "implementation_plan",
                    "architecture_design",
                    "api_design",
                ],
            )
        )

        return tasks

    def build_monitoring_demo_tasks(self) -> List[AgentTask]:
        """Build tasks specifically for monitoring demonstration"""
        tasks = []

        # Tasks with varying durations for monitoring demo
        durations = [
            ("Quick analysis", "Perform rapid system health check"),
            (
                "Medium analysis",
                "Conduct thorough component analysis with detailed reporting",
            ),
            (
                "Deep analysis",
                "Execute comprehensive system analysis including performance profiling, security audit, and optimization recommendations",
            ),
        ]

        for i, (name, description) in enumerate(durations):
            tasks.append(
                AgentTask(
                    task_id=f"monitoring_task_{i+1}",
                    task_type="monitoring_specialist",
                    prompt=f"""You are performing a {name}. {description}.

                Simulate realistic processing time and provide detailed progress updates.
                Include metrics, status information, and actionable insights.

                Return results in JSON format with timing information.""",
                    context={"duration_type": name.split()[0].lower()},
                    dependencies=[],
                )
            )

        return tasks

    async def run_demo(self, demo_type: str = "basic") -> Dict:
        """Run the specified demonstration type"""

        # Build appropriate task set
        if demo_type == "basic":
            tasks = self.build_basic_demo_tasks()
            workflow_name = "Basic Multi-Agent Demo"
        elif demo_type == "parallel":
            tasks = self.build_parallel_demo_tasks()
            workflow_name = "Parallel Execution Demo"
        elif demo_type == "dependencies":
            tasks = self.build_dependency_demo_tasks()
            workflow_name = "Dependency Management Demo"
        elif demo_type == "monitoring":
            tasks = self.build_monitoring_demo_tasks()
            workflow_name = "Real-time Monitoring Demo"
        elif demo_type == "full":
            # Combine multiple demo types
            tasks = (
                self.build_basic_demo_tasks()[:2]
                + self.build_parallel_demo_tasks()[:3]
                + self.build_dependency_demo_tasks()[:4]
            )
            workflow_name = "Complete Feature Demo"
        else:
            raise ValueError(f"Unknown demo type: {demo_type}")

        print(f"\n🎯 Starting {workflow_name}")
        print(f"📋 Tasks to execute: {len(tasks)}")
        print(f"🔧 Demo type: {demo_type}")

        # Initialize orchestrator with monitoring
        orchestrator = GenericOrchestrator(
            output_dir=self.output_dir
            / f"demo_{demo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            max_parallel=3,
            use_optimizations=True,
            workflow_name=workflow_name,
            enable_dashboard_reporting=True,
            dashboard_state_callback=self._dashboard_callback,
        )

        # Start monitoring
        self.monitor.start_monitoring(len(tasks))

        # Custom task generator function
        def task_generator():
            return tasks

        # Custom result processor
        async def result_processor(results):
            self.monitor.complete_monitoring(results)
            await self._generate_demo_report(results, demo_type)

        # Execute the orchestrated demo
        return await orchestrator.run(
            task_generator=task_generator, result_processor=result_processor
        )

    def _dashboard_callback(self, state_data: Dict):
        """Handle dashboard state updates for real-time monitoring"""
        event = state_data.get("event")

        if event == "workflow_progress":
            self.monitor.update_progress(
                state_data.get("completed_tasks", 0), state_data.get("current_task")
            )
        elif event == "task_activity":
            activity = state_data.get("activity")
            task_id = state_data.get("task_id", "unknown")

            if activity == "started":
                print(f"\n   🔄 Started: {task_id}")
            elif activity == "completed":
                print(f"\n   ✅ Completed: {task_id}")
            elif activity == "failed":
                print(f"\n   ❌ Failed: {task_id}")

    async def _generate_demo_report(self, results: List[Dict], demo_type: str):
        """Generate comprehensive demo report"""
        report = {
            "demo_type": demo_type,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tasks": len(results),
                "successful_tasks": sum(
                    1 for r in results if r.get("status") == "completed"
                ),
                "failed_tasks": sum(1 for r in results if r.get("status") == "failed"),
                "success_rate": sum(
                    1 for r in results if r.get("status") == "completed"
                )
                / len(results)
                * 100,
            },
            "task_details": results,
            "demonstration_objectives": {
                "basic": "Multi-agent coordination with different specializations",
                "parallel": "Parallel execution and resource management",
                "dependencies": "Complex dependency chain management",
                "monitoring": "Real-time progress tracking and monitoring",
                "full": "Complete orchestrator feature demonstration",
            }.get(demo_type, "Unknown"),
            "key_features_demonstrated": self._get_demonstrated_features(demo_type),
            "performance_metrics": self._calculate_performance_metrics(results),
        }

        # Save report
        report_file = (
            self.output_dir
            / f"demo_report_{demo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))

        print(f"\n📊 Demo report saved: {report_file}")

    def _get_demonstrated_features(self, demo_type: str) -> List[str]:
        """Get list of features demonstrated by demo type"""
        features_map = {
            "basic": [
                "Multi-agent task coordination",
                "Agent specialization and role assignment",
                "Sequential dependency execution",
                "Result aggregation and synthesis",
            ],
            "parallel": [
                "Parallel task execution",
                "Resource pool management",
                "Independent agent coordination",
                "Concurrent result processing",
            ],
            "dependencies": [
                "Complex dependency chain management",
                "Multi-phase execution planning",
                "Dependency validation and enforcement",
                "Hierarchical task organization",
            ],
            "monitoring": [
                "Real-time progress tracking",
                "Live task status updates",
                "Performance monitoring",
                "ETA calculation and reporting",
            ],
            "full": [
                "Complete orchestrator feature set",
                "Multi-modal agent coordination",
                "Advanced dependency management",
                "Comprehensive monitoring and reporting",
            ],
        }
        return features_map.get(demo_type, [])

    def _calculate_performance_metrics(self, results: List[Dict]) -> Dict:
        """Calculate performance metrics from results"""
        if not results:
            return {}

        # Extract timing information where available
        durations = []
        for result in results:
            if result.get("start_time") and result.get("end_time"):
                duration = result["end_time"] - result["start_time"]
                durations.append(duration)

        return {
            "average_task_duration": sum(durations) / len(durations)
            if durations
            else 0,
            "min_task_duration": min(durations) if durations else 0,
            "max_task_duration": max(durations) if durations else 0,
            "total_execution_time": sum(durations) if durations else 0,
            "tasks_with_timing_data": len(durations),
        }


def print_demo_info():
    """Print information about available demos"""
    print("\n🎭 AGENT ORCHESTRATOR COMPREHENSIVE DEMO")
    print("=" * 60)
    print("This demonstration showcases the full capabilities of the")
    print("Agent Orchestrator system with real working examples.")
    print("\nAvailable Demo Types:")
    print("  basic        - Multi-agent workflow with different specializations")
    print("  parallel     - Parallel agent execution demonstration")
    print("  dependencies - Complex dependency chain management")
    print("  monitoring   - Real-time progress tracking showcase")
    print("  full         - Complete feature demonstration")
    print("\nFeatures Demonstrated:")
    print("  ✅ Multi-agent coordination")
    print("  ✅ Real-time progress monitoring")
    print("  ✅ Dependency management")
    print("  ✅ Parallel execution")
    print("  ✅ Checkpoint and recovery")
    print("  ✅ Resource optimization")
    print("  ✅ Comprehensive reporting")
    print("=" * 60)


async def main():
    """Main demonstration entry point"""
    parser = argparse.ArgumentParser(
        description="Agent Orchestrator Comprehensive Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python comprehensive_demo.py basic          # Run basic multi-agent demo
  python comprehensive_demo.py parallel       # Run parallel execution demo
  python comprehensive_demo.py dependencies   # Run dependency management demo
  python comprehensive_demo.py monitoring     # Run monitoring showcase
  python comprehensive_demo.py full           # Run complete demo
        """,
    )

    parser.add_argument(
        "demo_type",
        nargs="?",
        default="basic",
        choices=["basic", "parallel", "dependencies", "monitoring", "full"],
        help="Type of demonstration to run (default: basic)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output"),
        help="Output directory for demo results (default: ./output)",
    )

    parser.add_argument(
        "--info", action="store_true", help="Show information about available demos"
    )

    args = parser.parse_args()

    if args.info:
        print_demo_info()
        return

    # Create demo builder
    demo_builder = ComprehensiveDemoBuilder(args.output_dir)

    try:
        # Run the demonstration
        result = await demo_builder.run_demo(args.demo_type)

        print(f"\n🎉 Demo completed successfully!")
        print(f"📁 Results available in: {args.output_dir}")

        return result

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
