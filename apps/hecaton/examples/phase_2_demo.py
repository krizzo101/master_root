#!/usr/bin/env python3
"""
HECATON Phase 2 Integration Demo
Demonstrates all Phase 2 components working together:
- MessageBroker for inter-agent communication
- AgentRegistry for agent management
- PerformanceMonitor for tracking execution metrics
- Specialized agents (Code, Research, Test)
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hecaton.core.orchestrator import HecatonConfig, HecatonOrchestrator
from src.hecaton.messaging.message_broker import Message


async def demo_phase_2_features():
    """Demonstrate all Phase 2 features integrated together."""

    print("=" * 60)
    print("HECATON PHASE 2 INTEGRATION DEMO")
    print("=" * 60)
    print()

    # Initialize HECATON with Phase 2 configuration
    config = HecatonConfig(
        max_parallel_agents=15,
        token_pool_size=15,
        enable_monitoring=True,
        enable_checkpointing=True,
    )

    orchestrator = HecatonOrchestrator(config)

    print("✓ HECATON Orchestrator initialized with Phase 2 components")
    print()

    # Start message broker
    await orchestrator.start_message_broker()
    print("✓ Message broker started")
    print()

    # Register specialized agents
    print("Registering specialized agents...")
    agents = orchestrator.register_specialized_agents()
    print(f"✓ Registered agents: {json.dumps(agents, indent=2)}")
    print()

    # Demo 1: Inter-agent communication via message broker
    print("-" * 40)
    print("Demo 1: Inter-Agent Communication")
    print("-" * 40)

    # Subscribe code agents to 'code_tasks' topic
    async def handle_code_task(message: Message):
        print(f"  Code agent received: {message.payload}")

    await orchestrator.message_broker.subscribe("code_tasks", handle_code_task)

    # Broadcast a message
    await orchestrator.broadcast_message(
        "code_tasks",
        {"task": "refactor", "target": "authentication module"},
        sender="orchestrator",
    )

    # Allow time for message processing
    await asyncio.sleep(0.5)
    print("✓ Message broadcast and received")
    print()

    # Demo 2: Execute tasks with different agent types
    print("-" * 40)
    print("Demo 2: Specialized Agent Execution")
    print("-" * 40)

    tasks = [
        {
            "id": "research_1",
            "type": "research",
            "task_type": "code_analysis",
            "query": "Analyze HECATON architecture",
            "depth": 3,
        },
        {
            "id": "code_1",
            "type": "code",
            "operation": "refactor",
            "target": "src/core/orchestrator.py",
            "description": "Optimize performance",
        },
        {
            "id": "test_1",
            "type": "test",
            "test_type": "unit_test",
            "target": "core_modules",
            "coverage_threshold": 85,
        },
    ]

    print("Executing specialized tasks with monitoring...")
    results = await orchestrator.execute_with_monitoring(tasks)

    for task_id, result in results.items():
        if task_id != "_metrics":
            status = result.get("status", "unknown")
            agent_id = result.get("agent_id", "N/A")
            print(f"  Task {task_id}: {status} (Agent: {agent_id[:8]}...)")
    print()

    # Demo 3: Performance monitoring
    print("-" * 40)
    print("Demo 3: Performance Monitoring")
    print("-" * 40)

    if "_metrics" in results:
        metrics = results["_metrics"]
        print(f"  Total tasks: {metrics['total_tasks']}")
        print(f"  Success rate: {metrics['success_rate']:.1%}")
        print(f"  Avg execution time: {metrics['avg_execution_time']:.3f}s")
        print(f"  Peak memory: {metrics['peak_memory'] / 1024 / 1024:.1f} MB")
        print(f"  Total token usage: {metrics['total_token_usage']}")
    print()

    # Demo 4: Agent registry operations
    print("-" * 40)
    print("Demo 4: Agent Registry Management")
    print("-" * 40)

    agent_status = orchestrator.get_agent_status()
    print(f"  Registered agent types:")
    for agent_type, count in agent_status["agent_types"].items():
        print(f"    - {agent_type}: {count} agents")

    print(f"  Total agents: {len(agent_status['registered_agents'])}")
    print()

    # Demo 5: Direct messaging between agents
    print("-" * 40)
    print("Demo 5: Direct Agent Messaging")
    print("-" * 40)

    if agents["code"]:
        agent_id = agents["code"][0]
        await orchestrator.message_broker.send_direct(
            agent_id,
            Message(
                sender="orchestrator",
                payload={"priority": "high", "task": "emergency fix"},
            ),
        )
        print(f"  Sent direct message to agent {agent_id[:8]}...")

        # Agent would receive message via:
        # message = await orchestrator.message_broker.receive_direct(agent_id, timeout=1.0)
        print("  ✓ Direct messaging demonstrated")
    print()

    # Demo 6: Export performance metrics
    print("-" * 40)
    print("Demo 6: Metrics Export")
    print("-" * 40)

    metrics_json = orchestrator.export_metrics()
    metrics_data = json.loads(metrics_json)
    print(f"  Metrics exported with {len(metrics_data.get('completed_tasks', {}))} completed tasks")
    print(f"  Monitor uptime: {metrics_data['statistics']['monitor_uptime']:.1f}s")
    print()

    # Demo 7: Topic management
    print("-" * 40)
    print("Demo 7: Message Broker Topics")
    print("-" * 40)

    topics = await orchestrator.message_broker.get_topics()
    print(f"  Active topics: {list(topics)}")

    direct_agents = await orchestrator.message_broker.get_agents()
    print(f"  Agents with direct queues: {len(direct_agents)}")
    print()

    # Clean up
    await orchestrator.stop_message_broker()
    print("✓ Message broker stopped")
    print()

    print("=" * 60)
    print("PHASE 2 INTEGRATION DEMO COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print("✓ MessageBroker enables pub/sub and direct messaging")
    print("✓ AgentRegistry manages specialized agent lifecycle")
    print("✓ PerformanceMonitor tracks execution metrics")
    print("✓ Specialized agents execute domain-specific tasks")
    print("✓ All components integrated into HecatonOrchestrator")
    print()
    print("HECATON is ready for Phase 3: Full parallel execution!")


async def demo_agent_collaboration():
    """Demonstrate complex agent collaboration scenario."""

    print("\n" + "=" * 60)
    print("BONUS: Agent Collaboration Demo")
    print("=" * 60)
    print()

    config = HecatonConfig(enable_monitoring=True)
    orchestrator = HecatonOrchestrator(config)

    await orchestrator.start_message_broker()
    agents = orchestrator.register_specialized_agents()

    print("Scenario: Collaborative code improvement workflow")
    print("-" * 40)

    # Step 1: Research agent analyzes codebase
    research_task = {
        "id": "research_codebase",
        "type": "research",
        "task_type": "code_analysis",
        "query": "Identify optimization opportunities",
        "depth": 3,
    }

    print("1. Research agent analyzing codebase...")
    results = await orchestrator.execute_with_monitoring([research_task])
    research_result = results.get("research_codebase", {})
    findings = {}  # Initialize findings with empty dict

    if research_result.get("status") == "success":
        findings = research_result.get("findings", {})
        print(f"   Found {len(findings.get('recommendations', []))} optimization opportunities")

    # Step 2: Code agent implements improvements
    code_task = {
        "id": "implement_improvements",
        "type": "code",
        "operation": "optimize",
        "target": "identified_modules",
        "recommendations": findings.get("recommendations", []),
    }

    print("2. Code agent implementing improvements...")
    results = await orchestrator.execute_with_monitoring([code_task])
    code_result = results.get("implement_improvements", {})

    if code_result.get("status") == "success":
        changes = code_result.get("changes_made", {})
        print(f"   Implemented {changes.get('files_modified', 0)} improvements")

    # Step 3: Test agent validates changes
    test_task = {
        "id": "validate_changes",
        "type": "test",
        "test_type": "integration_test",
        "target": "modified_modules",
        "coverage_threshold": 90,
    }

    print("3. Test agent validating changes...")
    results = await orchestrator.execute_with_monitoring([test_task])
    test_result = results.get("validate_changes", {})

    if test_result.get("status") == "success":
        test_data = test_result.get("test_results", {})
        print(f"   Tests passed: {test_data.get('passed', 0)}/{test_data.get('total_tests', 0)}")
        print(f"   Coverage: {test_data.get('coverage_percentage', 0)}%")

    await orchestrator.stop_message_broker()

    print()
    print("✓ Collaborative workflow completed successfully!")
    print()


if __name__ == "__main__":
    # Run main demo
    asyncio.run(demo_phase_2_features())

    # Run collaboration demo
    asyncio.run(demo_agent_collaboration())
