#!/usr/bin/env python3
"""
Real-time monitoring of executing agents using chat log analysis
Based on claude_headless_complete_guide.md patterns
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.append("/home/opsvi/master_root/apps/chat-search")


def get_recent_session_files(minutes_ago=10):
    """Get session files created in the last N minutes"""
    chat_logs_dir = Path("/home/opsvi/master_root/chat_logs")
    cutoff_time = time.time() - (minutes_ago * 60)

    recent_files = []
    for file in chat_logs_dir.glob("*.jsonl"):
        if file.stat().st_mtime > cutoff_time:
            recent_files.append(file)

    return sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)


def identify_agent_type(file_path):
    """Try to identify what type of agent this is based on session content"""
    try:
        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = str(message.get("content", ""))

                    # Look for agent type indicators
                    if "solution-architect" in content.lower():
                        return "solution-architect"
                    elif "research-genius" in content.lower():
                        return "research-genius"
                    elif "database-specialist" in content.lower():
                        return "database-specialist"
                    elif "development-specialist" in content.lower():
                        return "development-specialist"
                    elif "api-integration-specialist" in content.lower():
                        return "api-integration-specialist"
                    elif "qa-testing-guru" in content.lower():
                        return "qa-testing-guru"
                    elif "technical-writer" in content.lower():
                        return "technical-writer"

                    # Look for task indicators
                    if "analyze_existing_systems" in content:
                        return "solution-architect (analyze_existing_systems)"
                    elif "research_timescale_pgvector" in content:
                        return "research-genius (research_timescale_pgvector)"
                    elif "design_unified_schema" in content:
                        return "database-specialist (design_unified_schema)"
                    elif "implement_core_schema" in content:
                        return "database-specialist (implement_core_schema)"

                except json.JSONDecodeError:
                    continue
        return "unknown-agent"
    except Exception:
        return "error-reading"


def get_session_status(file_path):
    """Get the current status of a session"""
    try:
        with open(file_path, "r") as f:
            lines = list(f)

        if not lines:
            return "empty"

        # Check last few lines for completion indicators
        recent_lines = lines[-10:] if len(lines) > 10 else lines

        for line in reversed(recent_lines):
            try:
                data = json.loads(line)
                message = data.get("message", {})
                content = str(message.get("content", "")).lower()

                if any(
                    word in content
                    for word in ["completed", "finished", "✅", "success"]
                ):
                    return "completed"
                elif any(
                    word in content for word in ["error", "failed", "❌", "exception"]
                ):
                    return "failed"
                elif any(
                    word in content for word in ["working", "processing", "analyzing"]
                ):
                    return "active"

            except json.JSONDecodeError:
                continue

        return "active"
    except Exception:
        return "unknown"


def monitor_agents():
    """Monitor currently executing agents"""
    print("🔍 AGENT EXECUTION MONITOR")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get recent session files
    recent_files = get_recent_session_files(minutes_ago=15)

    if not recent_files:
        print("❌ No recent agent sessions found (last 15 minutes)")
        return

    print(f"📊 Found {len(recent_files)} recent sessions:")
    print()

    active_agents = []
    completed_agents = []
    failed_agents = []

    for file_path in recent_files:
        session_id = file_path.stem
        agent_type = identify_agent_type(file_path)
        status = get_session_status(file_path)
        size_kb = file_path.stat().st_size / 1024
        modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

        agent_info = {
            "session_id": session_id,
            "agent_type": agent_type,
            "status": status,
            "size_kb": size_kb,
            "modified": modified_time,
            "file_path": file_path,
        }

        if status == "completed":
            completed_agents.append(agent_info)
        elif status == "failed":
            failed_agents.append(agent_info)
        else:
            active_agents.append(agent_info)

    # Display results
    print("✅ COMPLETED AGENTS:")
    for agent in completed_agents:
        print(
            f"   {agent['agent_type']:35} | {agent['session_id'][:8]}... | {agent['size_kb']:6.1f}KB | {agent['modified'].strftime('%H:%M:%S')}"
        )

    print(f"\n🔄 ACTIVE AGENTS ({len(active_agents)}):")
    for agent in active_agents:
        print(
            f"   {agent['agent_type']:35} | {agent['session_id'][:8]}... | {agent['size_kb']:6.1f}KB | {agent['modified'].strftime('%H:%M:%S')}"
        )

    if failed_agents:
        print(f"\n❌ FAILED AGENTS ({len(failed_agents)}):")
        for agent in failed_agents:
            print(
                f"   {agent['agent_type']:35} | {agent['session_id'][:8]}... | {agent['size_kb']:6.1f}KB | {agent['modified'].strftime('%H:%M:%S')}"
            )

    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Completed: {len(completed_agents)}")
    print(f"   🔄 Active: {len(active_agents)}")
    print(f"   ❌ Failed: {len(failed_agents)}")
    print(f"   📁 Total sessions: {len(recent_files)}")

    # Provide monitoring commands
    if active_agents:
        print(f"\n🔍 REAL-TIME MONITORING COMMANDS:")
        for agent in active_agents[:3]:  # Show top 3 active
            session_id = agent["session_id"]
            print(f"   tail -f /home/opsvi/master_root/chat_logs/{session_id}.jsonl")

    return active_agents, completed_agents, failed_agents


def continuous_monitor(interval_seconds=30):
    """Continuously monitor agents with updates"""
    try:
        while True:
            os.system("clear")  # Clear screen
            active, completed, failed = monitor_agents()

            if not active:
                print(f"\n🎯 All agents completed! No active sessions detected.")
                break

            print(f"\n⏱️  Refreshing in {interval_seconds} seconds... (Ctrl+C to stop)")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\n\n👋 Monitoring stopped by user")


def main():
    """Main monitoring function"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor executing agents")
    parser.add_argument(
        "--continuous",
        "-c",
        action="store_true",
        help="Continuously monitor (refresh every 30s)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)",
    )

    args = parser.parse_args()

    if args.continuous:
        continuous_monitor(args.interval)
    else:
        monitor_agents()


if __name__ == "__main__":
    main()
