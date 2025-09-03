#!/usr/bin/env python3
"""
Example usage of the comprehensive data collection service.
Demonstrates how to collect and display aggregated metrics from all sources.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add collectors directory to path
sys.path.insert(0, str(Path(__file__).parent / "collectors"))

from data_collector import DataCollector, collect_comprehensive_data


async def demonstrate_data_collection():
    """Demonstrate comprehensive data collection capabilities."""
    print("=== Claude Monitor Data Collection Demo ===\n")

    # Initialize collector
    collector = DataCollector()

    try:
        print("🔄 Collecting metrics from all sources...")
        start_time = time.time()

        # Collect comprehensive data
        data = await collector.collect_all_metrics(hours_back=24)

        collection_time = time.time() - start_time
        print(f"✅ Collection completed in {collection_time:.2f} seconds\n")

        # Display summary
        print("📊 SYSTEM OVERVIEW")
        print("=" * 50)
        summary = data["summary"]
        print(f"💰 Total Cost (24h):        ${summary['total_cost']:.4f}")
        print(f"🎯 Total Tokens (24h):      {summary['total_tokens']:,}")
        print(f"🔥 Active Sessions:         {summary['active_sessions']}")
        print(f"📈 System CPU Usage:        {summary['system_cpu_percent']:.1f}%")
        print(f"🧠 System Memory Usage:     {summary['system_memory_percent']:.1f}%")
        print(f"⚡ Claude Processes:        {summary['claude_processes']}")
        print(f"🐳 Claude Containers:       {summary['claude_containers']}")
        print(f"❌ Error Rate:              {summary['error_rate']:.2f}%")
        print()

        # Token usage breakdown
        print("🎯 TOKEN USAGE BY MODEL")
        print("=" * 50)
        token_data = data["token_usage"]
        if token_data["cost_by_model"]:
            for model, cost in token_data["cost_by_model"].items():
                tokens = token_data["tokens_by_model"].get(model, {})
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                total_tokens = tokens.get("total", 0)
                print(
                    f"{model:20s} ${cost:8.4f} ({total_tokens:8,} tokens) [{input_tokens:,}in/{output_tokens:,}out]"
                )
        else:
            print("No token usage data found")
        print()

        # System resources
        print("🖥️  SYSTEM RESOURCES")
        print("=" * 50)
        system_data = data["system_resources"]
        print(f"CPU Usage:           {system_data['cpu_percent']:.1f}%")
        print(
            f"Memory Usage:        {system_data['memory_percent']:.1f}% ({system_data['memory_used']:,} / {system_data['memory_total']:,} bytes)"
        )
        print(
            f"Disk Usage:          {system_data['disk_percent']:.1f}% ({system_data['disk_used']:,} / {system_data['disk_total']:,} bytes)"
        )
        print(
            f"Load Average:        {', '.join(f'{x:.2f}' for x in system_data['load_average'])}"
        )
        print()

        # Process monitoring
        print("⚡ CLAUDE PROCESSES")
        print("=" * 50)
        process_data = data["process_monitoring"]
        if process_data["claude_processes"]:
            for proc in process_data["claude_processes"]:
                print(
                    f"PID {proc['pid']:6s} {proc['name']:15s} CPU: {proc['cpu_percent']:5.1f}% MEM: {proc['memory_rss']/1024/1024:6.1f}MB"
                )
                if proc["cmdline"]:
                    print(f"         CMD: {proc['cmdline'][:80]}...")
        else:
            print("No Claude processes detected")
        print()

        # Docker containers
        print("🐳 DOCKER CONTAINERS")
        print("=" * 50)
        docker_data = data["docker_containers"]
        if docker_data["containers"]:
            print(f"Total Containers: {docker_data['total_containers']}")
            print(f"Running: {docker_data['running_containers']}")
            print(f"Claude-related: {docker_data['claude_containers']}")
            print()

            for container in docker_data["containers"]:
                if container.get("is_claude_related"):
                    cpu = container.get("cpu_percent", 0)
                    mem_percent = container.get("memory_percent", 0)
                    print(
                        f"🔥 {container['name']:20s} [{container['status']:8s}] CPU: {cpu:5.1f}% MEM: {mem_percent:5.1f}%"
                    )
        else:
            print("No Docker containers found")
        print()

        # Log analysis
        print("📋 LOG ANALYSIS")
        print("=" * 50)
        log_data = data["log_analysis"]
        print(f"Files Processed:     {log_data['log_files_processed']}")
        print(f"Errors Found:        {log_data['error_count']}")
        print(f"Warnings Found:      {log_data['warning_count']}")
        print(f"Error Rate:          {log_data['error_rate']:.2f}%")
        print()

        if log_data["common_errors"]:
            print("Top Error Patterns:")
            for error, count in list(log_data["common_errors"].items())[:5]:
                print(f"  • {error[:60]:60s} ({count} times)")
            print()

        if log_data["performance_issues"]:
            print(f"Performance Issues Found: {len(log_data['performance_issues'])}")
            for issue in log_data["performance_issues"][-3:]:  # Show last 3
                print(
                    f"  • {issue['file']}:{issue['line_number']} - {issue['content'][:50]}..."
                )
            print()

        # Session activity
        print("📱 SESSION ACTIVITY")
        print("=" * 50)
        session_data = data["session_activity"]
        print(f"Active Sessions (1h):    {session_data['active_sessions']}")
        print(f"Total Sessions (24h):    {session_data['total_sessions']}")
        print(f"Recent Tool Calls (1h):  {session_data['recent_tool_calls']}")
        print()

        # Cache statistics
        print("🗄️  CACHE STATISTICS")
        print("=" * 50)
        cache_stats = collector.get_cache_stats()
        total_cached_items = sum(cache_stats.values())
        print(f"Total Cached Items: {total_cached_items}")
        for cache_name, size in cache_stats.items():
            print(f"  {cache_name:20s}: {size:4d} items")
        print()

        # Project-specific metrics example
        print("📁 PROJECT METRICS EXAMPLE")
        print("=" * 50)
        project_metrics = collector.get_project_metrics("claude-monitor")
        print(f"Project: {project_metrics.project_name}")
        print(f"Active Sessions: {project_metrics.active_sessions}")
        print(f"Error Rate: {project_metrics.error_rate:.2f}%")
        print(f"Token Cost: ${project_metrics.token_usage.total_cost:.4f}")
        print()

        print("=" * 50)
        print("✅ Data collection demonstration completed!")

        # Optionally save data to file
        save_data = input("Save collected data to JSON file? (y/N): ").lower().strip()
        if save_data == "y":
            filename = f"metrics_{int(time.time())}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"📄 Data saved to {filename}")

    except Exception as e:
        print(f"❌ Error during data collection: {e}")
        raise
    finally:
        # Cleanup
        collector.executor.shutdown(wait=True)


async def continuous_monitoring_demo():
    """Demonstrate continuous monitoring capabilities."""
    print("🔄 Starting continuous monitoring demo (30 seconds)...")

    collector = DataCollector()

    try:
        for i in range(6):  # Monitor for 30 seconds (6 * 5 seconds)
            print(f"\n📊 Update {i+1}/6:")

            # Collect key metrics
            token_metrics = collector.db_collector.get_token_metrics(hours_back=1)
            system_metrics = collector.system_collector.get_system_metrics()

            print(
                f"  Tokens (1h): {token_metrics.total_tokens:,} | Cost: ${token_metrics.total_cost:.4f}"
            )
            print(
                f"  CPU: {system_metrics.cpu_percent:5.1f}% | Memory: {system_metrics.memory_percent:5.1f}%"
            )

            if i < 5:  # Don't sleep on last iteration
                await asyncio.sleep(5)

        print("\n✅ Continuous monitoring demo completed!")

    except Exception as e:
        print(f"❌ Error during continuous monitoring: {e}")
    finally:
        collector.executor.shutdown(wait=True)


async def main():
    """Main demo function."""
    print("Claude Monitor Data Collection Service")
    print("=====================================\n")

    while True:
        print("Available demos:")
        print("1. Comprehensive data collection")
        print("2. Continuous monitoring (30 seconds)")
        print("3. Exit")

        choice = input("\nSelect demo (1-3): ").strip()

        if choice == "1":
            await demonstrate_data_collection()
        elif choice == "2":
            await continuous_monitoring_demo()
        elif choice == "3":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

        if choice in ["1", "2"]:
            input("\nPress Enter to continue...")
            print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
