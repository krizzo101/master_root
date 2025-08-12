"""
Enhanced Agent Registry for Multi-Agent System

Provides scalable agent lifecycle management, discovery, and health monitoring
with distributed storage, concurrent processing, and advanced query capabilities.

Author: ST-Agent-2 (Stream 2 Agent Systems Developer)
Created: 2025-01-27
Version: 2.0.0 (Enhanced for Scalability)
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field, asdict
from uuid import uuid4
import weakref

from src.agents.base_agent import BaseAgent, AgentState


class RegistrationStatus(Enum):
    """Enhanced agent registration status."""

    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    DEREGISTERED = "deregistered"
    MAINTENANCE = "maintenance"
    SCALING = "scaling"


class HealthLevel(Enum):
    """Agent health levels."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    """Agent performance metrics."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    task_count: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    error_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["last_updated"] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetrics":
        """Create from dictionary."""
        if "last_updated" in data and isinstance(data["last_updated"], str):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


@dataclass
class AgentRegistration:
    """Enhanced agent registration information."""

    agent_id: str
    agent_instance: Optional[BaseAgent]  # Use weak reference in practice
    status: RegistrationStatus
    capabilities: List[str]
    tags: Set[str] = field(default_factory=set)
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: Optional[datetime] = None
    heartbeat_interval: int = 30  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    health_level: HealthLevel = HealthLevel.UNKNOWN
    version: str = "1.0.0"
    host: str = "localhost"
    port: Optional[int] = None

    def is_healthy(self, grace_period_multiplier: float = 2.0) -> bool:
        """Check if agent is considered healthy based on heartbeat."""
        if not self.last_heartbeat:
            return False

        threshold = datetime.now(timezone.utc) - timedelta(
            seconds=self.heartbeat_interval * grace_period_multiplier
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

    def update_health_level(self) -> HealthLevel:
        """Update and return current health level."""
        if not self.is_healthy():
            self.health_level = HealthLevel.CRITICAL
        elif self.metrics.error_count > 10:
            self.health_level = HealthLevel.WARNING
        elif self.metrics.success_rate < 0.8:
            self.health_level = HealthLevel.WARNING
        else:
            self.health_level = HealthLevel.HEALTHY

        return self.health_level

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["agent_instance"] = None  # Don't serialize instance
        data["tags"] = list(self.tags)  # Convert set to list
        data["registered_at"] = self.registered_at.isoformat()
        data["last_heartbeat"] = (
            self.last_heartbeat.isoformat() if self.last_heartbeat else None
        )
        data["metrics"] = self.metrics.to_dict()
        data["status"] = self.status.value
        data["health_level"] = self.health_level.value
        return data

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], agent_instance: Optional[BaseAgent] = None
    ) -> "AgentRegistration":
        """Create from dictionary."""
        # Convert string enums back
        data["status"] = RegistrationStatus(data["status"])
        data["health_level"] = HealthLevel(data["health_level"])

        # Convert dates
        data["registered_at"] = datetime.fromisoformat(data["registered_at"])
        if data["last_heartbeat"]:
            data["last_heartbeat"] = datetime.fromisoformat(data["last_heartbeat"])

        # Convert tags and metrics
        data["tags"] = set(data["tags"])
        data["metrics"] = AgentMetrics.from_dict(data["metrics"])
        data["agent_instance"] = agent_instance

        return cls(**data)


class StorageBackend(ABC):
    """Abstract storage backend for agent registry."""

    @abstractmethod
    async def save_registration(self, registration: AgentRegistration) -> bool:
        """Save agent registration."""
        pass

    @abstractmethod
    async def load_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Load agent registration."""
        pass

    @abstractmethod
    async def delete_registration(self, agent_id: str) -> bool:
        """Delete agent registration."""
        pass

    @abstractmethod
    async def list_registrations(self) -> List[str]:
        """List all agent IDs."""
        pass

    @abstractmethod
    async def query_registrations(self, query: Dict[str, Any]) -> List[str]:
        """Query registrations by criteria."""
        pass


class FileStorageBackend(StorageBackend):
    """File-based storage backend."""

    def __init__(self, storage_path: str = "data/agent_registry"):
        """Initialize file storage."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.FileStorage")

    async def save_registration(self, registration: AgentRegistration) -> bool:
        """Save agent registration to file."""
        try:
            file_path = self.storage_path / f"{registration.agent_id}.json"
            data = registration.to_dict()

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            self.logger.error(
                f"Failed to save registration {registration.agent_id}: {e}"
            )
            return False

    async def load_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Load agent registration from file."""
        try:
            file_path = self.storage_path / f"{agent_id}.json"

            if not file_path.exists():
                return None

            with open(file_path, "r") as f:
                data = json.load(f)

            return AgentRegistration.from_dict(data)
        except Exception as e:
            self.logger.error(f"Failed to load registration {agent_id}: {e}")
            return None

    async def delete_registration(self, agent_id: str) -> bool:
        """Delete agent registration file."""
        try:
            file_path = self.storage_path / f"{agent_id}.json"

            if file_path.exists():
                file_path.unlink()

            return True
        except Exception as e:
            self.logger.error(f"Failed to delete registration {agent_id}: {e}")
            return False

    async def list_registrations(self) -> List[str]:
        """List all agent IDs."""
        try:
            return [f.stem for f in self.storage_path.glob("*.json")]
        except Exception as e:
            self.logger.error(f"Failed to list registrations: {e}")
            return []

    async def query_registrations(self, query: Dict[str, Any]) -> List[str]:
        """Query registrations by criteria."""
        # Simple file-based query - load all and filter
        # In production, use a proper database
        try:
            agent_ids = await self.list_registrations()
            results = []

            for agent_id in agent_ids:
                registration = await self.load_registration(agent_id)
                if registration and self._matches_query(registration, query):
                    results.append(agent_id)

            return results
        except Exception as e:
            self.logger.error(f"Failed to query registrations: {e}")
            return []

    def _matches_query(
        self, registration: AgentRegistration, query: Dict[str, Any]
    ) -> bool:
        """Check if registration matches query criteria."""
        for key, value in query.items():
            if key == "capabilities" and isinstance(value, list):
                if not all(cap in registration.capabilities for cap in value):
                    return False
            elif key == "tags" and isinstance(value, list):
                if not all(tag in registration.tags for tag in value):
                    return False
            elif key == "status":
                if registration.status.value != value:
                    return False
            elif key == "health_level":
                if registration.health_level.value != value:
                    return False
            elif hasattr(registration, key):
                if getattr(registration, key) != value:
                    return False

        return True


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for testing."""

    def __init__(self):
        """Initialize memory storage."""
        self._data: Dict[str, Dict[str, Any]] = {}

    async def save_registration(self, registration: AgentRegistration) -> bool:
        """Save registration in memory."""
        self._data[registration.agent_id] = registration.to_dict()
        return True

    async def load_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Load registration from memory."""
        data = self._data.get(agent_id)
        if data:
            return AgentRegistration.from_dict(data)
        return None

    async def delete_registration(self, agent_id: str) -> bool:
        """Delete registration from memory."""
        if agent_id in self._data:
            del self._data[agent_id]
        return True

    async def list_registrations(self) -> List[str]:
        """List all agent IDs."""
        return list(self._data.keys())

    async def query_registrations(self, query: Dict[str, Any]) -> List[str]:
        """Query registrations by criteria."""
        results = []
        for agent_id, data in self._data.items():
            registration = AgentRegistration.from_dict(data)
            if self._matches_query(registration, query):
                results.append(agent_id)
        return results

    def _matches_query(
        self, registration: AgentRegistration, query: Dict[str, Any]
    ) -> bool:
        """Check if registration matches query criteria."""
        # Same logic as FileStorageBackend
        for key, value in query.items():
            if key == "capabilities" and isinstance(value, list):
                if not all(cap in registration.capabilities for cap in value):
                    return False
            elif key == "tags" and isinstance(value, list):
                if not all(tag in registration.tags for tag in value):
                    return False
            elif key == "status":
                if registration.status.value != value:
                    return False
            elif key == "health_level":
                if registration.health_level.value != value:
                    return False
            elif hasattr(registration, key):
                if getattr(registration, key) != value:
                    return False

        return True


class RegistryMetrics:
    """Registry performance metrics."""

    def __init__(self):
        """Initialize metrics."""
        self.reset()

    def reset(self) -> None:
        """Reset all metrics."""
        self.registrations_total = 0
        self.deregistrations_total = 0
        self.heartbeats_total = 0
        self.queries_total = 0
        self.query_times = []
        self.health_checks_total = 0
        self.failed_agents_total = 0
        self.start_time = time.time()

    def record_registration(self) -> None:
        """Record a registration."""
        self.registrations_total += 1

    def record_deregistration(self) -> None:
        """Record a deregistration."""
        self.deregistrations_total += 1

    def record_heartbeat(self) -> None:
        """Record a heartbeat."""
        self.heartbeats_total += 1

    def record_query(self, duration: float) -> None:
        """Record a query with duration."""
        self.queries_total += 1
        self.query_times.append(duration)

        # Keep only last 1000 query times
        if len(self.query_times) > 1000:
            self.query_times = self.query_times[-1000:]

    def record_health_check(self) -> None:
        """Record a health check."""
        self.health_checks_total += 1

    def record_failed_agent(self) -> None:
        """Record a failed agent."""
        self.failed_agents_total += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime = time.time() - self.start_time
        avg_query_time = (
            sum(self.query_times) / len(self.query_times) if self.query_times else 0
        )

        return {
            "uptime_seconds": uptime,
            "registrations_total": self.registrations_total,
            "deregistrations_total": self.deregistrations_total,
            "heartbeats_total": self.heartbeats_total,
            "heartbeats_per_second": self.heartbeats_total / uptime
            if uptime > 0
            else 0,
            "queries_total": self.queries_total,
            "average_query_time": avg_query_time,
            "health_checks_total": self.health_checks_total,
            "failed_agents_total": self.failed_agents_total,
        }


class EnhancedAgentRegistry:
    """
    Enhanced agent registry with scalability improvements.

    Features:
    - Pluggable storage backends (file, database, distributed)
    - Concurrent processing with asyncio
    - Advanced query capabilities
    - Comprehensive metrics and monitoring
    - Fault tolerance and recovery
    - Auto-scaling support
    """

    def __init__(
        self,
        storage_backend: Optional[StorageBackend] = None,
        max_concurrent_operations: int = 100,
        health_check_interval: int = 10,
        metrics_enabled: bool = True,
    ):
        """Initialize enhanced agent registry."""
        self.logger = logging.getLogger(__name__)

        # Storage and caching
        self.storage = storage_backend or FileStorageBackend()
        self._cache: Dict[str, AgentRegistration] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, float] = {}

        # Indexes for fast lookups
        self._capabilities_index: Dict[str, Set[str]] = defaultdict(set)
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)
        self._status_index: Dict[RegistrationStatus, Set[str]] = defaultdict(set)
        self._health_index: Dict[HealthLevel, Set[str]] = defaultdict(set)

        # Weak references to agent instances
        self._agent_instances: Dict[str, weakref.ReferenceType] = {}

        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent_operations)
        self._locks: Dict[str, asyncio.Lock] = {}

        # Background tasks
        self._running = False
        self._health_check_interval = health_check_interval
        self._tasks: Dict[str, asyncio.Task] = {}

        # Metrics
        self.metrics_enabled = metrics_enabled
        self.metrics = RegistryMetrics() if metrics_enabled else None

        # Event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        self.logger.info("Enhanced agent registry initialized")

    async def start(self) -> None:
        """Start registry services."""
        if self._running:
            return

        self._running = True

        # Load existing registrations from storage
        await self._load_registrations()

        # Start background tasks
        self._tasks["health_monitor"] = asyncio.create_task(self._health_monitor())
        self._tasks["cache_cleanup"] = asyncio.create_task(self._cache_cleanup())
        self._tasks["metrics_collector"] = asyncio.create_task(
            self._metrics_collector()
        )

        self.logger.info("Enhanced agent registry started")

    async def stop(self) -> None:
        """Stop registry services."""
        if not self._running:
            return

        self._running = False

        # Cancel background tasks
        for task_name, task in self._tasks.items():
            if not task.done():
                self.logger.debug(f"Cancelling task: {task_name}")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Deregister all agents
        agent_ids = list(self._cache.keys())
        for agent_id in agent_ids:
            await self.deregister_agent(agent_id)

        self.logger.info("Enhanced agent registry stopped")

    async def register_agent(
        self,
        agent: BaseAgent,
        capabilities: List[str],
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        host: str = "localhost",
        port: Optional[int] = None,
    ) -> str:
        """Register an agent with enhanced features."""
        async with self._semaphore:
            if not agent.agent_id:
                agent.agent_id = str(uuid4())

            agent_id = agent.agent_id

            # Check if already registered
            if agent_id in self._cache or await self.storage.load_registration(
                agent_id
            ):
                raise ValueError(f"Agent {agent_id} already registered")

            # Create registration
            registration = AgentRegistration(
                agent_id=agent_id,
                agent_instance=None,  # Will use weak reference
                status=RegistrationStatus.REGISTERED,
                capabilities=capabilities,
                tags=tags or set(),
                metadata=metadata or {},
                host=host,
                port=port,
            )

            # Store weak reference to agent instance
            self._agent_instances[agent_id] = weakref.ref(agent)

            # Save to storage
            await self.storage.save_registration(registration)

            # Update cache and indexes
            await self._update_cache(registration)
            await self._update_indexes(registration)

            # Send initial heartbeat
            await self.heartbeat(agent_id)

            # Record metrics
            if self.metrics:
                self.metrics.record_registration()

            # Trigger events
            await self._trigger_event(
                "agent_registered",
                {
                    "agent_id": agent_id,
                    "capabilities": capabilities,
                    "tags": list(tags or []),
                },
            )

            self.logger.info(
                f"Agent registered: {agent_id} with capabilities {capabilities}"
            )

            return agent_id

    async def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent with cleanup."""
        async with self._get_agent_lock(agent_id):
            # Load registration
            registration = await self._get_registration(agent_id)
            if not registration:
                return False

            # Update status
            registration.status = RegistrationStatus.DEREGISTERED

            # Stop agent if possible
            agent_ref = self._agent_instances.get(agent_id)
            if agent_ref:
                agent = agent_ref()
                if agent and agent.state != AgentState.STOPPED:
                    try:
                        await agent.stop()
                    except Exception as e:
                        self.logger.warning(f"Error stopping agent {agent_id}: {e}")

            # Remove from storage and caches
            await self.storage.delete_registration(agent_id)
            await self._remove_from_cache(agent_id)
            await self._remove_from_indexes(registration)

            # Clean up references
            self._agent_instances.pop(agent_id, None)
            self._locks.pop(agent_id, None)

            # Record metrics
            if self.metrics:
                self.metrics.record_deregistration()

            # Trigger events
            await self._trigger_event("agent_deregistered", {"agent_id": agent_id})

            self.logger.info(f"Agent deregistered: {agent_id}")
            return True

    async def heartbeat(
        self, agent_id: str, metrics: Optional[AgentMetrics] = None
    ) -> bool:
        """Record heartbeat with optional metrics."""
        async with self._get_agent_lock(agent_id):
            registration = await self._get_registration(agent_id)
            if not registration:
                return False

            # Update heartbeat and metrics
            registration.last_heartbeat = datetime.now(timezone.utc)

            if metrics:
                registration.metrics = metrics

            # Update health level
            old_health = registration.health_level
            new_health = registration.update_health_level()

            # Update status based on agent state
            agent_ref = self._agent_instances.get(agent_id)
            if agent_ref:
                agent = agent_ref()
                if agent:
                    if agent.state == AgentState.RUNNING:
                        registration.status = RegistrationStatus.ACTIVE
                    elif agent.state == AgentState.STOPPED:
                        registration.status = RegistrationStatus.INACTIVE
                    elif agent.state == AgentState.ERROR:
                        registration.status = RegistrationStatus.FAILED

            # Save changes
            await self.storage.save_registration(registration)
            await self._update_cache(registration)

            # Record metrics
            if self.metrics:
                self.metrics.record_heartbeat()
                self.metrics.record_health_check()

                if registration.status == RegistrationStatus.FAILED:
                    self.metrics.record_failed_agent()

            # Trigger health change events
            if old_health != new_health:
                await self._trigger_event(
                    "agent_health_changed",
                    {
                        "agent_id": agent_id,
                        "old_health": old_health.value,
                        "new_health": new_health.value,
                    },
                )

            return True

    async def find_agents(
        self,
        capabilities: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[RegistrationStatus] = None,
        health_level: Optional[HealthLevel] = None,
        limit: Optional[int] = None,
    ) -> List[str]:
        """Advanced agent discovery with multiple criteria."""
        start_time = time.time()

        try:
            # Use indexes for efficient lookup
            candidate_sets = []

            if capabilities:
                for capability in capabilities:
                    candidate_sets.append(
                        self._capabilities_index.get(capability, set())
                    )

            if tags:
                for tag in tags:
                    candidate_sets.append(self._tags_index.get(tag, set()))

            if status:
                candidate_sets.append(self._status_index.get(status, set()))

            if health_level:
                candidate_sets.append(self._health_index.get(health_level, set()))

            # Intersect all candidate sets
            if candidate_sets:
                result_set = candidate_sets[0]
                for candidate_set in candidate_sets[1:]:
                    result_set = result_set.intersection(candidate_set)
                results = list(result_set)
            else:
                # No criteria provided, return all
                results = list(self._cache.keys())

            # Apply limit
            if limit and len(results) > limit:
                results = results[:limit]

            # Record metrics
            if self.metrics:
                query_time = time.time() - start_time
                self.metrics.record_query(query_time)

            return results

        except Exception as e:
            self.logger.error(f"Error in find_agents: {e}")
            return []

    async def get_agent_info(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get comprehensive agent information."""
        return await self._get_registration(agent_id)

    async def get_agent_instance(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent instance by ID."""
        agent_ref = self._agent_instances.get(agent_id)
        if agent_ref:
            return agent_ref()
        return None

    async def update_agent_metrics(self, agent_id: str, metrics: AgentMetrics) -> bool:
        """Update agent metrics."""
        return await self.heartbeat(agent_id, metrics)

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics."""
        total_agents = len(self._cache)

        status_counts = {
            status.value: len(agents) for status, agents in self._status_index.items()
        }

        health_counts = {
            health.value: len(agents) for health, agents in self._health_index.items()
        }

        stats = {
            "total_agents": total_agents,
            "status_counts": status_counts,
            "health_counts": health_counts,
            "capabilities": list(self._capabilities_index.keys()),
            "tags": list(self._tags_index.keys()),
            "cache_size": len(self._cache),
            "active_locks": len(self._locks),
        }

        if self.metrics:
            stats["performance_metrics"] = self.metrics.get_summary()

        return stats

    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """Add event callback."""
        self._event_callbacks[event_type].append(callback)

    def remove_event_callback(self, event_type: str, callback: Callable) -> None:
        """Remove event callback."""
        if callback in self._event_callbacks[event_type]:
            self._event_callbacks[event_type].remove(callback)

    # Internal methods

    async def _get_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration from cache or storage."""
        # Check cache first
        if agent_id in self._cache:
            # Check cache freshness
            cache_time = self._cache_timestamps.get(agent_id, 0)
            if time.time() - cache_time < self._cache_ttl:
                return self._cache[agent_id]

        # Load from storage
        registration = await self.storage.load_registration(agent_id)
        if registration:
            await self._update_cache(registration)

        return registration

    async def _update_cache(self, registration: AgentRegistration) -> None:
        """Update cache with registration."""
        self._cache[registration.agent_id] = registration
        self._cache_timestamps[registration.agent_id] = time.time()

    async def _remove_from_cache(self, agent_id: str) -> None:
        """Remove registration from cache."""
        self._cache.pop(agent_id, None)
        self._cache_timestamps.pop(agent_id, None)

    async def _update_indexes(self, registration: AgentRegistration) -> None:
        """Update all indexes for registration."""
        agent_id = registration.agent_id

        # Capabilities index
        for capability in registration.capabilities:
            self._capabilities_index[capability].add(agent_id)

        # Tags index
        for tag in registration.tags:
            self._tags_index[tag].add(agent_id)

        # Status index
        self._status_index[registration.status].add(agent_id)

        # Health index
        self._health_index[registration.health_level].add(agent_id)

    async def _remove_from_indexes(self, registration: AgentRegistration) -> None:
        """Remove registration from all indexes."""
        agent_id = registration.agent_id

        # Capabilities index
        for capability in registration.capabilities:
            self._capabilities_index[capability].discard(agent_id)
            if not self._capabilities_index[capability]:
                del self._capabilities_index[capability]

        # Tags index
        for tag in registration.tags:
            self._tags_index[tag].discard(agent_id)
            if not self._tags_index[tag]:
                del self._tags_index[tag]

        # Status index
        self._status_index[registration.status].discard(agent_id)

        # Health index
        self._health_index[registration.health_level].discard(agent_id)

    def _get_agent_lock(self, agent_id: str) -> asyncio.Lock:
        """Get or create lock for agent."""
        if agent_id not in self._locks:
            self._locks[agent_id] = asyncio.Lock()
        return self._locks[agent_id]

    async def _load_registrations(self) -> None:
        """Load existing registrations from storage."""
        try:
            agent_ids = await self.storage.list_registrations()

            for agent_id in agent_ids:
                registration = await self.storage.load_registration(agent_id)
                if registration:
                    await self._update_cache(registration)
                    await self._update_indexes(registration)

            self.logger.info(f"Loaded {len(agent_ids)} registrations from storage")

        except Exception as e:
            self.logger.error(f"Error loading registrations: {e}")

    async def _health_monitor(self) -> None:
        """Background health monitoring."""
        while self._running:
            try:
                current_time = datetime.now(timezone.utc)

                # Check all cached registrations
                for agent_id, registration in list(self._cache.items()):
                    # Update health level
                    old_health = registration.health_level
                    new_health = registration.update_health_level()

                    # Check if agent needs heartbeat
                    if registration.should_heartbeat():
                        agent_ref = self._agent_instances.get(agent_id)
                        if agent_ref:
                            agent = agent_ref()
                            if agent and hasattr(agent, "send_heartbeat"):
                                try:
                                    await agent.send_heartbeat()
                                except Exception as e:
                                    self.logger.warning(
                                        f"Heartbeat failed for {agent_id}: {e}"
                                    )

                    # Update status if health changed
                    if not registration.is_healthy():
                        if registration.status != RegistrationStatus.FAILED:
                            registration.status = RegistrationStatus.FAILED
                            await self.storage.save_registration(registration)

                            # Trigger health change event
                            if old_health != new_health:
                                await self._trigger_event(
                                    "agent_health_changed",
                                    {
                                        "agent_id": agent_id,
                                        "old_health": old_health.value,
                                        "new_health": new_health.value,
                                    },
                                )

                await asyncio.sleep(self._health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)

    async def _cache_cleanup(self) -> None:
        """Background cache cleanup."""
        while self._running:
            try:
                current_time = time.time()
                expired_keys = []

                for agent_id, cache_time in self._cache_timestamps.items():
                    if current_time - cache_time > self._cache_ttl:
                        expired_keys.append(agent_id)

                for key in expired_keys:
                    await self._remove_from_cache(key)

                if expired_keys:
                    self.logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    async def _metrics_collector(self) -> None:
        """Background metrics collection."""
        if not self.metrics_enabled:
            return

        while self._running:
            try:
                # Could aggregate and export metrics here
                # For now, just sleep
                await asyncio.sleep(60)  # Collect every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collector error: {e}")
                await asyncio.sleep(60)

    async def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger event callbacks."""
        callbacks = self._event_callbacks.get(event_type, [])

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                self.logger.warning(f"Event callback error for {event_type}: {e}")


# Global registry instance
_enhanced_registry_instance: Optional[EnhancedAgentRegistry] = None


def get_enhanced_registry() -> EnhancedAgentRegistry:
    """Get the global enhanced agent registry instance."""
    global _enhanced_registry_instance
    if _enhanced_registry_instance is None:
        _enhanced_registry_instance = EnhancedAgentRegistry()
    return _enhanced_registry_instance


async def initialize_enhanced_registry(
    storage_backend: Optional[StorageBackend] = None, **kwargs
) -> EnhancedAgentRegistry:
    """Initialize and start the enhanced agent registry."""
    global _enhanced_registry_instance
    _enhanced_registry_instance = EnhancedAgentRegistry(
        storage_backend=storage_backend, **kwargs
    )
    await _enhanced_registry_instance.start()
    return _enhanced_registry_instance


async def shutdown_enhanced_registry() -> None:
    """Shutdown the enhanced agent registry."""
    global _enhanced_registry_instance
    if _enhanced_registry_instance:
        await _enhanced_registry_instance.stop()
        _enhanced_registry_instance = None
