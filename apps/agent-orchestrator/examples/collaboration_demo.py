#!/usr/bin/env python3
"""
Real-Time Multi-Agent Collaboration Demo

Demonstrates the full capabilities of the collaboration architecture including:
- Real-time agent messaging
- Dynamic task handoffs
- Shared workspace collaboration
- Event-driven coordination
- Performance monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collaboration import (
    AgentCapability,
    CollaborationOrchestrator,
    CollaborationType,
    CollaborativeTask,
    Priority,
    TaskRequirements,
)


async def basic_collaboration_demo():
    """Basic collaboration demo with 3 agents working together"""

    print("🚀 REAL-TIME MULTI-AGENT COLLABORATION DEMO")
    print("=" * 60)
    print("Demonstrating collaborative software development workflow")
    print()

    # Create collaboration orchestrator
    orchestrator = CollaborationOrchestrator(
        output_dir=Path("./collaboration_demo_output"),
        max_parallel=5,
        enable_collaboration=True,
        # redis_url="redis://localhost:6379/0",  # Optional Redis backend
        websocket_port=8767,
    )

    print("✅ CollaborationOrchestrator initialized")

    # Define collaborative software development workflow
    tasks = [
        # Phase 1: Requirements Analysis (can run independently)
        orchestrator.create_collaborative_task(
            task_id="requirements_analysis",
            task_type="business-analyst",
            prompt="""Analyze requirements for a real-time chat application.

            Requirements:
            1. Support 100+ concurrent users
            2. Real-time message delivery
            3. User authentication and presence
            4. Message persistence and history
            5. Mobile and web clients

            Deliverables:
            - Detailed requirements document
            - User stories and acceptance criteria
            - Technical constraints and assumptions
            """,
            required_capabilities=[
                "requirements_analysis",
                "business_analysis",
                "documentation",
            ],
            collaboration_type=CollaborationType.EXPERT_CONSULTATION,
            shared_workspace=True,
            priority="high",
            tags=["requirements", "analysis", "planning"],
        ),
        # Phase 2: Architecture Design (depends on requirements, enables peer review)
        orchestrator.create_collaborative_task(
            task_id="system_architecture",
            task_type="system-architect",
            prompt="""Design system architecture for the real-time chat application.

            Based on the requirements analysis, create:
            1. High-level system architecture diagram
            2. Technology stack recommendations
            3. Database schema design
            4. API design and endpoints
            5. Scalability and performance considerations
            6. Security architecture

            Enable peer review for architecture validation.
            """,
            dependencies=["requirements_analysis"],
            required_capabilities=[
                "system_architecture",
                "api_design",
                "scalability",
                "security",
            ],
            collaboration_type=CollaborationType.PEER_REVIEW,
            allow_peer_review=True,
            shared_workspace=True,
            priority="high",
            tags=["architecture", "design", "scalability"],
        ),
        # Phase 3A: Backend Implementation (parallel with frontend)
        orchestrator.create_collaborative_task(
            task_id="backend_implementation",
            task_type="backend-developer",
            prompt="""Implement backend services for the chat application.

            Implementation tasks:
            1. Set up WebSocket server for real-time messaging
            2. Implement user authentication and session management
            3. Create message persistence layer
            4. Build REST API for client operations
            5. Add presence tracking and user status
            6. Implement message queuing and delivery guarantees

            Allow task handoffs if specialized expertise needed.
            """,
            dependencies=["system_architecture"],
            required_capabilities=[
                "backend_development",
                "websockets",
                "databases",
                "api_development",
            ],
            collaboration_type=CollaborationType.PARALLEL_WORK,
            allow_handoffs=True,
            shared_workspace=True,
            max_collaborators=2,
            priority="normal",
            tags=["backend", "websockets", "api"],
        ),
        # Phase 3B: Frontend Implementation (parallel with backend)
        orchestrator.create_collaborative_task(
            task_id="frontend_implementation",
            task_type="frontend-developer",
            prompt="""Implement frontend clients for the chat application.

            Implementation tasks:
            1. Create React web client with real-time messaging
            2. Build mobile app with React Native
            3. Implement user interface for chat, contacts, settings
            4. Add real-time notifications and presence indicators
            5. Create responsive design for multiple screen sizes
            6. Implement offline support and message sync

            Collaborate with backend team for API integration.
            """,
            dependencies=["system_architecture"],
            required_capabilities=[
                "frontend_development",
                "react",
                "mobile_development",
                "ui_design",
            ],
            collaboration_type=CollaborationType.PARALLEL_WORK,
            shared_workspace=True,
            max_collaborators=2,
            priority="normal",
            tags=["frontend", "react", "mobile", "ui"],
        ),
        # Phase 4: Integration and Testing (depends on both implementations)
        orchestrator.create_collaborative_task(
            task_id="integration_testing",
            task_type="qa-engineer",
            prompt="""Integrate and test the complete chat application.

            Testing tasks:
            1. Integration testing between frontend and backend
            2. Load testing for concurrent user scenarios
            3. Real-time messaging performance testing
            4. Cross-platform compatibility testing
            5. Security testing and vulnerability assessment
            6. User acceptance testing with sample users

            Request handoff to specialists for complex issues.
            """,
            dependencies=["backend_implementation", "frontend_implementation"],
            required_capabilities=[
                "qa_testing",
                "integration_testing",
                "performance_testing",
                "security_testing",
            ],
            collaboration_type=CollaborationType.SEQUENTIAL_HANDOFF,
            allow_handoffs=True,
            enable_peer_review=True,
            shared_workspace=True,
            priority="normal",
            tags=["testing", "qa", "integration"],
        ),
    ]

    print(f"📋 Created {len(tasks)} collaborative tasks")
    print("🔄 Task dependencies:")
    for task in tasks:
        deps = ", ".join(task.dependencies) if task.dependencies else "None"
        print(f"  • {task.task_id} → depends on: {deps}")

    print(f"\n🤝 Collaboration features enabled:")
    for task in tasks:
        features = []
        if task.shared_workspace:
            features.append("shared workspace")
        if task.allow_handoffs:
            features.append("handoffs")
        if task.allow_peer_review:
            features.append("peer review")
        if task.collaboration_type:
            features.append(f"{task.collaboration_type.value}")
        print(f"  • {task.task_id}: {', '.join(features)}")

    print(
        f"\n⚡ Starting collaborative execution with up to {orchestrator.max_parallel} parallel agents..."
    )
    print()

    # Execute the collaborative workflow
    import time

    start_time = time.time()

    results = await orchestrator.execute_batch(tasks, enable_progress_monitoring=True)

    execution_time = time.time() - start_time

    # Analyze results
    successful = len([r for r in results if r.get("status") == "completed"])
    failed = len([r for r in results if r.get("status") == "failed"])

    print("\n" + "=" * 60)
    print("📊 COLLABORATION EXECUTION RESULTS")
    print("=" * 60)
    print(f"✅ Successful tasks: {successful}/{len(tasks)}")
    print(f"❌ Failed tasks: {failed}")
    print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
    print(f"🎯 Success rate: {successful/len(tasks):.1%}")

    # Get collaboration statistics
    collab_stats = orchestrator.get_collaboration_stats()
    print(f"\n📈 Collaboration Statistics:")
    print(f"  • Collaborative tasks executed: {collab_stats['collaborative_tasks']}")
    print(f"  • Messages sent: {collab_stats['messages_sent']}")
    print(f"  • Successful handoffs: {collab_stats['successful_handoffs']}")
    print(f"  • Shared workspaces created: {collab_stats['shared_workspaces_created']}")
    print(f"  • Active collaboration sessions: {collab_stats['active_collaborations']}")

    # Generate detailed collaboration report
    report = await orchestrator.generate_collaboration_report()
    report_file = Path("./collaboration_demo_output/collaboration_report.json")
    import json

    report_file.write_text(json.dumps(report, indent=2))

    print(f"\n📄 Detailed report saved to: {report_file}")
    print(f"🗂️  Task outputs saved to: ./collaboration_demo_output/tasks/")

    # Show individual task results
    print(f"\n📋 Individual Task Results:")
    for i, (task, result) in enumerate(zip(tasks, results)):
        status_emoji = "✅" if result.get("status") == "completed" else "❌"
        duration = result.get("execution_time", 0)

        print(f"  {status_emoji} {task.task_id}")
        print(f"     Status: {result.get('status', 'unknown')}")
        print(f"     Duration: {duration:.1f}s")

        if result.get("collaboration"):
            collab_info = result["collaboration"]
            if collab_info.get("workspace_used"):
                print(f"     Used shared workspace: Yes")
            if collab_info.get("handoffs_attempted"):
                print(f"     Handoffs attempted: {collab_info['handoffs_attempted']}")

        if result.get("error"):
            print(f"     Error: {result['error']}")
        print()

    return results


async def advanced_collaboration_demo():
    """Advanced demo showing dynamic handoffs and real-time coordination"""

    print("\n" + "=" * 60)
    print("🔄 ADVANCED COLLABORATION FEATURES DEMO")
    print("=" * 60)
    print("Demonstrating dynamic handoffs, peer review, and real-time coordination")
    print()

    orchestrator = CollaborationOrchestrator(
        output_dir=Path("./advanced_collaboration_output"),
        max_parallel=3,
        enable_collaboration=True,
    )

    # Create tasks that will trigger collaboration features
    tasks = [
        # Task designed to trigger handoffs
        orchestrator.create_collaborative_task(
            task_id="complex_algorithm",
            task_type="algorithm-specialist",
            prompt="""Implement a distributed consensus algorithm (Raft).

            This is a complex task that may require handoffs to specialists:
            1. Design the Raft consensus protocol implementation
            2. Handle leader election, log replication, safety
            3. Implement network communication layer
            4. Add persistence and crash recovery
            5. Create comprehensive test suite

            If you encounter complexity beyond your expertise, request handoff.
            """,
            required_capabilities=[
                "distributed_systems",
                "algorithms",
                "networking",
                "testing",
            ],
            collaboration_type=CollaborationType.SEQUENTIAL_HANDOFF,
            allow_handoffs=True,
            priority="high",
        ),
        # Task requiring peer review
        orchestrator.create_collaborative_task(
            task_id="security_review",
            task_type="security-specialist",
            prompt="""Conduct security review of authentication system.

            Security review tasks:
            1. Analyze authentication flow and session management
            2. Review password hashing and storage mechanisms
            3. Evaluate token generation and validation
            4. Check for common vulnerabilities (OWASP Top 10)
            5. Assess encryption and data protection measures

            Mandatory peer review required for security validation.
            """,
            required_capabilities=[
                "security_analysis",
                "cryptography",
                "authentication",
            ],
            collaboration_type=CollaborationType.PEER_REVIEW,
            allow_peer_review=True,
            enable_handoffs=False,  # Must complete with peer review
            priority="urgent",
        ),
        # Collaborative brainstorming task
        orchestrator.create_collaborative_task(
            task_id="architecture_brainstorm",
            task_type="architect-team",
            prompt="""Brainstorm optimal architecture for global chat platform.

            Brainstorming session goals:
            1. Generate multiple architectural approaches
            2. Evaluate pros/cons of each approach
            3. Consider scalability to 10M+ users
            4. Address global distribution challenges
            5. Optimize for low latency and high availability

            This requires collaborative input from multiple specialists.
            """,
            required_capabilities=[
                "architecture",
                "scalability",
                "distributed_systems",
                "brainstorming",
            ],
            collaboration_type=CollaborationType.BRAINSTORMING,
            shared_workspace=True,
            max_collaborators=4,
            priority="normal",
        ),
    ]

    print(f"🎯 Executing {len(tasks)} advanced collaborative tasks...")

    # Monitor collaboration in real-time
    async def monitor_collaboration():
        """Monitor collaboration progress"""
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            stats = orchestrator.get_collaboration_stats()
            print(
                f"⏱️  [Monitor] Active collaborations: {stats.get('active_collaborations', 0)}, "
                f"Messages: {stats.get('messages_sent', 0)}, "
                f"Handoffs: {stats.get('successful_handoffs', 0)}"
            )

    # Start monitoring
    monitor_task = asyncio.create_task(monitor_collaboration())

    try:
        # Execute advanced collaboration
        results = await orchestrator.execute_batch(tasks)

        # Stop monitoring
        monitor_task.cancel()

        print("\n📊 Advanced Collaboration Results:")
        for task, result in zip(tasks, results):
            print(f"  • {task.task_id}: {result.get('status', 'unknown')}")
            if task.collaboration_type:
                print(f"    Collaboration type: {task.collaboration_type.value}")

    except KeyboardInterrupt:
        monitor_task.cancel()
        print("\n👋 Demo cancelled by user")

    return results


async def main():
    """Main demo runner"""
    print("Real-Time Multi-Agent Collaboration System Demo")
    print("Choose demo to run:")
    print("1. Basic Collaboration Demo (software development workflow)")
    print("2. Advanced Collaboration Demo (handoffs, peer review, brainstorming)")
    print("3. Both demos")

    try:
        choice = input("\nEnter choice [1/2/3]: ").strip()

        if choice == "1":
            await basic_collaboration_demo()
        elif choice == "2":
            await advanced_collaboration_demo()
        elif choice == "3":
            await basic_collaboration_demo()
            await advanced_collaboration_demo()
        else:
            print("Invalid choice. Running basic demo...")
            await basic_collaboration_demo()

    except KeyboardInterrupt:
        print("\n👋 Demo cancelled")
    except EOFError:
        print("\n🤖 Running basic collaboration demo by default...")
        await basic_collaboration_demo()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run the collaboration demo
    asyncio.run(main())
