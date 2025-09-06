#!/usr/bin/env python3
"""
Sustained swarm test - 5 agents doing continuous work for several minutes
Each agent does multiple sequential tasks to test true parallelism
"""

import asyncio
import sys
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def create_sustained_swarm():
    """Create 5 agents that do sustained work over several minutes"""

    tasks = [
        AgentTask(
            task_id="continuous_analysis",
            task_type="analysis",
            prompt="""Perform continuous system analysis over 5 minutes:
1. Count files in /tmp and /var/tmp every 30 seconds (5 iterations)
2. Check disk usage with df -h every 30 seconds
3. List top 5 processes by memory every 30 seconds
4. Between each check, sleep 30 seconds and announce what you're doing
5. Provide running commentary on any changes you observe
6. At the end, give a summary of patterns observed

Take your time and be thorough - this should run for about 5 minutes total.""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="file_watcher",
            task_type="monitoring",
            prompt="""Monitor file system activity for 5 minutes:
1. Find all files modified in the last hour in /home/opsvi/master_root
2. Watch for new files being created every 30 seconds (10 iterations)
3. Track which directories are most active
4. Sleep 30 seconds between each check and report what you see
5. Count total files vs directories in different subdirectories
6. Look for patterns in file creation/modification
7. End with a summary of file system activity patterns

This should take about 5 minutes of continuous monitoring.""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="network_monitor",
            task_type="monitoring",
            prompt="""Monitor network and process activity for 5 minutes:
1. Check listening ports with netstat every 45 seconds
2. Monitor top CPU processes every 45 seconds (7 iterations)
3. Check memory usage patterns every 45 seconds
4. Look for any new processes starting/stopping
5. Sleep 45 seconds between checks and describe what you observe
6. Track which services are most active
7. Provide continuous commentary on system behavior

Take full 5 minutes and be very detailed in observations.""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="log_analyzer",
            task_type="analysis",
            prompt="""Analyze system logs continuously for 5 minutes:
1. Check /var/log/syslog for recent entries every 40 seconds
2. Look at dmesg output every 40 seconds (8 iterations)
3. Monitor auth logs if accessible
4. Track patterns in log messages over time
5. Sleep 40 seconds between analyses and report findings
6. Look for any error patterns or anomalies
7. Count different types of log entries
8. End with comprehensive log analysis summary

This should run for the full 5 minutes with detailed analysis.""",
            context={"timeout": 400},
        ),
        AgentTask(
            task_id="resource_tracker",
            task_type="monitoring",
            prompt="""Track resource utilization continuously for 5 minutes:
1. Monitor CPU load average every 35 seconds (9 iterations)
2. Track memory usage trends every 35 seconds
3. Watch disk I/O if possible every 35 seconds
4. Monitor swap usage every 35 seconds
5. Sleep 35 seconds between checks and provide commentary
6. Calculate resource usage trends over time
7. Identify peak usage periods
8. Look for resource usage patterns

Run for full 5 minutes with continuous resource monitoring and analysis.""",
            context={"timeout": 400},
        ),
    ]

    # Create orchestrator with all 5 running in parallel
    orchestrator = GenericOrchestrator(
        max_parallel=5,  # All 5 can run simultaneously
        output_dir=Path("/tmp/sustained_swarm_output"),
    )

    print("🐝 Starting 5-agent SUSTAINED swarm test...")
    print("📊 Each agent will work continuously for ~5 minutes")
    print("⏰ Total expected duration: 5-6 minutes")
    print("🔍 Monitor with: ./chat-monitor swarm (in another terminal)")
    print("💡 You should see CONTINUOUS overlapping activity from all 5 agents")
    print("")

    # Execute all tasks in parallel
    results = await orchestrator.execute_batch(tasks)

    print("✅ Sustained swarm execution complete!")
    print(
        f"📈 Results: {len([r for r in results if r.get('status') == 'completed'])} completed, {len([r for r in results if r.get('status') == 'failed'])} failed"
    )

    return results


if __name__ == "__main__":
    asyncio.run(create_sustained_swarm())
