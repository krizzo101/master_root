#!/usr/bin/env python3
"""
Autonomous Coder - Agent Orchestrator Integration
Integrates the autonomous coding capabilities with the agent orchestrator
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import orchestrator functionality
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-orchestrator" / "src"))
from generic_orchestrator import AgentTask, GenericOrchestrator

logger = logging.getLogger(__name__)


class AutonomousCoderPlugin:
    """
    Plugin that integrates autonomous_coder with the agent orchestrator
    """

    def __init__(self, orchestrator: GenericOrchestrator):
        self.orchestrator = orchestrator
        self.output_base = Path("./output/autonomous_builds")
        self.output_base.mkdir(parents=True, exist_ok=True)

    async def build_from_description(
        self, description: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Build software using the orchestrator with autonomous coder task types
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.output_base / f"build_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🏗️ Starting autonomous build: {description}")
        logger.info(f"📁 Output directory: {output_dir}")

        # Phase 1: Understanding and Analysis
        analysis_tasks = [
            AgentTask(
                task_id="requirements_analysis",
                task_type="requirements-analyst",
                prompt=f"""Analyze the following software request and extract comprehensive requirements:

Request: "{description}"

Provide:
1. Core purpose and functionality
2. User types and personas
3. Functional requirements (detailed list)
4. Non-functional requirements (performance, security, etc.)
5. Implied requirements (logging, monitoring, error handling)
6. Technical constraints and preferences
7. Success criteria

Focus on understanding the true intent and creating actionable requirements.""",
            ),
            AgentTask(
                task_id="architecture_design",
                task_type="solution-architect",
                prompt=f"""Design the architecture for this software request:

Request: "{description}"

Create:
1. High-level system architecture
2. Technology stack recommendations with specific versions
3. Component breakdown and responsibilities
4. Data models and database schema
5. API design (if applicable)
6. Security considerations
7. Deployment architecture
8. Integration points

Provide modern, production-ready architecture following best practices.""",
                dependencies=["requirements_analysis"],
            ),
            AgentTask(
                task_id="research_best_practices",
                task_type="research-genius",
                prompt=f"""Research current best practices for this type of software:

Request: "{description}"

Research:
1. Current industry standards and patterns
2. Popular frameworks and libraries (2024-2025)
3. Security best practices
4. Performance optimization techniques
5. Testing strategies
6. Documentation approaches
7. Common pitfalls and how to avoid them
8. Example implementations and case studies

Focus on modern, actively maintained solutions.""",
            ),
        ]

        logger.info("🔍 Phase 1: Analysis and Research")
        analysis_results = await self.orchestrator.execute_batch(analysis_tasks)

        # Phase 2: Implementation Planning
        planning_tasks = [
            AgentTask(
                task_id="implementation_plan",
                task_type="sdlc-planning",
                prompt=f"""Create a detailed implementation plan based on the analysis:

Request: "{description}"

Use the analysis results to create:
1. Development phases and milestones
2. File structure and organization
3. Implementation priority and sequence
4. Resource requirements
5. Risk assessment and mitigation
6. Testing strategy
7. Timeline estimates

Create a practical, executable plan.""",
                dependencies=[
                    "requirements_analysis",
                    "architecture_design",
                    "research_best_practices",
                ],
            ),
            AgentTask(
                task_id="development_tasks",
                task_type="development-specialist",
                prompt=f"""Based on the requirements and architecture, implement the core functionality:

Request: "{description}"

Implement:
1. Core application structure
2. Main functionality modules
3. Configuration and setup files
4. Error handling and logging
5. Basic documentation
6. Entry points and interfaces

Provide complete, working code following the architectural design.""",
                dependencies=["implementation_plan"],
            ),
            AgentTask(
                task_id="testing_suite",
                task_type="qa-testing-guru",
                prompt=f"""Create comprehensive tests for the implementation:

Request: "{description}"

Develop:
1. Unit tests for core functionality
2. Integration tests
3. End-to-end tests (if applicable)
4. Performance tests
5. Security tests
6. Test data and fixtures
7. Test automation setup
8. Coverage reporting

Ensure high-quality, maintainable test suite.""",
                dependencies=["development_tasks"],
            ),
        ]

        logger.info("🏗️ Phase 2: Implementation")
        implementation_results = await self.orchestrator.execute_batch(planning_tasks)

        # Phase 3: Quality and Optimization
        quality_tasks = [
            AgentTask(
                task_id="code_review",
                task_type="reviewer-critic",
                prompt=f"""Review the implemented code for quality and improvements:

Request: "{description}"

Review:
1. Code quality and adherence to standards
2. Architecture compliance
3. Security vulnerabilities
4. Performance bottlenecks
5. Error handling completeness
6. Documentation quality
7. Testing coverage
8. Maintainability issues

Provide constructive feedback and specific improvement recommendations.""",
                dependencies=["testing_suite"],
            ),
            AgentTask(
                task_id="optimization",
                task_type="performance-optimizer",
                prompt=f"""Optimize the implementation for production use:

Request: "{description}"

Optimize:
1. Performance bottlenecks
2. Resource usage (memory, CPU)
3. Database queries and indexing
4. Caching strategies
5. Error recovery mechanisms
6. Monitoring and observability
7. Scalability considerations
8. Production deployment preparation

Focus on real-world production readiness.""",
                dependencies=["code_review"],
            ),
            AgentTask(
                task_id="documentation",
                task_type="technical-writer",
                prompt=f"""Create comprehensive documentation:

Request: "{description}"

Document:
1. README with setup instructions
2. API documentation (if applicable)
3. Architecture overview
4. Development guide
5. Deployment instructions
6. Configuration reference
7. Troubleshooting guide
8. Examples and tutorials

Create user-friendly, complete documentation.""",
                dependencies=["optimization"],
            ),
        ]

        logger.info("🔍 Phase 3: Quality Assurance")
        quality_results = await self.orchestrator.execute_batch(quality_tasks)

        # Phase 4: Finalization
        final_tasks = [
            AgentTask(
                task_id="production_readiness",
                task_type="sdlc-production",
                prompt=f"""Finalize the implementation for production deployment:

Request: "{description}"

Prepare:
1. Production configuration
2. Environment setup scripts
3. CI/CD pipeline configuration
4. Docker/containerization setup
5. Security hardening checklist
6. Monitoring and alerting setup
7. Backup and recovery procedures
8. Final deployment checklist

Ensure complete production readiness.""",
                dependencies=["documentation"],
            ),
            AgentTask(
                task_id="project_summary",
                task_type="business-analyst",
                prompt=f"""Create a comprehensive project summary and business value assessment:

Request: "{description}"

Summarize:
1. Project objectives and outcomes
2. Technical achievements
3. Business value delivered
4. Quality metrics and test results
5. Performance characteristics
6. Security assessment
7. Maintenance requirements
8. Future enhancement opportunities

Provide executive-level summary with technical details.""",
                dependencies=["production_readiness"],
            ),
        ]

        logger.info("🎯 Phase 4: Finalization")
        final_results = await self.orchestrator.execute_batch(final_tasks)

        # Compile results
        all_results = {
            **analysis_results,
            **implementation_results,
            **quality_results,
            **final_results,
        }

        # Extract key information
        success_count = sum(
            1 for r in all_results.values() if r.get("status") == "completed"
        )
        total_count = len(all_results)

        # Save build summary
        build_summary = {
            "request": description,
            "timestamp": datetime.now().isoformat(),
            "output_directory": str(output_dir),
            "phases_completed": 4,
            "total_tasks": total_count,
            "successful_tasks": success_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "results": {k: v.get("result", v) for k, v in all_results.items()},
        }

        summary_file = output_dir / "build_summary.json"
        with open(summary_file, "w") as f:
            json.dump(build_summary, f, indent=2, default=str)

        logger.info(f"✅ Build complete: {success_count}/{total_count} tasks successful")
        logger.info(f"📄 Summary saved: {summary_file}")

        return build_summary

    async def quick_build(self, description: str, **kwargs) -> Dict[str, Any]:
        """
        Quick build with essential tasks only
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.output_base / f"quick_build_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"⚡ Quick build: {description}")

        tasks = [
            AgentTask(
                task_id="quick_analysis",
                task_type="requirements-analyst",
                prompt=f"Quickly analyze and extract core requirements for: {description}",
            ),
            AgentTask(
                task_id="quick_implementation",
                task_type="development-specialist",
                prompt=f"Create a working prototype/MVP for: {description}",
                dependencies=["quick_analysis"],
            ),
            AgentTask(
                task_id="quick_test",
                task_type="qa-testing-guru",
                prompt=f"Create basic tests for: {description}",
                dependencies=["quick_implementation"],
            ),
        ]

        results = await self.orchestrator.execute_batch(tasks)

        summary = {
            "request": description,
            "build_type": "quick",
            "timestamp": datetime.now().isoformat(),
            "output_directory": str(output_dir),
            "results": results,
        }

        return summary


async def main():
    """
    Main entry point for autonomous coder with orchestrator integration
    """
    if len(sys.argv) < 2:
        print("Usage: python orchestrator_integration.py '<description>' [--quick]")
        print(
            "Example: python orchestrator_integration.py 'Build a REST API for task management'"
        )
        return

    description = sys.argv[1]
    quick_mode = "--quick" in sys.argv

    # Initialize orchestrator
    orchestrator = GenericOrchestrator(max_parallel=8, use_optimizations=True)
    plugin = AutonomousCoderPlugin(orchestrator)

    try:
        if quick_mode:
            result = await plugin.quick_build(description)
        else:
            result = await plugin.build_from_description(description)

        print("\n" + "=" * 60)
        print("🎉 AUTONOMOUS BUILD COMPLETE")
        print("=" * 60)
        print(f"Request: {result['request']}")
        print(f"Build Type: {'Quick' if quick_mode else 'Full'}")
        print(f"Success Rate: {result.get('success_rate', 'N/A')}")
        print(f"Output: {result['output_directory']}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Build failed: {e}")
        print(f"❌ Build failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
