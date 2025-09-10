#!/usr/bin/env python3
"""
Start the agent orchestrator dashboard
"""
import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps/agent-orchestrator/src"))

from monitoring.dashboard_server import DashboardServer


async def main():
    server = DashboardServer(port=8765)
    await server.start_server()
    print("🚀 Agent Orchestrator Dashboard running on http://localhost:8765")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
