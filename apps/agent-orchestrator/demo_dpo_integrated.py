#!/usr/bin/env python3
"""
Demo: DPO as Integrated Intelligence Layer for Agent-Orchestrator

Shows how DPO enhances orchestrator operations from within.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

# Import DPO components from integrated location
from src.dpo import DevelopmentProcessOrchestrator, DPOConfiguration, RequestAnalysis
from src.dpo.request_analyzer import RequestAnalyzer
from src.dpo.specialist_agent_templates import SpecialistAgentTemplates

# Import orchestrator
from src.generic_orchestrator import AgentTask, GenericOrchestrator


async def demo_integrated_dpo():
    """Demonstrate DPO enhancing orchestrator from within."""

    print("=" * 70)
    print("DEMO: DPO INTEGRATED INTELLIGENCE LAYER")
    print("=" * 70)
    print()

    # Step 1: High-level user request
    user_request = "Build a real-time chat application with user authentication and message history"
    print("📝 USER REQUEST:")
    print(f"   '{user_request}'")
    print()

    # Step 2: DPO analyzes the request
    print("🧠 DPO INTELLIGENCE ANALYSIS:")
    analyzer = RequestAnalyzer()
    analysis = analyzer.analyze(user_request)

    print(f"   Project Type: {analysis.project_type.value}")
    print(f"   Complexity: {analysis.complexity.value}")
    print(f"   Estimated Agents: {analysis.estimated_agents}")
    print(f"   Technologies Detected: {', '.join(analysis.tech_stack.frameworks)}")
    print(f"   Focus Areas: {', '.join(analysis.focus_areas)}")
    print()

    # Step 3: DPO selects specialist agents based on analysis
    print("🤖 DPO SPECIALIST AGENT SELECTION:")
    specialist_templates = SpecialistAgentTemplates()

    # Select agents based on project complexity and type
    if analysis.complexity.value in ["complex", "enterprise"]:
        selected_agents = [
            "requirements-analyst",
            "solution-architect",
            "security-architect",
            "development-specialist",
            "database-specialist",
            "api-integration-specialist",
            "qa-testing-guru",
            "technical-writer",
        ]
    else:
        selected_agents = [
            "requirements-analyst",
            "development-specialist",
            "database-specialist",
            "qa-testing-guru",
        ]

    for agent in selected_agents[:5]:  # Show first 5
        print(f"   ✓ {agent}")
    if len(selected_agents) > 5:
        print(f"   ... and {len(selected_agents) - 5} more specialists")
    print()

    # Step 4: DPO generates enhanced workflow
    print("📋 DPO WORKFLOW GENERATION:")

    # Create orchestrator tasks from DPO intelligence
    tasks = []

    # Phase 1: Requirements & Architecture
    if "requirements-analyst" in selected_agents:
        tasks.append(
            AgentTask(
                task_id="analyze_requirements",
                task_type="requirements-analyst",
                prompt=f"Analyze and document detailed requirements for: {user_request}",
                context={
                    "project_type": analysis.project_type.value,
                    "complexity": analysis.complexity.value,
                    "focus_areas": analysis.focus_areas,
                },
            )
        )

    if "solution-architect" in selected_agents:
        tasks.append(
            AgentTask(
                task_id="design_architecture",
                task_type="solution-architect",
                prompt="Design scalable architecture for real-time chat with WebSocket support",
                dependencies=["analyze_requirements"],
                context={
                    "tech_stack": analysis.tech_stack.to_dict(),
                    "scalability": "high",
                    "real_time": True,
                },
            )
        )

    # Phase 2: Implementation
    tasks.append(
        AgentTask(
            task_id="implement_backend",
            task_type="development-specialist",
            prompt="Implement WebSocket server with authentication and message persistence",
            dependencies=["design_architecture"]
            if "solution-architect" in selected_agents
            else ["analyze_requirements"],
            context={
                "framework": "FastAPI with WebSockets",
                "database": "PostgreSQL + Redis",
                "auth": "JWT tokens",
            },
        )
    )

    tasks.append(
        AgentTask(
            task_id="implement_frontend",
            task_type="development-specialist",
            prompt="Create real-time chat UI with authentication flow",
            dependencies=["implement_backend"],
            context={
                "framework": "React with Socket.io",
                "styling": "Tailwind CSS",
                "state": "Redux for message history",
            },
        )
    )

    # Phase 3: Testing & Documentation
    tasks.append(
        AgentTask(
            task_id="comprehensive_testing",
            task_type="qa-testing-guru",
            prompt="Test real-time messaging, authentication, and message persistence",
            dependencies=["implement_frontend"],
            quality_gates=["performance", "security", "functionality"],
        )
    )

    print(
        f"   Generated {len(tasks)} orchestrated tasks across {len(set(t.task_type for t in tasks))} specialist agents"
    )
    print(
        f"   Workflow includes: Requirements → Architecture → Implementation → Testing"
    )
    print()

    # Step 5: Execute with enhanced orchestrator
    print("🚀 ORCHESTRATOR EXECUTION (with DPO intelligence):")

    output_dir = Path(f"/tmp/demo_dpo_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    orchestrator = GenericOrchestrator(max_parallel=3, output_dir=output_dir)

    print(f"   Output directory: {output_dir}")
    print(f"   Max parallel agents: 3")
    print(f"   Execution mode: DPO-enhanced with specialist selection")
    print()

    # Show task dependency graph
    print("📊 TASK DEPENDENCY GRAPH:")
    for task in tasks:
        deps = (
            f" → depends on: {', '.join(task.dependencies)}"
            if task.dependencies
            else ""
        )
        gates = f" [QG: {', '.join(task.quality_gates)}]" if task.quality_gates else ""
        print(f"   {task.task_id}{deps}{gates}")
    print()

    # Step 6: Show benefits of integration
    print("✨ BENEFITS OF DPO INTEGRATION:")
    print("   1. Intelligent request analysis (not just parsing)")
    print("   2. Automatic specialist agent selection based on complexity")
    print("   3. Context-aware task generation with dependencies")
    print("   4. Quality gates integrated into workflow")
    print("   5. Technology stack detection and configuration")
    print()

    print("=" * 70)
    print("DEMO COMPLETE: DPO is enhancing orchestrator intelligence from within!")
    print("=" * 70)

    # Return the generated workflow for potential execution
    return {
        "analysis": analysis,
        "tasks": tasks,
        "orchestrator": orchestrator,
        "specialist_count": len(selected_agents),
        "complexity": analysis.complexity.value,
    }


async def main():
    """Run the demo."""
    result = await demo_integrated_dpo()

    print("\n💡 READY TO EXECUTE?")
    print("   The workflow is ready to run with real agents.")
    print("   Uncomment the execution line in the script to run it!")

    # Uncomment to actually execute:
    # print("\n🏃 EXECUTING WORKFLOW...")
    # results = await result["orchestrator"].execute_batch(result["tasks"])
    # print(f"✅ Execution complete! Results in: {result['orchestrator'].output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
