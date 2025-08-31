"""Agent Registry System for HECATON.

Provides registration, discovery, and management of agents with
health monitoring and load balancing capabilities.
"""

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AgentStatus(Enum):
    """Agent operational status."""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    INITIALIZING = "initializing"


@dataclass
class Agent:
    """Agent representation with metadata and capabilities."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    capabilities: Set[str] = field(default_factory=set)
    status: AgentStatus = AgentStatus.INITIALIZING
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    task_count: int = 0
    error_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if agent is healthy based on heartbeat."""
        if self.status == AgentStatus.OFFLINE:
            return False
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        return time_since_heartbeat < timeout_seconds

    def update_heartbeat(self):
        """Update the last heartbeat timestamp."""
        self.last_heartbeat = datetime.now()
        if self.status == AgentStatus.OFFLINE:
            self.status = AgentStatus.IDLE


class AgentRegistry:
    """Registry for managing agents with discovery and load balancing."""

    def __init__(self, heartbeat_timeout: int = 60):
        """Initialize the agent registry.

        Args:
            heartbeat_timeout: Seconds before considering an agent unhealthy
        """
        self._agents: Dict[str, Agent] = {}
        self._capability_index: Dict[str, Set[str]] = defaultdict(set)
        self._heartbeat_timeout = heartbeat_timeout
        self._task_distribution: Dict[str, int] = defaultdict(int)

    def register(self, agent: Agent) -> str:
        """Register a new agent.

        Args:
            agent: Agent instance to register

        Returns:
            Agent ID
        """
        if not agent.id:
            agent.id = str(uuid.uuid4())

        self._agents[agent.id] = agent

        # Update capability index
        for capability in agent.capabilities:
            self._capability_index[capability].add(agent.id)

        # Initialize task distribution tracking
        self._task_distribution[agent.id] = 0

        return agent.id

    def deregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry.

        Args:
            agent_id: ID of agent to remove

        Returns:
            True if agent was found and removed, False otherwise
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]

        # Remove from capability index
        for capability in agent.capabilities:
            self._capability_index[capability].discard(agent_id)
            if not self._capability_index[capability]:
                del self._capability_index[capability]

        # Remove from agents and task distribution
        del self._agents[agent_id]
        if agent_id in self._task_distribution:
            del self._task_distribution[agent_id]

        return True

    def find_by_capability(self, capability: str) -> List[Agent]:
        """Find all agents with a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability
        """
        agent_ids = self._capability_index.get(capability, set())
        agents = []

        for agent_id in agent_ids:
            agent = self._agents.get(agent_id)
            if agent and agent.is_healthy(self._heartbeat_timeout):
                agents.append(agent)

        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieve a specific agent by ID.

        Args:
            agent_id: ID of agent to retrieve

        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents.

        Returns:
            List of all agents
        """
        return list(self._agents.values())

    def update_heartbeat(self, agent_id: str) -> bool:
        """Update an agent's heartbeat timestamp.

        Args:
            agent_id: ID of agent to update

        Returns:
            True if agent was found and updated, False otherwise
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.update_heartbeat()
            return True
        return False

    def get_healthy_agents(self) -> List[Agent]:
        """Get all healthy agents based on heartbeat.

        Returns:
            List of healthy agents
        """
        return [
            agent for agent in self._agents.values() if agent.is_healthy(self._heartbeat_timeout)
        ]

    def get_unhealthy_agents(self) -> List[Agent]:
        """Get all unhealthy agents based on heartbeat.

        Returns:
            List of unhealthy agents
        """
        return [
            agent
            for agent in self._agents.values()
            if not agent.is_healthy(self._heartbeat_timeout)
        ]

    def mark_offline(self, agent_id: str) -> bool:
        """Mark an agent as offline.

        Args:
            agent_id: ID of agent to mark offline

        Returns:
            True if agent was found and marked, False otherwise
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = AgentStatus.OFFLINE
            return True
        return False

    def get_least_loaded_agent(self, capability: Optional[str] = None) -> Optional[Agent]:
        """Get the agent with the lowest task count.

        Implements load balancing by selecting the healthy agent
        with the fewest assigned tasks.

        Args:
            capability: Optional capability filter

        Returns:
            Agent with lowest load or None if no agents available
        """
        if capability:
            candidates = self.find_by_capability(capability)
        else:
            candidates = self.get_healthy_agents()

        if not candidates:
            return None

        # Filter to only IDLE agents
        idle_agents = [a for a in candidates if a.status == AgentStatus.IDLE]

        # If no idle agents, return None (all are busy)
        if not idle_agents:
            return None

        # Return agent with lowest task count
        return min(idle_agents, key=lambda a: a.task_count)

    def assign_task(self, agent_id: str) -> bool:
        """Increment task count for load balancing.

        Args:
            agent_id: ID of agent assigned a task

        Returns:
            True if agent was found and updated, False otherwise
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.task_count += 1
            agent.status = AgentStatus.BUSY
            self._task_distribution[agent_id] += 1
            return True
        return False

    def complete_task(self, agent_id: str) -> bool:
        """Mark a task as completed for an agent.

        Args:
            agent_id: ID of agent that completed a task

        Returns:
            True if agent was found and updated, False otherwise
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = AgentStatus.IDLE
            return True
        return False

    def report_error(self, agent_id: str) -> bool:
        """Record an error for an agent.

        Args:
            agent_id: ID of agent that encountered an error

        Returns:
            True if agent was found and updated, False otherwise
        """
        agent = self._agents.get(agent_id)
        if agent:
            agent.error_count += 1
            agent.status = AgentStatus.ERROR
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics.

        Returns:
            Dictionary with registry metrics
        """
        healthy = self.get_healthy_agents()
        unhealthy = self.get_unhealthy_agents()

        status_counts = defaultdict(int)
        for agent in self._agents.values():
            status_counts[agent.status.value] += 1

        return {
            "total_agents": len(self._agents),
            "healthy_agents": len(healthy),
            "unhealthy_agents": len(unhealthy),
            "status_breakdown": dict(status_counts),
            "total_capabilities": len(self._capability_index),
            "capability_coverage": {
                cap: len(agents) for cap, agents in self._capability_index.items()
            },
            "task_distribution": dict(self._task_distribution),
            "total_tasks_assigned": sum(self._task_distribution.values()),
        }
