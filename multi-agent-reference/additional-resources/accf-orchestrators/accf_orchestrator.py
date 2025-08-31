"""
Core Orchestrator - Main MCP server routing logic

Handles the central routing between User → MCP → Agents → MCP → User
Currently implements the direct routing pattern, ready for:
- Gatekeeper integration (pre-processing)
- Research agent integration (context enrichment)
- Quality gates (iteration validation)
"""

import asyncio
import os
from typing import Optional

from accf.shared.mcp.mcp_server_template import MCPServerTemplate

from .agent_registry import AgentRegistry


class MCPOrchestrator:
    """Central orchestrator for MCP agent routing."""

    def __init__(self, agent_type: Optional[str] = None):
        self.agent_type = agent_type
        self.registry = AgentRegistry()

    def create_server(self) -> MCPServerTemplate:
        """Create and configure the MCP server."""
        tools = self.registry.get_tools_for_agent_type(self.agent_type)
        server_name = self.registry.get_server_name_for_agent_type(self.agent_type)

        return MCPServerTemplate(name=server_name, tools=tools)

    async def run(self):
        """Run the MCP server."""
        server = self.create_server()
        await server.run()


async def main():
    """Main entry point for MCP server."""
    # No longer need agent type from environment - it's passed as parameter
    orchestrator = MCPOrchestrator()
    await orchestrator.run()


if __name__ == "__main__":
    asyncio.run(main())
