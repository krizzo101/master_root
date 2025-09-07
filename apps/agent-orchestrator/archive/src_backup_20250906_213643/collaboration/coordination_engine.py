#!/usr/bin/env python3
"""
Dynamic Coordination Engine

Handles event-driven coordination, task handoffs, and collaborative workflows
between agents in real-time.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .message_bus import (
    CollaborationMessage,
    CollaborationMessageBus,
    MessageType,
    Priority,
)

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of coordination events"""

    TASK_HANDOFF = "task_handoff"
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    AGENT_DISCOVERY = "agent_discovery"
    PROGRESS_UPDATE = "progress_update"
    COMPLETION_NOTIFICATION = "completion_notification"
    ERROR_ESCALATION = "error_escalation"
    WORKSPACE_INVITATION = "workspace_invitation"
    CAPABILITY_ANNOUNCEMENT = "capability_announcement"


class CollaborationType(Enum):
    """Types of collaboration patterns"""

    PEER_REVIEW = "peer_review"
    PARALLEL_WORK = "parallel_work"
    SEQUENTIAL_HANDOFF = "sequential_handoff"
    EXPERT_CONSULTATION = "expert_consultation"
    BRAINSTORMING = "brainstorming"
    INTEGRATION_WORK = "integration_work"


class HandoffStatus(Enum):
    """Status of task handoffs"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CoordinationEvent:
    """Event structure for agent coordination"""

    event_type: EventType
    source_agent: str
    target_agent: Optional[str]  # None for broadcast
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    requires_response: bool = False
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3600  # Time to live in seconds

    def to_message(self) -> CollaborationMessage:
        """Convert to collaboration message"""
        return CollaborationMessage(
            message_type=MessageType.COORDINATION,
            from_agent=self.source_agent,
            to_agent=self.target_agent,
            payload={
                "event_type": self.event_type.value,
                "event_id": self.event_id,
                "payload": self.payload,
                "requires_response": self.requires_response,
                "correlation_id": self.correlation_id,
                "ttl": self.ttl,
            },
            priority=self.priority,
            correlation_id=self.correlation_id,
            requires_response=self.requires_response,
        )


@dataclass
class TaskRequirements:
    """Requirements for task execution"""

    required_capabilities: List[str]
    estimated_duration: Optional[int] = None  # minutes
    priority_level: Priority = Priority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class HandoffRequest:
    """Task handoff request"""

    handoff_id: str
    from_agent: str
    task_id: str
    task_description: str
    requirements: TaskRequirements
    current_progress: Dict[str, Any]
    status: HandoffStatus = HandoffStatus.PENDING
    target_agent: Optional[str] = None
    created_time: float = field(default_factory=time.time)
    response_deadline: Optional[float] = None


@dataclass
class Collaboration:
    """Active collaboration session"""

    collaboration_id: str
    collaboration_type: CollaborationType
    initiator: str
    participants: Set[str]
    workspace_id: Optional[str] = None
    status: str = "active"  # active, paused, completed, cancelled
    created_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Agent capability definition"""

    name: str
    description: str
    confidence_level: float  # 0.0 to 1.0
    max_concurrent_tasks: int = 1
    estimated_response_time: int = 60  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class DynamicCoordinationEngine:
    """
    Engine for dynamic agent coordination and collaboration

    Features:
    - Event-driven coordination
    - Dynamic task handoffs
    - Collaborative workflow management
    - Agent capability matching
    - Real-time progress tracking
    """

    def __init__(self, message_bus: CollaborationMessageBus):
        self.message_bus = message_bus

        # State management
        self.active_collaborations: Dict[str, Collaboration] = {}
        self.pending_handoffs: Dict[str, HandoffRequest] = {}
        self.agent_capabilities: Dict[str, Set[AgentCapability]] = {}
        self.agent_workload: Dict[str, int] = {}

        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False

        # Stats
        self.stats = {
            "events_processed": 0,
            "handoffs_initiated": 0,
            "handoffs_successful": 0,
            "collaborations_created": 0,
            "collaborations_completed": 0,
        }

        # Register default handlers
        self._register_default_handlers()

        logger.info("DynamicCoordinationEngine initialized")

    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler(EventType.TASK_HANDOFF, self._handle_task_handoff)
        self.register_handler(
            EventType.COLLABORATION_REQUEST, self._handle_collaboration_request
        )
        self.register_handler(EventType.AGENT_DISCOVERY, self._handle_agent_discovery)
        self.register_handler(
            EventType.CAPABILITY_ANNOUNCEMENT, self._handle_capability_announcement
        )
        self.register_handler(EventType.PROGRESS_UPDATE, self._handle_progress_update)

    def register_handler(self, event_type: EventType, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def start(self):
        """Start the coordination engine"""
        if self.running:
            return

        self.running = True

        # Start background tasks
        asyncio.create_task(self._monitor_handoff_timeouts())
        asyncio.create_task(self._cleanup_expired_events())

        logger.info("DynamicCoordinationEngine started")

    async def stop(self):
        """Stop the coordination engine"""
        self.running = False
        logger.info("DynamicCoordinationEngine stopped")

    async def process_event(self, event: CoordinationEvent) -> bool:
        """Process coordination event"""
        try:
            self.stats["events_processed"] += 1

            # Check if event has expired
            if time.time() - event.timestamp > event.ttl:
                logger.warning(f"Event {event.event_id} expired, skipping")
                return False

            # Get handlers for event type
            handlers = self.event_handlers.get(event.event_type, [])

            if not handlers:
                logger.warning(
                    f"No handlers registered for event type: {event.event_type}"
                )
                return False

            # Execute all handlers
            results = []
            for handler in handlers:
                try:
                    result = await handler(event)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {e}")
                    results.append(False)

            success = any(results)
            logger.debug(f"Event {event.event_id} processed: {success}")
            return success

        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")
            return False

    async def initiate_handoff(
        self,
        from_agent: str,
        task_id: str,
        task_description: str,
        requirements: TaskRequirements,
        current_progress: Dict[str, Any],
        target_agent: Optional[str] = None,
    ) -> str:
        """Initiate task handoff"""
        handoff_id = str(uuid.uuid4())

        handoff = HandoffRequest(
            handoff_id=handoff_id,
            from_agent=from_agent,
            task_id=task_id,
            task_description=task_description,
            requirements=requirements,
            current_progress=current_progress,
            target_agent=target_agent,
            response_deadline=time.time() + 300,  # 5 minutes
        )

        self.pending_handoffs[handoff_id] = handoff

        # Create handoff event
        event = CoordinationEvent(
            event_type=EventType.TASK_HANDOFF,
            source_agent=from_agent,
            target_agent=target_agent,
            payload={
                "handoff_id": handoff_id,
                "task_id": task_id,
                "task_description": task_description,
                "requirements": asdict(requirements),
                "current_progress": current_progress,
                "response_deadline": handoff.response_deadline,
            },
            requires_response=True,
            priority=requirements.priority_level,
        )

        # Send as message
        message = event.to_message()
        await self.message_bus.send_message(message)

        self.stats["handoffs_initiated"] += 1
        logger.info(f"Handoff {handoff_id} initiated for task {task_id}")

        return handoff_id

    async def respond_to_handoff(
        self,
        handoff_id: str,
        responding_agent: str,
        accepted: bool,
        estimated_completion: Optional[int] = None,
        additional_context: Dict[str, Any] = None,
    ) -> bool:
        """Respond to handoff request"""
        if handoff_id not in self.pending_handoffs:
            logger.error(f"Handoff {handoff_id} not found")
            return False

        handoff = self.pending_handoffs[handoff_id]

        if accepted:
            handoff.status = HandoffStatus.ACCEPTED
            handoff.target_agent = responding_agent
        else:
            handoff.status = HandoffStatus.REJECTED

        # Send response to original agent
        response_event = CoordinationEvent(
            event_type=EventType.TASK_HANDOFF,
            source_agent=responding_agent,
            target_agent=handoff.from_agent,
            payload={
                "handoff_id": handoff_id,
                "accepted": accepted,
                "estimated_completion": estimated_completion,
                "additional_context": additional_context or {},
                "response_type": "handoff_response",
            },
            correlation_id=handoff_id,
        )

        message = response_event.to_message()
        await self.message_bus.send_message(message)

        if accepted:
            self.stats["handoffs_successful"] += 1
            logger.info(f"Handoff {handoff_id} accepted by {responding_agent}")
        else:
            logger.info(f"Handoff {handoff_id} rejected by {responding_agent}")

        return True

    async def start_collaboration(
        self,
        initiator: str,
        collaboration_type: CollaborationType,
        participants: List[str],
        workspace_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Start new collaboration session"""
        collaboration_id = str(uuid.uuid4())

        collaboration = Collaboration(
            collaboration_id=collaboration_id,
            collaboration_type=collaboration_type,
            initiator=initiator,
            participants=set([initiator] + participants),
            workspace_id=workspace_id,
            metadata=metadata or {},
        )

        self.active_collaborations[collaboration_id] = collaboration

        # Send invitations to participants
        for participant in participants:
            event = CoordinationEvent(
                event_type=EventType.WORKSPACE_INVITATION,
                source_agent=initiator,
                target_agent=participant,
                payload={
                    "collaboration_id": collaboration_id,
                    "collaboration_type": collaboration_type.value,
                    "workspace_id": workspace_id,
                    "participants": list(collaboration.participants),
                    "metadata": metadata or {},
                },
                requires_response=True,
            )

            message = event.to_message()
            await self.message_bus.send_message(message)

        self.stats["collaborations_created"] += 1
        logger.info(
            f"Collaboration {collaboration_id} started with {len(participants)} participants"
        )

        return collaboration_id

    async def find_capable_agents(
        self, requirements: TaskRequirements, exclude_agents: List[str] = None
    ) -> List[Tuple[str, float]]:
        """Find agents capable of handling requirements"""
        exclude_agents = exclude_agents or []
        capable_agents = []

        for agent_id, capabilities in self.agent_capabilities.items():
            if agent_id in exclude_agents:
                continue

            # Check workload
            current_workload = self.agent_workload.get(agent_id, 0)
            if current_workload >= 5:  # Max concurrent tasks
                continue

            # Calculate capability match score
            score = self._calculate_capability_match(requirements, capabilities)
            if score > 0.5:  # Minimum threshold
                capable_agents.append((agent_id, score))

        # Sort by score (highest first)
        capable_agents.sort(key=lambda x: x[1], reverse=True)

        return capable_agents

    def _calculate_capability_match(
        self, requirements: TaskRequirements, capabilities: Set[AgentCapability]
    ) -> float:
        """Calculate how well capabilities match requirements"""
        if not requirements.required_capabilities:
            return 0.0

        capability_names = {cap.name for cap in capabilities}
        required_set = set(requirements.required_capabilities)

        # Basic intersection match
        intersection = capability_names.intersection(required_set)
        base_score = len(intersection) / len(required_set)

        # Weight by confidence levels
        confidence_boost = 0.0
        for cap in capabilities:
            if cap.name in intersection:
                confidence_boost += cap.confidence_level * 0.1

        return min(1.0, base_score + confidence_boost)

    # Event Handlers
    async def _handle_task_handoff(self, event: CoordinationEvent) -> bool:
        """Handle task handoff events"""
        payload = event.payload

        if payload.get("response_type") == "handoff_response":
            # Handle handoff response
            handoff_id = payload.get("handoff_id")
            if handoff_id in self.pending_handoffs:
                accepted = payload.get("accepted", False)
                if accepted:
                    self.pending_handoffs[handoff_id].status = HandoffStatus.ACCEPTED
                else:
                    self.pending_handoffs[handoff_id].status = HandoffStatus.REJECTED
                logger.info(
                    f"Handoff {handoff_id} response processed: {'accepted' if accepted else 'rejected'}"
                )
            return True
        else:
            # Handle new handoff request
            requirements = TaskRequirements(**payload.get("requirements", {}))

            # Find capable agents if no specific target
            if not event.target_agent:
                capable_agents = await self.find_capable_agents(
                    requirements, exclude_agents=[event.source_agent]
                )

                if capable_agents:
                    # Send to top candidate
                    best_agent = capable_agents[0][0]
                    event.target_agent = best_agent
                    message = event.to_message()
                    await self.message_bus.send_message(message)
                    logger.info(
                        f"Handoff routed to {best_agent} (score: {capable_agents[0][1]:.2f})"
                    )
                else:
                    logger.warning("No capable agents found for handoff")
                    return False

            return True

    async def _handle_collaboration_request(self, event: CoordinationEvent) -> bool:
        """Handle collaboration requests"""
        payload = event.payload
        collaboration_type = CollaborationType(
            payload.get("collaboration_type", "peer_review")
        )
        participants = payload.get("participants", [])

        # Start collaboration
        collaboration_id = await self.start_collaboration(
            event.source_agent,
            collaboration_type,
            participants,
            workspace_id=payload.get("workspace_id"),
            metadata=payload.get("metadata", {}),
        )

        return collaboration_id is not None

    async def _handle_agent_discovery(self, event: CoordinationEvent) -> bool:
        """Handle agent discovery events"""
        # Respond with our known agents and capabilities
        discovery_response = CoordinationEvent(
            event_type=EventType.AGENT_DISCOVERY,
            source_agent="coordination_engine",
            target_agent=event.source_agent,
            payload={
                "known_agents": list(self.agent_capabilities.keys()),
                "capabilities_summary": {
                    agent_id: [cap.name for cap in caps]
                    for agent_id, caps in self.agent_capabilities.items()
                },
            },
            correlation_id=event.event_id,
        )

        message = discovery_response.to_message()
        await self.message_bus.send_message(message)

        return True

    async def _handle_capability_announcement(self, event: CoordinationEvent) -> bool:
        """Handle agent capability announcements"""
        agent_id = event.source_agent
        capabilities_data = event.payload.get("capabilities", [])

        capabilities = set()
        for cap_data in capabilities_data:
            capability = AgentCapability(**cap_data)
            capabilities.add(capability)

        self.agent_capabilities[agent_id] = capabilities
        logger.info(
            f"Updated capabilities for {agent_id}: {[cap.name for cap in capabilities]}"
        )

        return True

    async def _handle_progress_update(self, event: CoordinationEvent) -> bool:
        """Handle progress updates"""
        # Update workload tracking
        agent_id = event.source_agent
        payload = event.payload

        if payload.get("task_completed"):
            self.agent_workload[agent_id] = max(
                0, self.agent_workload.get(agent_id, 0) - 1
            )
        elif payload.get("task_started"):
            self.agent_workload[agent_id] = self.agent_workload.get(agent_id, 0) + 1

        # Forward to interested parties (e.g., collaboration participants)
        task_id = payload.get("task_id")
        if task_id:
            for collaboration in self.active_collaborations.values():
                if agent_id in collaboration.participants:
                    # Broadcast to other participants
                    for participant in collaboration.participants:
                        if participant != agent_id:
                            forward_event = CoordinationEvent(
                                event_type=EventType.PROGRESS_UPDATE,
                                source_agent=agent_id,
                                target_agent=participant,
                                payload=payload,
                            )
                            message = forward_event.to_message()
                            await self.message_bus.send_message(message)

        return True

    # Background Tasks
    async def _monitor_handoff_timeouts(self):
        """Monitor handoff timeouts"""
        while self.running:
            try:
                current_time = time.time()
                expired_handoffs = []

                for handoff_id, handoff in self.pending_handoffs.items():
                    if (
                        handoff.response_deadline
                        and current_time > handoff.response_deadline
                        and handoff.status == HandoffStatus.PENDING
                    ):
                        expired_handoffs.append(handoff_id)

                for handoff_id in expired_handoffs:
                    handoff = self.pending_handoffs[handoff_id]
                    handoff.status = HandoffStatus.FAILED

                    # Notify original agent
                    timeout_event = CoordinationEvent(
                        event_type=EventType.ERROR_ESCALATION,
                        source_agent="coordination_engine",
                        target_agent=handoff.from_agent,
                        payload={
                            "error_type": "handoff_timeout",
                            "handoff_id": handoff_id,
                            "message": "Handoff request timed out",
                        },
                    )

                    message = timeout_event.to_message()
                    await self.message_bus.send_message(message)

                    logger.warning(f"Handoff {handoff_id} timed out")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in handoff timeout monitor: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_events(self):
        """Clean up expired events and old state"""
        while self.running:
            try:
                current_time = time.time()

                # Clean up old handoffs
                expired_handoffs = [
                    hid
                    for hid, handoff in self.pending_handoffs.items()
                    if current_time - handoff.created_time > 3600  # 1 hour
                ]

                for handoff_id in expired_handoffs:
                    del self.pending_handoffs[handoff_id]

                logger.debug(f"Cleaned up {len(expired_handoffs)} expired handoffs")

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(1800)

    def get_stats(self) -> Dict[str, Any]:
        """Get coordination engine statistics"""
        return {
            **self.stats,
            "running": self.running,
            "active_collaborations": len(self.active_collaborations),
            "pending_handoffs": len(self.pending_handoffs),
            "registered_agents": len(self.agent_capabilities),
            "total_agent_workload": sum(self.agent_workload.values()),
        }
