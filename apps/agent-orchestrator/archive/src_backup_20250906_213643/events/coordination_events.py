"""
Coordination Events

Specialized event handling for agent coordination, task handoffs,
and collaborative work management.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .event_bus import EventBus, get_global_event_bus
from .event_types import (
    BaseEvent,
    CoordinationEvent,
    EventType,
    Priority,
    create_help_request_event,
    create_task_handoff_event,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents an agent's capabilities"""

    skill_name: str
    proficiency_level: float  # 0.0 to 1.0
    availability: bool = True
    max_concurrent_tasks: int = 3
    current_task_count: int = 0


@dataclass
class Agent:
    """Represents an agent in the coordination system"""

    agent_id: str
    name: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: str = "available"  # available, busy, offline
    current_tasks: List[str] = field(default_factory=list)
    last_heartbeat: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_available_for_task(self, required_skills: List[str] = None) -> bool:
        """Check if agent is available and has required skills"""
        if self.status != "available":
            return False

        # Check capacity
        total_capacity = sum(cap.max_concurrent_tasks for cap in self.capabilities)
        if len(self.current_tasks) >= total_capacity:
            return False

        # Check skills if specified
        if required_skills:
            agent_skills = {
                cap.skill_name for cap in self.capabilities if cap.availability
            }
            return bool(set(required_skills) & agent_skills)

        return True

    def get_skill_proficiency(self, skill_name: str) -> float:
        """Get proficiency level for a specific skill"""
        for cap in self.capabilities:
            if cap.skill_name == skill_name and cap.availability:
                return cap.proficiency_level
        return 0.0


class CoordinationManager:
    """Manages agent coordination, task assignments, and collaboration"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_global_event_bus()
        self.agents: Dict[str, Agent] = {}
        self.pending_requests: Dict[str, CoordinationEvent] = {}
        self.active_handoffs: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()

        # Subscribe to coordination events
        self.event_bus.subscribe(
            self._handle_coordination_event,
            event_types=[
                EventType.TASK_HANDOFF,
                EventType.HELP_REQUEST,
                EventType.AGENT_AVAILABLE,
                EventType.WORK_REQUEST,
                EventType.RESOURCE_REQUEST,
            ],
        )

        # Subscribe to system events for agent management
        self.event_bus.subscribe(
            self._handle_system_event,
            event_types=[EventType.AGENT_JOINED, EventType.AGENT_LEFT],
        )

        logger.info("CoordinationManager initialized")

    async def register_agent(
        self, agent_id: str, name: str, capabilities: List[AgentCapability]
    ) -> None:
        """Register an agent with the coordination system"""
        async with self.lock:
            agent = Agent(
                agent_id=agent_id,
                name=name,
                capabilities=capabilities,
                last_heartbeat=asyncio.get_event_loop().time(),
            )
            self.agents[agent_id] = agent

        # Publish agent joined event
        await self.event_bus.publish(
            BaseEvent(
                event_type=EventType.AGENT_JOINED,
                source_agent_id=agent_id,
                metadata={
                    "agent_name": name,
                    "capabilities": [cap.skill_name for cap in capabilities],
                },
            )
        )

        logger.info(
            f"Agent {agent_id} ({name}) registered with capabilities: "
            f"{[cap.skill_name for cap in capabilities]}"
        )

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the coordination system"""
        async with self.lock:
            if agent_id in self.agents:
                agent = self.agents.pop(agent_id)

                # Publish agent left event
                await self.event_bus.publish(
                    BaseEvent(
                        event_type=EventType.AGENT_LEFT,
                        source_agent_id=agent_id,
                        metadata={"agent_name": agent.name},
                    )
                )

                logger.info(f"Agent {agent_id} ({agent.name}) unregistered")

    async def request_task_handoff(
        self,
        source_agent_id: str,
        task_id: str,
        task_data: Dict[str, Any],
        required_skills: List[str] = None,
        preferred_agent: Optional[str] = None,
        context: str = "",
    ) -> Optional[str]:
        """Request a task handoff to another agent"""

        # Find suitable agent
        target_agent_id = await self._find_suitable_agent(
            required_skills, preferred_agent, source_agent_id
        )

        if not target_agent_id:
            logger.warning(
                f"No suitable agent found for task handoff from {source_agent_id}"
            )
            return None

        # Create and publish handoff event
        handoff_event = create_task_handoff_event(
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            task_id=task_id,
            task_data=task_data,
            context=context,
        )

        # Track the handoff
        async with self.lock:
            self.active_handoffs[handoff_event.event_id] = {
                "source_agent": source_agent_id,
                "target_agent": target_agent_id,
                "task_id": task_id,
                "timestamp": handoff_event.timestamp,
                "status": "pending",
            }

        await self.event_bus.publish(handoff_event)

        logger.info(
            f"Task {task_id} handoff requested from {source_agent_id} "
            f"to {target_agent_id}"
        )

        return target_agent_id

    async def request_help(
        self,
        source_agent_id: str,
        problem_description: str,
        required_skills: List[str] = None,
        urgency: Priority = Priority.NORMAL,
    ) -> List[str]:
        """Request help from other agents"""

        # Find available agents with required skills
        suitable_agents = await self._find_all_suitable_agents(
            required_skills, exclude_agent=source_agent_id
        )

        if not suitable_agents:
            logger.warning(f"No suitable agents found to help {source_agent_id}")
            return []

        # Create and publish help request
        help_event = create_help_request_event(
            source_agent_id=source_agent_id,
            problem_description=problem_description,
            required_skills=required_skills,
            urgency=urgency,
        )

        # Set target agents
        help_event.target_agent_ids = suitable_agents

        # Track the request
        async with self.lock:
            self.pending_requests[help_event.event_id] = help_event

        await self.event_bus.publish(help_event)

        logger.info(
            f"Help requested by {source_agent_id}, notifying {len(suitable_agents)} agents"
        )

        return suitable_agents

    async def update_agent_status(
        self, agent_id: str, status: str, current_tasks: List[str] = None
    ) -> None:
        """Update an agent's status and current tasks"""
        async with self.lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.status = status
                if current_tasks is not None:
                    agent.current_tasks = current_tasks
                agent.last_heartbeat = asyncio.get_event_loop().time()

                logger.debug(f"Agent {agent_id} status updated to {status}")

    async def _find_suitable_agent(
        self,
        required_skills: List[str] = None,
        preferred_agent: Optional[str] = None,
        exclude_agent: Optional[str] = None,
    ) -> Optional[str]:
        """Find the best suitable agent for a task"""

        async with self.lock:
            # First try preferred agent if specified
            if preferred_agent and preferred_agent in self.agents:
                agent = self.agents[preferred_agent]
                if agent.agent_id != exclude_agent and agent.is_available_for_task(
                    required_skills
                ):
                    return preferred_agent

            # Find all suitable agents and pick the best one
            suitable_agents = []
            for agent_id, agent in self.agents.items():
                if agent_id != exclude_agent and agent.is_available_for_task(
                    required_skills
                ):
                    # Calculate fitness score
                    score = self._calculate_agent_fitness(agent, required_skills)
                    suitable_agents.append((agent_id, score))

            if suitable_agents:
                # Sort by fitness score (higher is better)
                suitable_agents.sort(key=lambda x: x[1], reverse=True)
                return suitable_agents[0][0]

        return None

    async def _find_all_suitable_agents(
        self, required_skills: List[str] = None, exclude_agent: Optional[str] = None
    ) -> List[str]:
        """Find all suitable agents for a task"""

        suitable_agents = []
        async with self.lock:
            for agent_id, agent in self.agents.items():
                if agent_id != exclude_agent and agent.is_available_for_task(
                    required_skills
                ):
                    suitable_agents.append(agent_id)

        return suitable_agents

    def _calculate_agent_fitness(
        self, agent: Agent, required_skills: List[str] = None
    ) -> float:
        """Calculate fitness score for agent selection"""
        score = 0.0

        # Base availability score (higher if less busy)
        total_capacity = sum(cap.max_concurrent_tasks for cap in agent.capabilities)
        if total_capacity > 0:
            availability_score = 1.0 - (len(agent.current_tasks) / total_capacity)
            score += availability_score * 0.5

        # Skill match score
        if required_skills:
            skill_scores = []
            for skill in required_skills:
                proficiency = agent.get_skill_proficiency(skill)
                skill_scores.append(proficiency)

            if skill_scores:
                avg_proficiency = sum(skill_scores) / len(skill_scores)
                score += avg_proficiency * 0.5
        else:
            score += 0.5  # No specific skills required

        return score

    async def _handle_coordination_event(self, event: BaseEvent) -> None:
        """Handle coordination events"""
        if not isinstance(event, CoordinationEvent):
            return

        try:
            if event.event_type == EventType.TASK_HANDOFF:
                await self._handle_task_handoff(event)
            elif event.event_type == EventType.HELP_REQUEST:
                await self._handle_help_request(event)
            elif event.event_type == EventType.AGENT_AVAILABLE:
                await self._handle_agent_available(event)
            elif event.event_type == EventType.WORK_REQUEST:
                await self._handle_work_request(event)
            elif event.event_type == EventType.RESOURCE_REQUEST:
                await self._handle_resource_request(event)

        except Exception as e:
            logger.error(f"Error handling coordination event {event.event_id}: {e}")

    async def _handle_system_event(self, event: BaseEvent) -> None:
        """Handle system events"""
        try:
            if event.event_type == EventType.AGENT_JOINED:
                logger.info(f"Agent joined: {event.source_agent_id}")
            elif event.event_type == EventType.AGENT_LEFT:
                await self._handle_agent_departure(event.source_agent_id)

        except Exception as e:
            logger.error(f"Error handling system event {event.event_id}: {e}")

    async def _handle_task_handoff(self, event: CoordinationEvent) -> None:
        """Handle task handoff event"""
        handoff_id = event.event_id

        async with self.lock:
            if handoff_id in self.active_handoffs:
                handoff = self.active_handoffs[handoff_id]
                handoff["status"] = "acknowledged"

                # Update agent task assignments
                source_agent = handoff["source_agent"]
                target_agent = handoff["target_agent"]
                task_id = handoff["task_id"]

                if source_agent in self.agents:
                    if task_id in self.agents[source_agent].current_tasks:
                        self.agents[source_agent].current_tasks.remove(task_id)

                if target_agent in self.agents:
                    self.agents[target_agent].current_tasks.append(task_id)

                logger.info(f"Task handoff {handoff_id} processed successfully")

    async def _handle_help_request(self, event: CoordinationEvent) -> None:
        """Handle help request event"""
        logger.info(f"Processing help request from {event.source_agent_id}")

    async def _handle_agent_available(self, event: CoordinationEvent) -> None:
        """Handle agent availability notification"""
        await self.update_agent_status(event.source_agent_id, "available")

    async def _handle_work_request(self, event: CoordinationEvent) -> None:
        """Handle work request event"""
        logger.info(f"Processing work request from {event.source_agent_id}")

    async def _handle_resource_request(self, event: CoordinationEvent) -> None:
        """Handle resource request event"""
        logger.info(f"Processing resource request from {event.source_agent_id}")

    async def _handle_agent_departure(self, agent_id: str) -> None:
        """Handle agent departure and reassign their tasks"""
        async with self.lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]

                # Reassign their current tasks
                for task_id in agent.current_tasks:
                    logger.info(
                        f"Reassigning task {task_id} from departed agent {agent_id}"
                    )

                    # Find another suitable agent
                    suitable_agent = await self._find_suitable_agent(
                        exclude_agent=agent_id
                    )
                    if suitable_agent:
                        # Create handoff event
                        handoff_event = create_task_handoff_event(
                            source_agent_id=agent_id,
                            target_agent_id=suitable_agent,
                            task_id=task_id,
                            task_data={"reason": "agent_departure"},
                            context="Task reassignment due to agent departure",
                        )
                        await self.event_bus.publish(handoff_event)

    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination system statistics"""
        async with self.lock:
            return {
                "total_agents": len(self.agents),
                "available_agents": len(
                    [a for a in self.agents.values() if a.status == "available"]
                ),
                "active_handoffs": len(self.active_handoffs),
                "pending_requests": len(self.pending_requests),
                "agents": {
                    agent_id: {
                        "name": agent.name,
                        "status": agent.status,
                        "current_tasks": len(agent.current_tasks),
                        "capabilities": [cap.skill_name for cap in agent.capabilities],
                    }
                    for agent_id, agent in self.agents.items()
                },
            }
