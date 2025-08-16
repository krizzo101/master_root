"""
Agent Registry for Multi-Agent System

Provides centralized agent lifecycle management, discovery, and health monitoring
for the AI-Powered Development Workflow System.

Author: AI Agent System
Created: 2025-01-27
"""

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from uuid import uuid4
from weakref import WeakValueDictionary

from src.agents.base_agent import BaseAgent, AgentState


class RegistrationStatus(Enum):
    """Agent registration status."""

    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    DEREGISTERED = "deregistered"


@dataclass
class AgentRegistration:
    """Agent registration information."""

    agent_id: str
    agent_instance: BaseAgent
    status: RegistrationStatus
    capabilities: List[str]
    tags: Set[str] = field(default_factory=set)
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: Optional[datetime] = None
    heartbeat_interval: int = 30  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """Check if agent is considered healthy based on heartbeat."""
        if not self.last_heartbeat:
            return False

        threshold = datetime.now(timezone.utc) - timedelta(
            seconds=self.heartbeat_interval * 2
        )
        return self.last_heartbeat > threshold

    def should_heartbeat(self) -> bool:
        """Check if agent should send a heartbeat."""
        if not self.last_heartbeat:
            return True

        threshold = datetime.now(timezone.utc) - timedelta(
            seconds=self.heartbeat_interval
        )
        return self.last_heartbeat <= threshold


class AgentRegistry:
    """
    Centralized registry for agent lifecycle management and discovery.

    Manages agent registration, deregistration, health monitoring,
    and provides discovery services for agent coordination.
    """

    def __init__(self):
        """Initialize agent registry."""
        self.logger = logging.getLogger(__name__)

        # Core registry storage - using WeakValueDictionary for memory efficiency
        self._agents: Dict[str, AgentRegistration] = {}

        # Optimized indexes using defaultdict(set) for O(1) operations
        self._capabilities_index: Dict[str, Set[str]] = defaultdict(set)
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)
        self._status_index: Dict[RegistrationStatus, Set[str]] = defaultdict(set)

        # Performance monitoring
        self._operation_lock = asyncio.Lock()  # For thread-safe operations
        self._last_cleanup = datetime.now(timezone.utc)
        self._cleanup_interval = 300  # 5 minutes

        # Registry state
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Statistics for performance monitoring
        self._stats = {
            "registrations": 0,
            "deregistrations": 0,
            "heartbeats": 0,
            "lookups": 0,
            "last_reset": datetime.now(timezone.utc),
        }

        self.logger.info("Scalable agent registry initialized with optimized indexes")

    async def start(self) -> None:
        """Start registry services."""
        if self._running:
            return

        self._running = True

        # Start monitoring tasks
        self._monitor_task = asyncio.create_task(self._health_monitor())
        self._cleanup_task = asyncio.create_task(self._cleanup_monitor())

        self.logger.info(
            "Scalable agent registry started with health and cleanup monitoring"
        )

    async def stop(self) -> None:
        """Stop registry services."""
        if not self._running:
            return

        self._running = False

        # Stop monitoring tasks
        for task in [self._monitor_task, self._cleanup_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Deregister all agents efficiently
        async with self._operation_lock:
            agent_ids = list(self._agents.keys())
            for agent_id in agent_ids:
                await self._deregister_agent_unsafe(agent_id)

        self.logger.info(
            "Scalable agent registry stopped with cleanup statistics: %s", self._stats
        )

    async def register_agent(
        self,
        agent: BaseAgent,
        capabilities: List[str],
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register an agent with the registry.

        Args:
            agent: Agent instance to register
            capabilities: List of agent capabilities
            tags: Optional tags for categorization
            metadata: Optional metadata dictionary

        Returns:
            Agent ID assigned to the registered agent

        Raises:
            ValueError: If agent is already registered
        """
        async with self._operation_lock:
            # Generate ID if needed
            if not agent.agent_id:
                agent.agent_id = str(uuid4())

            if agent.agent_id in self._agents:
                raise ValueError(f"Agent {agent.agent_id} already registered")

            registration = AgentRegistration(
                agent_id=agent.agent_id,
                agent_instance=agent,
                status=RegistrationStatus.REGISTERED,
                capabilities=capabilities,
                tags=tags or set(),
                metadata=metadata or {},
            )

            # Store registration
            self._agents[agent.agent_id] = registration

            # Update optimized indexes (O(1) operations with defaultdict)
            for capability in capabilities:
                self._capabilities_index[capability].add(agent.agent_id)

            for tag in registration.tags:
                self._tags_index[tag].add(agent.agent_id)

            # Update status index
            self._status_index[RegistrationStatus.REGISTERED].add(agent.agent_id)

            # Update statistics
            self._stats["registrations"] += 1

            # Send initial heartbeat
            await self.heartbeat(agent.agent_id)

            self.logger.info(
                f"Agent registered: {agent.agent_id} with capabilities {capabilities} [Total: {len(self._agents)}]"
            )

            return agent.agent_id

    async def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the registry.

        Args:
            agent_id: ID of agent to deregister

        Returns:
            True if agent was deregistered, False if not found
        """
        async with self._operation_lock:
            return await self._deregister_agent_unsafe(agent_id)

    async def _deregister_agent_unsafe(self, agent_id: str) -> bool:
        """
        Deregister an agent without acquiring lock (for internal use).

        Args:
            agent_id: ID of agent to deregister

        Returns:
            True if agent was deregistered, False if not found
        """
        if agent_id not in self._agents:
            return False

        registration = self._agents[agent_id]
        old_status = registration.status

        # Update status
        registration.status = RegistrationStatus.DEREGISTERED

        # Remove from optimized indexes efficiently
        for capability in registration.capabilities:
            self._capabilities_index[capability].discard(agent_id)

        for tag in registration.tags:
            self._tags_index[tag].discard(agent_id)

        # Update status index
        self._status_index[old_status].discard(agent_id)
        self._status_index[RegistrationStatus.DEREGISTERED].add(agent_id)

        # Stop agent if running
        try:
            if registration.agent_instance.state != AgentState.STOPPED:
                await registration.agent_instance.stop()
        except Exception as e:
            self.logger.warning(f"Error stopping agent {agent_id}: {e}")

        # Remove from registry
        del self._agents[agent_id]

        # Update statistics
        self._stats["deregistrations"] += 1

        self.logger.info(f"Agent deregistered: {agent_id} [Total: {len(self._agents)}]")
        return True

    async def heartbeat(self, agent_id: str) -> bool:
        """
        Record heartbeat for an agent.

        Args:
            agent_id: ID of agent sending heartbeat

        Returns:
            True if heartbeat recorded, False if agent not found
        """
        # Use read lock for better concurrency on heartbeats (they're frequent)
        if agent_id not in self._agents:
            return False

        registration = self._agents[agent_id]
        old_status = registration.status
        registration.last_heartbeat = datetime.now(timezone.utc)

        # Update status based on agent state
        agent_state = registration.agent_instance.state
        new_status = registration.status

        if agent_state == AgentState.RUNNING:
            new_status = RegistrationStatus.ACTIVE
        elif agent_state == AgentState.STOPPED:
            new_status = RegistrationStatus.INACTIVE
        elif agent_state == AgentState.ERROR:
            new_status = RegistrationStatus.FAILED

        # Update status index if status changed
        if old_status != new_status:
            self._status_index[old_status].discard(agent_id)
            self._status_index[new_status].add(agent_id)
            registration.status = new_status

        # Update statistics
        self._stats["heartbeats"] += 1

        return True

    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find agents with a specific capability. Optimized O(1) lookup.

        Args:
            capability: Capability to search for

        Returns:
            List of agent IDs with the capability
        """
        self._stats["lookups"] += 1
        return list(
            self._capabilities_index[capability]
        )  # defaultdict returns empty set if not found

    def find_agents_by_tag(self, tag: str) -> List[str]:
        """
        Find agents with a specific tag. Optimized O(1) lookup.

        Args:
            tag: Tag to search for

        Returns:
            List of agent IDs with the tag
        """
        self._stats["lookups"] += 1
        return list(self._tags_index[tag])  # defaultdict returns empty set if not found

    def find_agents_by_status(self, status: RegistrationStatus) -> List[str]:
        """
        Find agents with a specific status. Optimized O(1) lookup using status index.

        Args:
            status: Status to search for

        Returns:
            List of agent IDs with the status
        """
        self._stats["lookups"] += 1
        return list(
            self._status_index[status]
        )  # defaultdict returns empty set if not found

    def get_agent_info(self, agent_id: str) -> Optional[AgentRegistration]:
        """
        Get registration information for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            AgentRegistration if found, None otherwise
        """
        return self._agents.get(agent_id)

    def get_agent_instance(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get agent instance by ID.

        Args:
            agent_id: Agent ID

        Returns:
            BaseAgent instance if found, None otherwise
        """
        registration = self._agents.get(agent_id)
        return registration.agent_instance if registration else None

    def list_agents(
        self, status_filter: Optional[RegistrationStatus] = None
    ) -> List[str]:
        """
        List registered agent IDs, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of agent IDs
        """
        if status_filter:
            return self.find_agents_by_status(status_filter)
        return list(self._agents.keys())

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get detailed performance metrics for monitoring.

        Returns:
            Dictionary with performance metrics
        """
        uptime = datetime.now(timezone.utc) - self._stats["last_reset"]
        uptime_hours = uptime.total_seconds() / 3600

        return {
            "operations_per_hour": {
                "registrations": self._stats["registrations"] / max(uptime_hours, 1),
                "deregistrations": self._stats["deregistrations"]
                / max(uptime_hours, 1),
                "heartbeats": self._stats["heartbeats"] / max(uptime_hours, 1),
                "lookups": self._stats["lookups"] / max(uptime_hours, 1),
            },
            "efficiency_metrics": {
                "registry_size": len(self._agents),
                "index_sizes": {
                    "capabilities": len(self._capabilities_index),
                    "tags": len(self._tags_index),
                    "statuses": len(self._status_index),
                },
                "memory_efficiency": {
                    "agents_per_capability": len(self._agents)
                    / max(len(self._capabilities_index), 1),
                    "agents_per_tag": len(self._agents) / max(len(self._tags_index), 1),
                },
            },
            "uptime": {
                "seconds": uptime.total_seconds(),
                "hours": uptime_hours,
                "since": self._stats["last_reset"].isoformat(),
            },
        }

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive registry statistics.

        Returns:
            Dictionary with detailed registry statistics
        """
        # Use optimized status index for counts
        status_counts = {
            status.value: len(self._status_index[status])
            for status in RegistrationStatus
        }

        healthy_count = sum(1 for reg in self._agents.values() if reg.is_healthy())

        # Calculate uptime
        uptime = datetime.now(timezone.utc) - self._stats["last_reset"]

        return {
            "total_agents": len(self._agents),
            "status_counts": status_counts,
            "healthy_agents": healthy_count,
            "capabilities": {
                "count": len(self._capabilities_index),
                "list": list(self._capabilities_index.keys()),
            },
            "tags": {
                "count": len(self._tags_index),
                "list": list(self._tags_index.keys()),
            },
            "performance": {
                "registrations": self._stats["registrations"],
                "deregistrations": self._stats["deregistrations"],
                "heartbeats": self._stats["heartbeats"],
                "lookups": self._stats["lookups"],
                "uptime_seconds": uptime.total_seconds(),
                "avg_heartbeats_per_minute": self._stats["heartbeats"]
                / max(uptime.total_seconds() / 60, 1),
            },
        }

    async def _health_monitor(self) -> None:
        """Monitor agent health and update statuses."""
        while self._running:
            try:
                current_time = datetime.now(timezone.utc)

                for agent_id, registration in self._agents.items():
                    # Check if agent should send heartbeat
                    if registration.should_heartbeat():
                        try:
                            # Request heartbeat from agent
                            if hasattr(registration.agent_instance, "send_heartbeat"):
                                await registration.agent_instance.send_heartbeat()
                        except Exception as e:
                            self.logger.warning(
                                f"Heartbeat request failed for {agent_id}: {e}"
                            )

                    # Check health status
                    if not registration.is_healthy():
                        old_status = registration.status
                        registration.status = RegistrationStatus.FAILED

                        if old_status != RegistrationStatus.FAILED:
                            self.logger.warning(
                                f"Agent {agent_id} marked as failed (no heartbeat)"
                            )

                # Sleep before next check
                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)

    async def _cleanup_monitor(self) -> None:
        """Monitor and clean up stale data structures for memory efficiency."""
        while self._running:
            try:
                current_time = datetime.now(timezone.utc)

                # Cleanup every 5 minutes
                if (
                    current_time - self._last_cleanup
                ).total_seconds() >= self._cleanup_interval:
                    await self._perform_cleanup()
                    self._last_cleanup = current_time

                # Sleep for 60 seconds between cleanup checks
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup monitor error: {e}")
                await asyncio.sleep(30)

    async def _perform_cleanup(self) -> None:
        """Perform registry cleanup operations."""
        async with self._operation_lock:
            # Clean up empty index entries (shouldn't happen with defaultdict, but defensive)
            empty_capabilities = [
                cap for cap, agents in self._capabilities_index.items() if not agents
            ]
            for cap in empty_capabilities:
                del self._capabilities_index[cap]

            empty_tags = [tag for tag, agents in self._tags_index.items() if not agents]
            for tag in empty_tags:
                del self._tags_index[tag]

            empty_statuses = [
                status for status, agents in self._status_index.items() if not agents
            ]
            for status in empty_statuses:
                del self._status_index[status]

            # Reset statistics periodically to prevent overflow
            if self._stats["heartbeats"] > 1000000:  # Reset after 1M heartbeats
                old_stats = self._stats.copy()
                self._stats = {
                    "registrations": 0,
                    "deregistrations": 0,
                    "heartbeats": 0,
                    "lookups": 0,
                    "last_reset": datetime.now(timezone.utc),
                }
                self.logger.info(f"Registry statistics reset. Previous: {old_stats}")

            self.logger.debug(
                f"Registry cleanup completed. Agents: {len(self._agents)}, Capabilities: {len(self._capabilities_index)}, Tags: {len(self._tags_index)}"
            )


# Global registry instance
_registry_instance: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance


async def initialize_registry() -> AgentRegistry:
    """Initialize and start the global agent registry."""
    registry = get_registry()
    await registry.start()
    return registry


async def shutdown_registry() -> None:
    """Shutdown the global agent registry."""
    global _registry_instance
    if _registry_instance:
        await _registry_instance.stop()
        _registry_instance = None
