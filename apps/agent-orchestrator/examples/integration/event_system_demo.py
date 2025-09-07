#!/usr/bin/env python3
"""
Event-Driven Coordination System Demo

Demonstrates the key capabilities of the event-driven coordination system
including task handoffs, notifications, and automated processors.
"""

import asyncio
import logging
import time
from typing import Any, Dict

# Import the event system components
from src.events import (
    CoordinationEvent,
    DiscoveryEvent,
    EventBus,
    EventHistory,
    EventQuery,
    EventType,
    NotificationEngine,
    NotificationMethod,
    NotificationRule,
    Priority,
    ProgressEvent,
    create_default_processors,
    get_global_event_bus,
)
from src.events.coordination_events import Agent, AgentCapability, CoordinationManager
from src.events.event_types import (
    create_help_request_event,
    create_insight_event,
    create_progress_event,
    create_task_handoff_event,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def demo_basic_event_publishing():
    """Demonstrate basic event publishing and subscription"""
    print("\n=== Demo 1: Basic Event Publishing ===")

    event_bus = get_global_event_bus()

    # Create a simple event handler
    received_events = []

    def event_handler(event):
        received_events.append(event)
        print(f"Received event: {event.event_type.value} from {event.source_agent_id}")

    # Subscribe to coordination events
    subscription_id = event_bus.subscribe(
        event_handler, event_types=[EventType.TASK_HANDOFF, EventType.HELP_REQUEST]
    )

    # Publish some events
    handoff_event = create_task_handoff_event(
        source_agent_id="agent_1",
        target_agent_id="agent_2",
        task_id="task_123",
        task_data={"description": "Analyze user behavior patterns"},
        context="Need specialized data analysis skills",
    )

    help_event = create_help_request_event(
        source_agent_id="agent_3",
        problem_description="Stuck on API integration issue",
        required_skills=["api_integration", "debugging"],
        urgency=Priority.HIGH,
    )

    await event_bus.publish(handoff_event)
    await event_bus.publish(help_event)

    # Wait for event processing
    await asyncio.sleep(0.1)

    print(f"Published 2 events, received {len(received_events)} events")

    # Clean up
    event_bus.unsubscribe(subscription_id)


async def demo_coordination_manager():
    """Demonstrate the coordination manager for agent coordination"""
    print("\n=== Demo 2: Agent Coordination Manager ===")

    event_bus = get_global_event_bus()
    coordination_manager = CoordinationManager(event_bus)

    # Register some agents with different capabilities
    agents_data = [
        (
            "data_analyst_1",
            "Data Analysis Specialist",
            [
                AgentCapability("data_analysis", 0.9),
                AgentCapability("visualization", 0.8),
                AgentCapability("statistics", 0.85),
            ],
        ),
        (
            "api_expert_1",
            "API Integration Expert",
            [
                AgentCapability("api_integration", 0.95),
                AgentCapability("debugging", 0.8),
                AgentCapability("testing", 0.7),
            ],
        ),
        (
            "general_agent_1",
            "General Purpose Agent",
            [
                AgentCapability("research", 0.7),
                AgentCapability("writing", 0.8),
                AgentCapability("analysis", 0.6),
            ],
        ),
    ]

    # Register agents
    for agent_id, name, capabilities in agents_data:
        await coordination_manager.register_agent(agent_id, name, capabilities)

    # Request a task handoff
    print("\nRequesting task handoff for data analysis task...")
    target_agent = await coordination_manager.request_task_handoff(
        source_agent_id="general_agent_1",
        task_id="complex_data_analysis",
        task_data={
            "dataset": "user_behavior_2023.csv",
            "analysis_type": "clustering",
            "deadline": "2023-12-15",
        },
        required_skills=["data_analysis", "statistics"],
    )

    if target_agent:
        print(f"Task successfully assigned to: {target_agent}")
    else:
        print("No suitable agent found for task handoff")

    # Request help
    print("\nRequesting help for API integration issue...")
    helper_agents = await coordination_manager.request_help(
        source_agent_id="general_agent_1",
        problem_description="Need help with complex REST API authentication",
        required_skills=["api_integration"],
        urgency=Priority.HIGH,
    )

    print(f"Help request sent to {len(helper_agents)} agents: {helper_agents}")

    # Get coordination stats
    stats = await coordination_manager.get_coordination_stats()
    print(f"\nCoordination Stats:")
    print(f"- Total agents: {stats['total_agents']}")
    print(f"- Available agents: {stats['available_agents']}")
    print(f"- Active handoffs: {stats['active_handoffs']}")


async def demo_notification_system():
    """Demonstrate the intelligent notification system"""
    print("\n=== Demo 3: Notification System ===")

    event_bus = get_global_event_bus()
    notification_engine = NotificationEngine(event_bus)

    # Custom notification handler
    notifications_received = []

    async def custom_notification_handler(
        agent_id: str, event, notification_data: Dict[str, Any]
    ):
        message = f"NOTIFICATION for {agent_id}: {notification_data['event_type']} from {notification_data['source_agent']}"
        notifications_received.append(message)
        print(message)

    # Register notification handler
    notification_engine.register_handler(
        NotificationMethod.DIRECT_MESSAGE, custom_notification_handler
    )

    # Create notification rules for agents
    rule1 = NotificationRule(
        rule_id="urgent_tasks",
        agent_id="project_manager_1",
        event_types=[EventType.TASK_HANDOFF, EventType.HELP_REQUEST],
        priority_threshold=Priority.HIGH,
        keywords=["urgent", "critical", "deadline"],
    )

    rule2 = NotificationRule(
        rule_id="discovery_alerts",
        agent_id="research_lead_1",
        event_types=[EventType.INSIGHT_FOUND, EventType.PROBLEM_SOLVED],
        priority_threshold=Priority.NORMAL,
    )

    # Add rules
    notification_engine.add_notification_rule(rule1)
    notification_engine.add_notification_rule(rule2)

    # Start notification engine
    await notification_engine.start()

    # Publish events that should trigger notifications
    urgent_help = create_help_request_event(
        source_agent_id="developer_1",
        problem_description="Critical API failure - urgent assistance needed",
        urgency=Priority.HIGH,
    )

    insight = create_insight_event(
        source_agent_id="researcher_1",
        insight_content="Discovered new optimization algorithm that improves performance by 40%",
        tags=["optimization", "algorithm", "performance"],
        relevance=0.9,
    )

    await event_bus.publish(urgent_help)
    await event_bus.publish(insight)

    # Wait for notifications to be processed
    await asyncio.sleep(0.5)

    print(f"Sent notifications: {len(notifications_received)}")

    # Stop notification engine
    await notification_engine.stop()


async def demo_event_history():
    """Demonstrate event history and analytics"""
    print("\n=== Demo 4: Event History & Analytics ===")

    event_bus = get_global_event_bus()
    event_history = EventHistory("demo_events.db", event_bus)

    # Generate some historical events
    agents = ["analyst_1", "developer_1", "tester_1", "manager_1"]

    print("Generating sample events...")
    for i in range(50):
        if i % 4 == 0:
            event = create_task_handoff_event(
                source_agent_id=agents[i % len(agents)],
                target_agent_id=agents[(i + 1) % len(agents)],
                task_id=f"task_{i}",
                task_data={"complexity": "medium", "priority": "normal"},
            )
        elif i % 4 == 1:
            event = create_help_request_event(
                source_agent_id=agents[i % len(agents)],
                problem_description=f"Need assistance with issue #{i}",
                required_skills=["debugging", "testing"],
            )
        elif i % 4 == 2:
            event = create_insight_event(
                source_agent_id=agents[i % len(agents)],
                insight_content=f"Discovered pattern #{i} in the data",
                tags=["pattern", "analysis"],
            )
        else:
            event = create_progress_event(
                source_agent_id=agents[i % len(agents)],
                task_id=f"task_{i // 4}",
                progress=min(100.0, (i % 10) * 10),
                message=f"Progress update #{i}",
            )

        await event_bus.publish(event)

    # Wait for events to be stored
    await asyncio.sleep(0.5)

    # Query events
    query = EventQuery(
        event_types=[EventType.TASK_HANDOFF, EventType.HELP_REQUEST], limit=10
    )

    recent_events = await event_history.query_events(query)
    print(f"Retrieved {len(recent_events)} recent coordination events")

    # Get agent activity
    activity = await event_history.get_agent_activity("analyst_1", days=1)
    print(f"Agent activity data points: {len(activity)}")

    # Analyze collaboration patterns
    patterns = await event_history.get_collaboration_patterns(min_frequency=3)
    print(f"Identified {len(patterns)} collaboration patterns")
    for pattern in patterns[:3]:  # Show first 3
        print(f"- {pattern.pattern_type}: {pattern.description}")

    # Get statistics
    stats = await event_history.get_statistics()
    print(f"\nEvent History Stats:")
    print(f"- Total events: {stats.get('total_events', 0)}")
    print(f"- Active agents (24h): {stats.get('active_agents_24h', 0)}")
    print(f"- Database size: {stats.get('database_size_bytes', 0)} bytes")


async def demo_event_processors():
    """Demonstrate automated event processors"""
    print("\n=== Demo 5: Event Processors ===")

    event_bus = get_global_event_bus()
    processor_manager = create_default_processors(event_bus)

    # Start all processors
    await processor_manager.start_all_processors()

    # Simulate some events that will trigger processors
    print("Triggering events that will be processed automatically...")

    # Task handoff (will be processed by TaskHandoffProcessor)
    handoff = create_task_handoff_event(
        source_agent_id="overloaded_agent",
        target_agent_id="available_agent",
        task_id="redistribute_task_1",
        task_data={"workload": "high", "priority": "normal"},
    )

    # Progress updates
    progress_events = [
        create_progress_event("agent_1", "long_task", 25, "Started data processing"),
        create_progress_event("agent_1", "long_task", 50, "Halfway through analysis"),
        create_progress_event(
            "agent_1", "long_task", 100, "Task completed successfully"
        ),
    ]

    # Simulate an agent error (will trigger FailureRecoveryProcessor)
    error_event = CoordinationEvent(
        event_type=EventType.AGENT_ERROR,
        source_agent_id="problematic_agent",
        priority=Priority.HIGH,
        metadata={"error_type": "connection_timeout", "retry_count": 1},
    )

    # Publish events
    await event_bus.publish(handoff)

    for progress_event in progress_events:
        await event_bus.publish(progress_event)
        await asyncio.sleep(0.1)  # Small delay between progress updates

    await event_bus.publish(error_event)

    # Wait for processing
    await asyncio.sleep(1.0)

    # Get processor metrics
    metrics = processor_manager.get_processor_metrics()
    print("\nProcessor Metrics:")
    for processor_id, processor_metrics in metrics.items():
        print(f"- {processor_id}:")
        print(f"  - Processed: {processor_metrics['processed_count']}")
        print(f"  - Errors: {processor_metrics['error_count']}")
        print(f"  - Avg time: {processor_metrics['avg_processing_time']:.3f}s")
        print(f"  - Status: {processor_metrics['status']}")

    # Stop processors
    await processor_manager.stop_all_processors()


async def demo_integration_with_orchestrator():
    """Show how the event system integrates with the orchestrator"""
    print("\n=== Demo 6: Integration Concept ===")

    print(
        """
    Integration with GenericOrchestrator:

    1. Extended orchestrator would register agents with CoordinationManager
    2. Task execution would publish progress events automatically
    3. Failed tasks would trigger FailureRecoveryProcessor
    4. Agents could request help or handoff tasks during execution
    5. Real-time monitoring would show collaboration in dashboard

    Key integration points:
    - Orchestrator.run() -> publishes AGENT_JOINED events
    - Task execution -> publishes PROGRESS_UPDATE events
    - Task completion -> publishes TASK_COMPLETED events
    - Agent errors -> publishes AGENT_ERROR events
    - Dynamic coordination -> enables task handoffs mid-execution
    """
    )

    # Simulate what an integrated orchestrator would do
    event_bus = get_global_event_bus()

    # Simulate orchestrator startup
    startup_events = [
        CoordinationEvent(
            event_type=EventType.AGENT_JOINED,
            source_agent_id=f"agent_{i}",
            metadata={"capabilities": ["analysis", "coding", "testing"]},
        )
        for i in range(3)
    ]

    for event in startup_events:
        await event_bus.publish(event)

    print("Simulated orchestrator startup with 3 agents")

    # Simulate collaborative task execution
    collaborative_events = [
        create_progress_event(
            "agent_0", "collaborative_task", 0, "Starting collaboration"
        ),
        create_task_handoff_event(
            "agent_0",
            "agent_1",
            "collaborative_task",
            {"subtask": "data_processing", "status": "handed_off"},
        ),
        create_progress_event("agent_1", "collaborative_task", 50, "Processing data"),
        create_task_handoff_event(
            "agent_1",
            "agent_2",
            "collaborative_task",
            {"subtask": "analysis", "data_processed": True},
        ),
        create_progress_event(
            "agent_2", "collaborative_task", 100, "Analysis complete"
        ),
    ]

    for event in collaborative_events:
        await event_bus.publish(event)
        await asyncio.sleep(0.2)

    print("Simulated collaborative task execution with handoffs")


async def main():
    """Run all demos"""
    print("Event-Driven Coordination System Demo")
    print("=" * 50)

    try:
        await demo_basic_event_publishing()
        await demo_coordination_manager()
        await demo_notification_system()
        await demo_event_history()
        await demo_event_processors()
        await demo_integration_with_orchestrator()

        # Final stats
        event_bus = get_global_event_bus()
        metrics = await event_bus.get_metrics()

        print(f"\n=== Final Event Bus Statistics ===")
        print(f"Total events published: {metrics['events_published']}")
        print(f"Total events delivered: {metrics['events_delivered']}")
        print(f"Average delivery time: {metrics['avg_delivery_time_ms']:.2f}ms")
        print(f"Active subscriptions: {metrics['active_subscriptions']}")

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
