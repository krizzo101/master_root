#!/usr/bin/env python3
"""
Collaborative Orchestrator Example
Demonstrates how to use the CollaborativeOrchestrator for multi-agent collaboration
"""

import asyncio

# Add src to path for imports
import sys
import tempfile
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent.parent / "src"))

from collaborative_orchestrator import (
    CollaborationConfig,
    CollaborativeOrchestrator,
    CollaborativeTask,
    run_traditional,
)
from generic_orchestrator import AgentTask


async def example_collaborative_research():
    """Example: Collaborative research project with multiple agents"""

    print("=" * 60)
    print("COLLABORATIVE RESEARCH EXAMPLE")
    print("=" * 60)

    # Create orchestrator with collaboration enabled
    output_dir = Path(tempfile.mkdtemp(prefix="collaborative_research_"))

    collaboration_config = CollaborationConfig(
        enable_messaging=True,
        enable_shared_workspace=True,
        enable_team_formation=True,
        team_formation_mode="skill-based",
        max_team_size=5,
    )

    orchestrator = CollaborativeOrchestrator(
        output_dir=output_dir,
        max_parallel=3,
        collaboration_config=collaboration_config,
    )

    # Define collaborative tasks
    tasks = [
        CollaborativeTask(
            task_id="research_foundations",
            task_type="research",
            prompt="""Research the foundations of multi-agent systems and collaboration patterns.
            Focus on:
            1. Key principles of multi-agent collaboration
            2. Communication patterns between agents
            3. Coordination mechanisms

            Share your findings with other team members for synthesis.""",
            collaboration_enabled=True,
            required_capabilities=["research", "analysis"],
            collaboration_mode="shared",
        ),
        CollaborativeTask(
            task_id="research_implementation",
            task_type="research",
            prompt="""Research implementation approaches for multi-agent collaboration.
            Focus on:
            1. Technical architectures for agent collaboration
            2. Message passing systems
            3. Shared workspace implementations

            Build on the foundations research and coordinate with architecture team.""",
            dependencies=["research_foundations"],
            collaboration_enabled=True,
            required_capabilities=["research", "technical_analysis"],
            collaboration_mode="shared",
        ),
        CollaborativeTask(
            task_id="synthesis_report",
            task_type="synthesis",
            prompt="""Synthesize research findings from the team into a comprehensive report.

            Review all research from team members and create:
            1. Executive summary of key findings
            2. Technical recommendations
            3. Implementation roadmap

            This is a collaborative synthesis - work with all team members.""",
            dependencies=["research_foundations", "research_implementation"],
            collaboration_enabled=True,
            required_capabilities=["synthesis", "writing", "coordination"],
            collaboration_mode="review",
        ),
    ]

    # Execute collaborative research
    results = await orchestrator.run_collaborative(
        tasks=tasks,
        collaboration_config={
            "team_formation_mode": "auto",
            "max_team_size": 3,
        },
    )

    print(f"\nCollaborative Research Results:")
    print(f"Output Directory: {output_dir}")
    print(f"Total Tasks: {results['metrics']['total']}")
    print(f"Completed: {results['metrics']['completed']}")
    print(f"Failed: {results['metrics']['failed']}")
    print(f"Collaboration Events: {len(results['collaboration_events'])}")
    print(f"Messages Exchanged: {len(results['message_history'])}")

    return results


async def example_software_development_team():
    """Example: Multi-agent software development team"""

    print("\n" + "=" * 60)
    print("COLLABORATIVE SOFTWARE DEVELOPMENT EXAMPLE")
    print("=" * 60)

    # Create orchestrator
    output_dir = Path(tempfile.mkdtemp(prefix="collaborative_dev_"))

    collaboration_config = CollaborationConfig(
        enable_messaging=True,
        enable_shared_workspace=True,
        enable_team_formation=True,
        team_formation_mode="manual",  # Specific role assignments
        max_team_size=4,
    )

    orchestrator = CollaborativeOrchestrator(
        output_dir=output_dir,
        max_parallel=2,  # Allow parallel development
        collaboration_config=collaboration_config,
    )

    # Define development tasks with specific agent assignments
    tasks = [
        CollaborativeTask(
            task_id="architect_agent",
            task_type="architecture",
            prompt="""As the system architect, design a simple async web service.

            Create:
            1. System architecture diagram
            2. API specification
            3. Component design
            4. Database schema

            Share your architecture with the development team in the shared workspace.""",
            collaboration_enabled=True,
            assigned_agents=["architect_agent"],
            required_capabilities=["architecture", "design", "planning"],
            collaboration_mode="handoff",
        ),
        CollaborativeTask(
            task_id="backend_dev_agent",
            task_type="implementation",
            prompt="""As the backend developer, implement the web service based on the architecture.

            Build:
            1. FastAPI web service
            2. Database models
            3. API endpoints
            4. Business logic

            Coordinate with the architect and frontend developer.""",
            dependencies=["architect_agent"],
            collaboration_enabled=True,
            assigned_agents=["backend_dev_agent"],
            required_capabilities=["python", "fastapi", "databases"],
            collaboration_mode="shared",
        ),
        CollaborativeTask(
            task_id="frontend_dev_agent",
            task_type="implementation",
            prompt="""As the frontend developer, create a web interface for the service.

            Build:
            1. HTML/CSS interface
            2. JavaScript for API calls
            3. User interaction logic
            4. Basic styling

            Work with backend developer to integrate APIs.""",
            dependencies=["architect_agent"],
            collaboration_enabled=True,
            assigned_agents=["frontend_dev_agent"],
            required_capabilities=["javascript", "html", "css", "ui"],
            collaboration_mode="shared",
        ),
        CollaborativeTask(
            task_id="test_agent",
            task_type="testing",
            prompt="""As the test engineer, create comprehensive tests for the application.

            Create:
            1. Unit tests for backend
            2. Integration tests for APIs
            3. Frontend functionality tests
            4. Test automation scripts

            Review all code from the team and ensure quality.""",
            dependencies=["backend_dev_agent", "frontend_dev_agent"],
            collaboration_enabled=True,
            assigned_agents=["test_agent"],
            required_capabilities=["testing", "pytest", "automation"],
            collaboration_mode="review",
        ),
    ]

    # Execute development project
    results = await orchestrator.run_collaborative(
        tasks=tasks,
        collaboration_config={
            "workspace_sync_interval": 0.5,  # Faster sync for development
            "collaboration_timeout": 600.0,  # Longer timeout for complex tasks
        },
    )

    print(f"\nSoftware Development Results:")
    print(f"Output Directory: {output_dir}")
    print(f"Total Tasks: {results['metrics']['total']}")
    print(f"Completed: {results['metrics']['completed']}")
    print(f"Failed: {results['metrics']['failed']}")
    print(f"Collaboration Events: {len(results['collaboration_events'])}")

    # Show team assignments
    for task_result in results["results"]:
        task_id = task_result["task_id"]
        assigned_agents = task_result.get("assigned_agents", [])
        print(
            f"  {task_id}: {', '.join(assigned_agents) if assigned_agents else 'auto-assigned'}"
        )

    return results


async def example_backwards_compatibility():
    """Example: Using CollaborativeOrchestrator in traditional mode"""

    print("\n" + "=" * 60)
    print("BACKWARDS COMPATIBILITY EXAMPLE")
    print("=" * 60)

    # Create collaborative orchestrator
    output_dir = Path(tempfile.mkdtemp(prefix="traditional_mode_"))

    orchestrator = CollaborativeOrchestrator(
        output_dir=output_dir,
        max_parallel=3,
        # No collaboration config = traditional mode
    )

    def generate_traditional_tasks() -> List[AgentTask]:
        """Generate traditional tasks (no collaboration)"""
        return [
            AgentTask(
                task_id="task_1",
                task_type="analysis",
                prompt="Analyze the benefits of async programming in Python",
                dependencies=[],
            ),
            AgentTask(
                task_id="task_2",
                task_type="research",
                prompt="Research best practices for error handling in async code",
                dependencies=["task_1"],
            ),
            AgentTask(
                task_id="task_3",
                task_type="synthesis",
                prompt="Create a summary of async programming best practices",
                dependencies=["task_1", "task_2"],
            ),
        ]

    async def process_results(results: List[dict]):
        """Process results (traditional pattern)"""
        print("\nTraditional Results Summary:")
        for result in results:
            print(f"  {result['task_id']}: {result['status']}")

    # Use traditional interface (backwards compatible)
    results = await run_traditional(
        orchestrator=orchestrator,
        task_generator=generate_traditional_tasks,
        result_processor=process_results,
    )

    print(f"\nTraditional Mode Results:")
    print(f"Output Directory: {output_dir}")
    print(f"Total Tasks: {results['metrics']['total']}")
    print(f"Completed: {results['metrics']['completed']}")
    print(f"Failed: {results['metrics']['failed']}")
    print("No collaboration features used - fully backwards compatible!")

    return results


async def example_hybrid_mode():
    """Example: Hybrid mode - some tasks collaborative, others traditional"""

    print("\n" + "=" * 60)
    print("HYBRID MODE EXAMPLE")
    print("=" * 60)

    # Create orchestrator in hybrid mode
    output_dir = Path(tempfile.mkdtemp(prefix="hybrid_mode_"))

    orchestrator = CollaborativeOrchestrator(
        output_dir=output_dir,
        max_parallel=3,
        collaboration_config=CollaborationConfig(
            enable_messaging=True,
            enable_shared_workspace=True,
        ),
    )

    # Enable hybrid mode
    orchestrator.enable_hybrid_mode()

    # Mix of collaborative and traditional tasks
    tasks = [
        # Traditional task (no collaboration)
        CollaborativeTask(
            task_id="individual_research",
            task_type="research",
            prompt="Research authentication patterns for web APIs",
            collaboration_enabled=False,  # Traditional execution
        ),
        # Collaborative tasks
        CollaborativeTask(
            task_id="team_design",
            task_type="design",
            prompt="Collaboratively design an authentication system based on research",
            dependencies=["individual_research"],
            collaboration_enabled=True,
            required_capabilities=["design", "security"],
            collaboration_mode="shared",
        ),
        CollaborativeTask(
            task_id="team_review",
            task_type="review",
            prompt="Review and improve the authentication design as a team",
            dependencies=["team_design"],
            collaboration_enabled=True,
            collaboration_mode="review",
        ),
        # Another traditional task
        CollaborativeTask(
            task_id="individual_documentation",
            task_type="documentation",
            prompt="Create final documentation for the authentication system",
            dependencies=["team_review"],
            collaboration_enabled=False,  # Back to traditional
        ),
    ]

    # Execute in hybrid mode
    results = await orchestrator.run_collaborative(tasks=tasks)

    print(f"\nHybrid Mode Results:")
    print(f"Output Directory: {output_dir}")
    print(f"Total Tasks: {results['metrics']['total']}")
    print(f"Completed: {results['metrics']['completed']}")
    print(f"Failed: {results['metrics']['failed']}")

    # Show which tasks used collaboration
    for task_result in results["results"]:
        task_id = task_result["task_id"]
        collaboration_enabled = task_result.get("collaboration_enabled", False)
        mode = "Collaborative" if collaboration_enabled else "Traditional"
        print(f"  {task_id}: {mode}")

    return results


async def main():
    """Run all examples"""

    print("🤖 COLLABORATIVE ORCHESTRATOR EXAMPLES")
    print(
        "This demonstrates the enhanced GenericOrchestrator with collaboration features"
    )

    try:
        # Example 1: Collaborative research
        await example_collaborative_research()

        # Example 2: Software development team
        await example_software_development_team()

        # Example 3: Backwards compatibility
        await example_backwards_compatibility()

        # Example 4: Hybrid mode
        await example_hybrid_mode()

        print("\n" + "=" * 60)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("The CollaborativeOrchestrator provides:")
        print("  • Real-time agent messaging")
        print("  • Shared workspace collaboration")
        print("  • Intelligent team formation")
        print("  • Multiple collaboration modes")
        print("  • Full backwards compatibility")
        print("  • Hybrid execution options")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
