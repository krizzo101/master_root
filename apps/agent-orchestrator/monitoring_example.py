#!/usr/bin/env python3
"""
Real-Time Agent Status API - Usage Example
Demonstrates how to use the monitoring system in practice
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src import AgentLogParser, AgentStatusMonitor, UUIDMonitoringSystem


async def basic_monitoring_example():
    """Basic usage of the monitoring system"""
    print("=== Basic Agent Monitoring Example ===")

    # Initialize the monitor
    monitor = AgentStatusMonitor()

    # Example UUID - in practice this would come from your orchestrator
    example_uuid = "team-phase1-001-monitor-1725408000"

    print(f"Monitoring agent: {example_uuid}")

    # Get current status
    status = await monitor.get_agent_status(example_uuid)

    print(f"Status: {status.status}")
    print(f"Progress: {status.progress.progress_percentage:.1f}%")
    print(f"Current Task: {status.progress.current_task}")
    print(f"Errors: {status.error_count}")
    print(f"Context Usage: {status.context_usage:.1f}%")
    print(
        f"Runtime: {status.runtime_duration:.0f}s"
        if status.runtime_duration
        else "Runtime: unknown"
    )

    if status.deliverables_completed:
        print(f"Deliverables: {', '.join(status.deliverables_completed)}")

    # Get all agents
    print("\nAll active agents:")
    all_agents = await monitor.get_all_agent_statuses()
    for uuid, agent_status in all_agents.items():
        print(
            f"  {uuid[:8]}... : {agent_status.status} ({agent_status.progress.progress_percentage:.0f}%)"
        )


async def team_monitoring_example():
    """Example of monitoring agents by team"""
    print("\n=== Team Monitoring Example ===")

    # Use the comprehensive UUID monitoring system
    uuid_monitor = UUIDMonitoringSystem(update_interval=10)

    try:
        # Start monitoring
        await uuid_monitor.start_monitoring()

        # Let it run for a bit to discover agents
        await asyncio.sleep(2)

        # Get team-specific agents
        team_agents = await uuid_monitor.get_team_agents("phase1")
        print(f"Phase1 team has {len(team_agents)} agents:")

        for uuid, status in team_agents.items():
            print(f"  {uuid[:12]}: {status.status} - {status.progress.current_task}")

        # Get monitoring summary
        summary = await uuid_monitor.get_monitoring_summary()
        print(f"\nMonitoring Summary:")
        print(f"  Total Active: {summary['total_active_agents']}")
        print(f"  By Status: {dict(summary['agents_by_status'])}")
        print(
            f"  By Team: {[f'{k}:{len(v)}' for k,v in summary['agents_by_team'].items()]}"
        )
        print(
            f"  Total Errors: {summary['performance_metrics'].get('total_errors', 0)}"
        )

        # Check for stuck agents
        stuck = await uuid_monitor.detect_stuck_agents(threshold_minutes=5)
        if stuck:
            print(f"  Stuck agents: {[uuid[:8] for uuid in stuck]}")
        else:
            print("  No stuck agents detected")

    finally:
        await uuid_monitor.stop_monitoring()


async def real_time_monitoring_example():
    """Example of real-time log monitoring"""
    print("\n=== Real-Time Log Monitoring Example ===")

    monitor = AgentStatusMonitor()
    example_uuid = "team-phase1-001-monitor-1725408000"

    print(f"Starting real-time monitoring for: {example_uuid}")
    print("(This will monitor for new log entries - press Ctrl+C to stop)")

    try:
        # Monitor logs in real-time
        async for log_entry in monitor.monitor_agent_logs(example_uuid):
            print(
                f"[{log_entry.timestamp}] {log_entry.role}: {log_entry.content[:100]}..."
            )

            # Break after a few entries for demo
            if "completed" in log_entry.content.lower():
                print("Agent completed task - stopping monitoring")
                break

    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    except Exception as e:
        print(f"Monitoring error: {e}")


async def log_analysis_example():
    """Example of detailed log analysis"""
    print("\n=== Detailed Log Analysis Example ===")

    parser = AgentLogParser()
    example_uuid = "team-phase1-001-monitor-1725408000"

    print(f"Analyzing logs for: {example_uuid}")

    # Parse progress details
    progress = await parser.parse_agent_progress(example_uuid)
    print(f"Progress Analysis:")
    print(f"  Current: {progress.current_task}")
    print(f"  Percentage: {progress.progress_percentage:.1f}%")
    print(f"  Completed: {len(progress.completed_tasks)} tasks")
    if progress.completed_tasks:
        for i, task in enumerate(progress.completed_tasks[:3]):
            print(f"    {i+1}. {task}")

    # Analyze errors
    errors = await parser.detect_agent_errors(example_uuid)
    print(f"\nError Analysis:")
    print(f"  Total errors: {len(errors)}")

    error_types = {}
    for error in errors:
        error_types[error.error_type] = error_types.get(error.error_type, 0) + 1

    for error_type, count in error_types.items():
        print(f"    {error_type}: {count}")

    # Recent errors
    if errors:
        print("  Recent errors:")
        for error in errors[-3:]:  # Last 3 errors
            print(
                f"    [{error.timestamp[:19]}] {error.error_type}: {error.error_message[:80]}..."
            )

    # Performance analysis
    performance = await parser.analyze_agent_performance(example_uuid)
    print(f"\nPerformance Analysis:")
    print(f"  Messages: {performance['total_messages']}")
    print(f"  Messages/min: {performance['messages_per_minute']:.1f}")
    print(f"  Tool usage: {performance['tool_usage_frequency']}")
    print(f"  Error rate: {performance['error_rate']:.1f}%")
    print(f"  Efficiency score: {performance['efficiency_score']:.1f}/100")

    # Get deliverables
    deliverables = await parser.get_agent_deliverables(example_uuid)
    print(f"\nDeliverables ({len(deliverables)}):")
    for deliverable in deliverables:
        print(f"  - {deliverable}")


async def management_dashboard_example():
    """Example of a management dashboard view"""
    print("\n=== Management Dashboard Example ===")

    uuid_monitor = UUIDMonitoringSystem(update_interval=5)

    try:
        await uuid_monitor.start_monitoring()
        await asyncio.sleep(2)  # Let it discover agents

        # Simulate a management dashboard
        for update_cycle in range(3):
            print(f"\n--- Dashboard Update {update_cycle + 1} ---")

            # Get comprehensive status
            summary = await uuid_monitor.get_monitoring_summary()

            print(f"🚀 Active Agents: {summary['total_active_agents']}")

            status_counts = summary["agents_by_status"]
            print(
                f"📊 Status: ✅{status_counts.get('completed', 0)} "
                f"🔄{status_counts.get('running', 0)} "
                f"❌{status_counts.get('failed', 0)} "
                f"⏸️{status_counts.get('stuck', 0)}"
            )

            perf = summary.get("performance_metrics", {})
            avg_progress = perf.get("average_progress", 0)
            total_errors = perf.get("total_errors", 0)

            print(f"📈 Avg Progress: {avg_progress:.1f}% | Errors: {total_errors}")

            # Show team breakdown
            teams = summary["agents_by_team"]
            print(
                f"👥 Teams: {', '.join([f'{team}({len(agents)})' for team, agents in teams.items()])}"
            )

            # Check for issues
            stuck_agents = await uuid_monitor.detect_stuck_agents(threshold_minutes=2)
            if stuck_agents:
                print(f"⚠️ Stuck Agents: {len(stuck_agents)}")

            print(f"🔍 Last Scan: {summary['monitoring_stats']['scan_duration']:.2f}s")

            if update_cycle < 2:  # Don't wait after last cycle
                await asyncio.sleep(10)

    finally:
        await uuid_monitor.stop_monitoring()


async def main():
    """Run all examples"""
    print("Real-Time Agent Status API - Usage Examples")
    print("=" * 60)

    examples = [
        basic_monitoring_example,
        team_monitoring_example,
        log_analysis_example,
        management_dashboard_example,
        # real_time_monitoring_example,  # Skip interactive example for demo
    ]

    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # Brief pause between examples
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("✅ Examples completed successfully!")
    print("\nTo integrate with your orchestrator:")
    print("  1. Import: from src import AgentStatusMonitor")
    print("  2. Initialize: monitor = AgentStatusMonitor()")
    print("  3. Query: status = await monitor.get_agent_status(uuid)")
    print("  4. Monitor: async for log in monitor.monitor_agent_logs(uuid)")


if __name__ == "__main__":
    asyncio.run(main())
