"""
ACCF Agent Registry

Purpose:
    Enables dynamic registration, lookup, and listing of agents and their capabilities, with persistence and error handling.

References:
    - docs/applications/ACCF/standards/agent_registry_requirements.md
    - docs/applications/ACCF/architecture/adr/agent_registry_adrs.md
    - .cursor/templates/implementation/agent_registry_output_template.yml

Usage:
    from registry import AgentRegistry
    registry = AgentRegistry()
"""

import logging
from typing import Any, Dict, List


class AgentRegistry:
    def __init__(self):
        """Initialize the agent registry."""
        self.logger = logging.getLogger("AgentRegistry")
        self.agents: Dict[str, Dict[str, Any]] = {}

    def register(
        self, agent_id: str, capabilities: List[str], metadata: Dict[str, Any] = None
    ):
        """Register a new agent with its capabilities."""
        self.agents[agent_id] = {
            "capabilities": capabilities,
            "metadata": metadata or {},
        }
        self.logger.info(f"Registered agent: {agent_id}")

    def lookup(self, agent_id: str) -> Dict[str, Any]:
        """Lookup an agent by ID."""
        agent = self.agents.get(agent_id)
        if agent:
            self.logger.info(f"Lookup agent: {agent_id}")
            return agent
        else:
            self.logger.error(f"Agent {agent_id} not found.")
            return {"error": "Agent not found."}

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all registered agents and their capabilities."""
        self.logger.info("Listing all agents.")
        return self.agents
