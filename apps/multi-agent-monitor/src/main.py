#!/usr/bin/env python3
"""
Main entry point for Multi-Agent Monitor System
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.multi_agent_monitor.src.commands.team_orchestrate import main as cli_main
from apps.multi_agent_monitor.src.orchestration import (
    AgentTeamOrchestrator,
    ProjectType,
)

if __name__ == "__main__":
    # Run CLI
    asyncio.run(cli_main())
