#!/usr/bin/env python3
"""
Hierarchical COMPETITIVE swarm test - 3 teams competing, each with 3 agents = 12 total
Teams compete in parallel challenges - ultimate token pool stress test!
"""

import asyncio
import sys
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def create_hierarchical_swarm():
    """Create 3 parent agents that each spawn 3 child agents"""

    # The 3 parent agents - each will spawn 3 children
    parent_tasks = [
        AgentTask(
            task_id="team_alpha_file_race",
            task_type="competitive_orchestrator",
            prompt=f"""🏆 TEAM ALPHA - FILE ANALYSIS RACE CAPTAIN!

Your mission: Lead Team Alpha in the Great File Analysis Competition! You're racing against Team Beta and Team Gamma.

COMPETITION CHALLENGE: "Who can analyze the most files the fastest?"

1. Deploy your 3 specialist agents immediately in parallel:

🥇 SPEED AGENT: "RACE MODE: Count ALL files in /home/opsvi/master_root as fast as possible! Report total counts by file type and announce your speed!"
🥈 SIZE AGENT: "RACE MODE: Find the 20 LARGEST files in the entire project! Report sizes in MB and race for completion!"
🥉 HUNTER AGENT: "RACE MODE: Hunt for ALL config files (.conf, .cfg, .ini, .yaml, .yml, .json) and analyze them faster than the competition!"

2. Use this exact command structure:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="alpha_speed", task_type="racing", prompt="RACE MODE: Count ALL files..."),
    AgentTask(task_id="alpha_size", task_type="racing", prompt="RACE MODE: Find 20 LARGEST files..."),
    AgentTask(task_id="alpha_hunter", task_type="racing", prompt="RACE MODE: Hunt ALL config files...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/team_alpha_race"))
results = await orchestrator.execute_batch(tasks)
```

3. 🏁 VICTORY CONDITIONS: First team to complete all 3 analysis tasks wins! Announce completion times loudly!
4. 📢 Keep your team motivated with competitive commentary throughout the race!
5. ⚡ This is a SPEED COMPETITION - go as fast as possible while being thorough!""",
            context={"timeout": 300},
        ),
        AgentTask(
            task_id="team_beta_system_race",
            task_type="competitive_orchestrator",
            prompt=f"""🔥 TEAM BETA - SYSTEM MONITORING CHAMPIONS!

You're competing against Team Alpha and Team Gamma in the ULTIMATE SYSTEM RACE!

COMPETITION CHALLENGE: "Who can monitor the most system metrics the fastest?"

1. Spawn 3 child monitoring agents in parallel using the orchestrator:

Child 1: "Monitor disk usage, free space, and I/O activity continuously for 2 minutes - check every 30 seconds"
Child 2: "Track memory usage, swap usage, and top memory processes continuously for 2 minutes - check every 30 seconds"
Child 3: "Monitor network connections, listening ports, and network activity for 2 minutes - check every 30 seconds"

2. Use the orchestrator pattern:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="disk_monitor", task_type="monitoring", prompt="Monitor disk usage..."),
    AgentTask(task_id="memory_monitor", task_type="monitoring", prompt="Track memory usage..."),
    AgentTask(task_id="network_monitor", task_type="monitoring", prompt="Monitor network connections...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/parent_system_monitor"))
results = await orchestrator.execute_batch(tasks)
```

3. Coordinate the monitoring and provide consolidated reports.
4. Should run for 3-4 minutes with overlapping monitoring activity.""",
            context={"timeout": 300},
        ),
        AgentTask(
            task_id="parent_process_analyzer",
            task_type="orchestrator",
            prompt=f"""You are a parent agent that coordinates process analysis.

1. Launch 3 child process analysis agents in parallel:

Child 1: "Analyze running processes - find top CPU users, long-running processes, and process trees for 2 minutes"
Child 2: "Monitor log files - check /var/log for recent entries, errors, and patterns for 2 minutes"
Child 3: "Track service status - check systemd services, cron jobs, and background tasks for 2 minutes"

2. Orchestrate them with:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="process_analyzer", task_type="analysis", prompt="Analyze running processes..."),
    AgentTask(task_id="log_monitor", task_type="monitoring", prompt="Monitor log files..."),
    AgentTask(task_id="service_tracker", task_type="monitoring", prompt="Track service status...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/parent_process_analyzer"))
results = await orchestrator.execute_batch(tasks)
```

3. Synthesize findings from all 3 children into comprehensive process analysis.
4. Run for 3-4 minutes with continuous child agent coordination.""",
            context={"timeout": 300},
        ),
    ]

    # Create parent orchestrator
    orchestrator = GenericOrchestrator(
        max_parallel=3,  # 3 parents run in parallel
        output_dir=Path("/tmp/hierarchical_swarm_output"),
    )

    print("🌳 Starting HIERARCHICAL swarm test...")
    print("👥 3 parent agents each spawning 3 child agents = 12 total agents")
    print("⏰ Expected duration: 4-5 minutes")
    print("🔍 Monitor with: ./chat-monitor grid --size 4x4")
    print("💡 You should see 12 agents working simultaneously!")
    print("🎯 Ultimate test of token pool parallelism (19 tokens vs 12 agents)")
    print("")

    # Execute the 3 parent agents in parallel (each will spawn 3 children)
    results = await orchestrator.execute_batch(parent_tasks)

    print("✅ Hierarchical swarm execution complete!")
    print(
        f"📈 Parent Results: {len([r for r in results if r.get('status') == 'completed'])} completed, {len([r for r in results if r.get('status') == 'failed'])} failed"
    )

    return results


if __name__ == "__main__":
    asyncio.run(create_hierarchical_swarm())
