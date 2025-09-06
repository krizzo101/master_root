#!/usr/bin/env python3
"""
RESEARCH COMPETITION SWARM - 3 teams competing in parallel research challenges
12 total agents (3 teams × 3 researchers + 3 team captains)
The ultimate test of parallel token usage and research coordination!
"""

import asyncio
import sys
from pathlib import Path

# Add agent-orchestrator to path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))

from generic_orchestrator import AgentTask, GenericOrchestrator


async def create_research_competition():
    """Create 3 competing research teams - each with 3 specialist researchers"""

    # 3 competing research teams
    research_teams = [
        AgentTask(
            task_id="team_alpha_ai_research",
            task_type="research_captain",
            prompt="""🏆 TEAM ALPHA RESEARCH CAPTAIN - AI & MACHINE LEARNING DIVISION

RESEARCH COMPETITION CHALLENGE: "Who can discover the most cutting-edge AI research insights?"

You're competing against Team Beta (Quantum Computing) and Team Gamma (Cybersecurity) in a 4-minute research sprint!

1. Deploy your 3 AI research specialists immediately:

🧠 AI RESEARCHER 1: "Research latest LLM breakthroughs from 2024-2025 using mcp__mcp_web_search and mcp__research_papers tools. Find 5 significant papers with full citations (author, title, date, DOI/arXiv). Summarize key innovations!"

🤖 AI RESEARCHER 2: "Use mcp__firecrawl__firecrawl_search and web research to investigate AI agents and multi-agent systems. Focus on 2024-2025 research with proper citations. Find breakthrough architectures!"

⚡ AI RESEARCHER 3: "Research cutting-edge AI applications using all MCP research tools - mcp__mcp_web_search, mcp__research_papers, mcp__firecrawl. Find 2024-2025 developments with academic citations!"

2. Orchestration code:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="llm_researcher", task_type="research", prompt="Research latest LLM breakthroughs..."),
    AgentTask(task_id="agent_researcher", task_type="research", prompt="Investigate AI agents..."),
    AgentTask(task_id="app_researcher", task_type="research", prompt="Research cutting-edge AI applications...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/team_alpha_ai_research"))
results = await orchestrator.execute_batch(tasks)
```

3. 🏁 VICTORY CONDITIONS: Most groundbreaking research with proper academic citations wins!
4. 📊 SCORING: Research quality (40%) + Citation accuracy (30%) + Innovation (20%) + Speed (10%)!
5. 🎯 REQUIRED: Use MCP research tools and provide full citations for ALL findings!
6. ⚡ RESEARCH FASTER with better citations than the competition!""",
            context={"timeout": 300},
        ),
        AgentTask(
            task_id="team_beta_quantum_research",
            task_type="research_captain",
            prompt="""⚡ TEAM BETA RESEARCH CAPTAIN - QUANTUM COMPUTING DIVISION

RESEARCH COMPETITION CHALLENGE: "Who can uncover the most revolutionary quantum breakthroughs?"

Racing against Team Alpha (AI) and Team Gamma (Cybersecurity) - QUANTUM SUPREMACY AWAITS!

1. Launch your 3 quantum research experts in parallel:

🔬 QUANTUM RESEARCHER 1: "Research quantum computing breakthroughs from 2024-2025! Find the most significant quantum algorithms, error correction, and hardware advances!"

💫 QUANTUM RESEARCHER 2: "Investigate quantum networking, quantum internet, and quantum communication developments. Focus on latest 2024-2025 achievements!"

🌌 QUANTUM RESEARCHER 3: "Research quantum applications - quantum AI, quantum cryptography, quantum simulation. Find the most game-changing applications!"

2. Deploy with:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="quantum_algo_researcher", task_type="research", prompt="Research quantum computing breakthroughs..."),
    AgentTask(task_id="quantum_net_researcher", task_type="research", prompt="Investigate quantum networking..."),
    AgentTask(task_id="quantum_app_researcher", task_type="research", prompt="Research quantum applications...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/team_beta_quantum_research"))
results = await orchestrator.execute_batch(tasks)
```

3. ⚡ QUANTUM ADVANTAGE: Use quantum research speed to outpace classical teams!
4. 🏆 SCORE: Innovation impact × Research depth × Discovery speed!
5. 🚀 ENTANGLE your research efforts for maximum parallel efficiency!""",
            context={"timeout": 300},
        ),
        AgentTask(
            task_id="team_gamma_cybersec_research",
            task_type="research_captain",
            prompt="""🛡️ TEAM GAMMA RESEARCH CAPTAIN - CYBERSECURITY INTELLIGENCE DIVISION

RESEARCH COMPETITION CHALLENGE: "Who can discover the most critical cybersecurity insights?"

Competing against Team Alpha (AI) and Team Beta (Quantum) - SECURE THE VICTORY!

1. Deploy your 3 cybersecurity research operatives:

🔐 SECURITY RESEARCHER 1: "Research latest cybersecurity threats and vulnerabilities from 2024-2025. Focus on AI-powered attacks, zero-day exploits, and nation-state activities!"

🛡️ SECURITY RESEARCHER 2: "Investigate cutting-edge defense technologies - quantum cryptography, AI-powered security, zero-trust architectures. Find 2024-2025 innovations!"

⚔️ SECURITY RESEARCHER 3: "Research emerging attack vectors - deepfake attacks, supply chain security, IoT vulnerabilities. Find the most concerning 2024-2025 trends!"

2. Execute operation:
```python
import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path("/home/opsvi/master_root/apps/agent-orchestrator/src")))
from generic_orchestrator import AgentTask, GenericOrchestrator

tasks = [
    AgentTask(task_id="threat_researcher", task_type="research", prompt="Research latest cybersecurity threats..."),
    AgentTask(task_id="defense_researcher", task_type="research", prompt="Investigate cutting-edge defenses..."),
    AgentTask(task_id="attack_researcher", task_type="research", prompt="Research emerging attack vectors...")
]

orchestrator = GenericOrchestrator(max_parallel=3, output_dir=Path("/tmp/team_gamma_cybersec_research"))
results = await orchestrator.execute_batch(tasks)
```

3. 🎯 MISSION CRITICAL: First to identify the most critical security insights wins!
4. 📈 METRICS: Threat severity × Defense innovation × Research speed!
5. 🔒 OPERATIONAL SECURITY: Research faster while maintaining information security!""",
            context={"timeout": 300},
        ),
    ]

    # Create competition orchestrator
    orchestrator = GenericOrchestrator(
        max_parallel=3,  # 3 teams compete simultaneously
        output_dir=Path("/tmp/research_competition_output"),
    )

    print("🏆 STARTING RESEARCH COMPETITION SWARM!")
    print("🎯 3 TEAMS × 4 AGENTS = 12 RESEARCHERS COMPETING IN PARALLEL")
    print("⚡ Team Alpha: AI & Machine Learning Research")
    print("⚡ Team Beta: Quantum Computing Research")
    print("⚡ Team Gamma: Cybersecurity Intelligence Research")
    print("⏰ Competition Duration: 4-5 minutes")
    print("🔍 Monitor the battle: ./chat-monitor grid --size 4x4")
    print("🏁 VICTORY CONDITIONS: Most groundbreaking research discoveries!")
    print("💡 This will stress-test all 19 tokens with competitive parallel research!")
    print("")

    # LAUNCH THE RESEARCH COMPETITION!
    results = await orchestrator.execute_batch(research_teams)

    print("🏆 RESEARCH COMPETITION COMPLETE!")
    print(
        f"📊 Team Results: {len([r for r in results if r.get('status') == 'completed'])} teams completed research!"
    )

    return results


if __name__ == "__main__":
    asyncio.run(create_research_competition())
