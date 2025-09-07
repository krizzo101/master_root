#!/usr/bin/env python3
"""
Collaboration Orchestrator

Main orchestrator that integrates all collaboration components to enable
real-time multi-agent collaboration while maintaining backwards compatibility.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..generic_orchestrator import AgentTask, GenericOrchestrator
from ..practical_orchestrator import PracticalAgentTask, QualityReport
from .coordination_engine import (
    AgentCapability,
    CollaborationType,
    CoordinationEvent,
    DynamicCoordinationEngine,
    EventType,
    TaskRequirements,
)
from .message_bus import CollaborationMessage, CollaborationMessageBus, MessageType
from .workspace_manager import SharedWorkspaceManager

logger = logging.getLogger(__name__)


@dataclass
class CollaborativeTask(PracticalAgentTask):
    """Task with collaboration capabilities"""

    # Collaboration features
    collaboration_enabled: bool = True
    allow_handoffs: bool = True
    allow_peer_review: bool = True
    collaboration_type: Optional[CollaborationType] = None

    # Required capabilities for task execution
    required_capabilities: List[str] = field(default_factory=list)
    preferred_agents: List[str] = field(default_factory=list)
    max_collaborators: int = 3

    # Workspace settings
    shared_workspace: bool = False
    workspace_permissions: Dict[str, str] = field(
        default_factory=dict
    )  # agent_id -> permission level

    def to_task_requirements(self) -> TaskRequirements:
        """Convert to TaskRequirements for coordination engine"""
        return TaskRequirements(
            required_capabilities=self.required_capabilities,
            estimated_duration=self.context.get("estimated_duration"),
            dependencies=self.dependencies,
            context_data=self.context,
        )


@dataclass
class CollaborationSession:
    """Active collaboration session"""

    session_id: str
    task_ids: Set[str]
    participants: Set[str]
    workspace_id: Optional[str]
    status: str = "active"
    created_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CollaborationOrchestrator(GenericOrchestrator):
    """
    Enhanced orchestrator with full collaboration support

    Features:
    - Real-time agent-to-agent communication
    - Dynamic task handoffs
    - Shared workspaces for collaborative editing
    - Event-driven coordination
    - Backwards compatible with existing workflows
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        enable_collaboration: bool = True,
        redis_url: Optional[str] = None,
        websocket_port: int = 8767,
        **kwargs,
    ):
        super().__init__(output_dir, max_parallel, tokens, **kwargs)

        self.enable_collaboration = enable_collaboration
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}

        # Initialize collaboration components
        if enable_collaboration:
            self.message_bus = CollaborationMessageBus(
                redis_url=redis_url,
                websocket_port=websocket_port,
                fallback_dir=output_dir / "collaboration_messages",
            )

            self.coordination_engine = DynamicCoordinationEngine(self.message_bus)

            self.workspace_manager = SharedWorkspaceManager(
                workspace_root=output_dir / "shared_workspaces"
            )
        else:
            # Use existing simple message bus for backwards compatibility
            self.message_bus = self.message_bus  # Keep existing MessageBus
            self.coordination_engine = None
            self.workspace_manager = None

        # Enhanced stats tracking
        self.collaboration_stats = {
            "collaborative_tasks": 0,
            "successful_handoffs": 0,
            "active_collaborations": 0,
            "messages_sent": 0,
            "shared_workspaces_created": 0,
        }

        logger.info(
            f"CollaborationOrchestrator initialized (collaboration: {enable_collaboration})"
        )

    async def start_collaboration_services(self) -> None:
        """Start collaboration services"""
        if not self.enable_collaboration:
            logger.info("Collaboration disabled, skipping service startup")
            return

        logger.info("Starting collaboration services...")

        try:
            # Start message bus
            await self.message_bus.start()

            # Start coordination engine
            await self.coordination_engine.start()

            # Start workspace manager
            await self.workspace_manager.start()

            logger.info("Collaboration services started successfully")

        except Exception as e:
            logger.error(f"Failed to start collaboration services: {e}")
            raise

    async def stop_collaboration_services(self) -> None:
        """Stop collaboration services"""
        if not self.enable_collaboration:
            return

        logger.info("Stopping collaboration services...")

        try:
            if self.coordination_engine:
                await self.coordination_engine.stop()

            if self.workspace_manager:
                await self.workspace_manager.stop()

            if self.message_bus:
                await self.message_bus.stop()

            logger.info("Collaboration services stopped")

        except Exception as e:
            logger.error(f"Error stopping collaboration services: {e}")

    async def execute_batch(
        self, tasks: List[CollaborativeTask], enable_progress_monitoring: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute batch of collaborative tasks"""

        # Start collaboration services if enabled
        if self.enable_collaboration:
            await self.start_collaboration_services()

        try:
            # Pre-process tasks for collaboration
            processed_tasks = await self._preprocess_collaborative_tasks(tasks)

            # Execute using parent class method
            results = await super().execute_batch(processed_tasks)

            # Post-process results with collaboration data
            enhanced_results = await self._postprocess_collaborative_results(results)

            return enhanced_results

        finally:
            # Stop collaboration services
            if self.enable_collaboration:
                await self.stop_collaboration_services()

    async def _preprocess_collaborative_tasks(
        self, tasks: List[CollaborativeTask]
    ) -> List[CollaborativeTask]:
        """Pre-process tasks for collaboration features"""

        processed_tasks = []

        for task in tasks:
            if not task.collaboration_enabled or not self.enable_collaboration:
                # Treat as regular task
                processed_tasks.append(task)
                continue

            self.collaboration_stats["collaborative_tasks"] += 1

            # Create shared workspace if requested
            if task.shared_workspace:
                workspace_id = await self._create_shared_workspace(task)
                task.context["workspace_id"] = workspace_id
                self.collaboration_stats["shared_workspaces_created"] += 1

            # Register task with coordination engine
            if self.coordination_engine:
                await self._register_task_with_coordination(task)

            processed_tasks.append(task)

        return processed_tasks

    async def _create_shared_workspace(self, task: CollaborativeTask) -> str:
        """Create shared workspace for collaborative task"""
        workspace_config = {
            "task_id": task.task_id,
            "permissions": task.workspace_permissions,
            "max_collaborators": task.max_collaborators,
        }

        workspace = await self.workspace_manager.create_workspace(
            workspace_id=f"task_{task.task_id}",
            initiating_agent=f"orchestrator_{task.task_id}",
            config=workspace_config,
        )

        logger.info(
            f"Created shared workspace {workspace.workspace_id} for task {task.task_id}"
        )
        return workspace.workspace_id

    async def _register_task_with_coordination(self, task: CollaborativeTask) -> None:
        """Register task with coordination engine for potential handoffs"""
        # Announce task capabilities required
        if task.required_capabilities:
            capability_event = CoordinationEvent(
                event_type=EventType.CAPABILITY_ANNOUNCEMENT,
                source_agent=f"orchestrator_{task.task_id}",
                target_agent=None,  # Broadcast
                payload={
                    "task_id": task.task_id,
                    "required_capabilities": task.required_capabilities,
                    "collaboration_type": task.collaboration_type.value
                    if task.collaboration_type
                    else None,
                    "allows_handoffs": task.allow_handoffs,
                    "allows_peer_review": task.allow_peer_review,
                },
            )

            await self.coordination_engine.process_event(capability_event)

    async def _postprocess_collaborative_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add collaboration metadata to results"""

        enhanced_results = []

        for result in results:
            if not self.enable_collaboration:
                enhanced_results.append(result)
                continue

            # Add collaboration stats
            result["collaboration"] = {
                "messages_sent": self.message_bus.get_stats().get("messages_sent", 0),
                "collaboration_sessions": len(self.collaboration_sessions),
                "workspace_used": "workspace_id" in result.get("context", {}),
                "handoffs_attempted": 0,  # TODO: Track from coordination engine
                "peer_reviews_conducted": 0,  # TODO: Track from collaboration sessions
            }

            enhanced_results.append(result)

        return enhanced_results

    async def initiate_collaboration(
        self,
        initiator_task_id: str,
        collaboration_type: CollaborationType,
        participant_agents: List[str],
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Initiate collaboration between agents"""

        if not self.enable_collaboration:
            raise ValueError("Collaboration not enabled")

        collaboration_id = await self.coordination_engine.start_collaboration(
            initiator=f"task_{initiator_task_id}",
            collaboration_type=collaboration_type,
            participants=participant_agents,
            metadata=metadata,
        )

        # Track collaboration session
        session = CollaborationSession(
            session_id=collaboration_id,
            task_ids={initiator_task_id},
            participants=set(participant_agents + [f"task_{initiator_task_id}"]),
            metadata=metadata or {},
        )

        self.collaboration_sessions[collaboration_id] = session
        self.collaboration_stats["active_collaborations"] += 1

        logger.info(
            f"Initiated collaboration {collaboration_id} with {len(participant_agents)} agents"
        )

        return collaboration_id

    async def request_task_handoff(
        self,
        task_id: str,
        reason: str,
        requirements: TaskRequirements,
        current_progress: Dict[str, Any],
        preferred_agent: Optional[str] = None,
    ) -> Optional[str]:
        """Request handoff of task to another agent"""

        if not self.enable_collaboration:
            logger.warning("Collaboration not enabled, handoff request ignored")
            return None

        handoff_id = await self.coordination_engine.initiate_handoff(
            from_agent=f"task_{task_id}",
            task_id=task_id,
            task_description=reason,
            requirements=requirements,
            current_progress=current_progress,
            target_agent=preferred_agent,
        )

        self.collaboration_stats["successful_handoffs"] += 1
        logger.info(f"Requested handoff {handoff_id} for task {task_id}")

        return handoff_id

    async def broadcast_progress_update(
        self,
        task_id: str,
        progress_data: Dict[str, Any],
        notify_collaborators: bool = True,
    ) -> None:
        """Broadcast progress update to interested parties"""

        if not self.enable_collaboration:
            return

        update_event = CoordinationEvent(
            event_type=EventType.PROGRESS_UPDATE,
            source_agent=f"task_{task_id}",
            target_agent=None,  # Broadcast
            payload={
                "task_id": task_id,
                "progress_data": progress_data,
                "timestamp": time.time(),
            },
        )

        await self.coordination_engine.process_event(update_event)
        self.collaboration_stats["messages_sent"] += 1

    def create_collaborative_task(
        self,
        task_id: str,
        task_type: str,
        prompt: str,
        required_capabilities: List[str] = None,
        collaboration_type: CollaborationType = None,
        enable_handoffs: bool = True,
        enable_peer_review: bool = False,
        shared_workspace: bool = False,
        **kwargs,
    ) -> CollaborativeTask:
        """Factory method for creating collaborative tasks"""

        return CollaborativeTask(
            task_id=task_id,
            task_type=task_type,
            prompt=prompt,
            required_capabilities=required_capabilities or [],
            collaboration_type=collaboration_type,
            allow_handoffs=enable_handoffs,
            allow_peer_review=enable_peer_review,
            shared_workspace=shared_workspace,
            **kwargs,
        )

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get comprehensive collaboration statistics"""
        base_stats = {
            "collaboration_enabled": self.enable_collaboration,
            **self.collaboration_stats,
        }

        if self.enable_collaboration:
            base_stats.update(
                {
                    "message_bus": self.message_bus.get_stats()
                    if self.message_bus
                    else {},
                    "coordination_engine": self.coordination_engine.get_stats()
                    if self.coordination_engine
                    else {},
                    "workspace_manager": self.workspace_manager.get_stats()
                    if self.workspace_manager
                    else {},
                    "active_sessions": len(self.collaboration_sessions),
                }
            )

        return base_stats

    async def generate_collaboration_report(self) -> Dict[str, Any]:
        """Generate comprehensive collaboration report"""
        stats = self.get_collaboration_stats()

        report = {
            "timestamp": time.time(),
            "orchestrator_type": "CollaborationOrchestrator",
            "collaboration_summary": stats,
            "sessions": [
                {
                    "session_id": session.session_id,
                    "task_ids": list(session.task_ids),
                    "participants": list(session.participants),
                    "status": session.status,
                    "duration": time.time() - session.created_time,
                }
                for session in self.collaboration_sessions.values()
            ],
        }

        return report


# Factory function for easy instantiation
async def create_collaboration_orchestrator(
    output_dir: Path,
    max_parallel: int = 10,
    enable_collaboration: bool = True,
    redis_url: Optional[str] = None,
    **kwargs,
) -> CollaborationOrchestrator:
    """Create and initialize collaboration orchestrator"""

    orchestrator = CollaborationOrchestrator(
        output_dir=output_dir,
        max_parallel=max_parallel,
        enable_collaboration=enable_collaboration,
        redis_url=redis_url,
        **kwargs,
    )

    return orchestrator


# Example usage demonstration
async def collaboration_example():
    """Example demonstrating collaboration features"""

    # Create orchestrator with collaboration enabled
    orchestrator = await create_collaboration_orchestrator(
        output_dir=Path("./collaboration_demo"),
        max_parallel=5,
        enable_collaboration=True,
        redis_url="redis://localhost:6379/0",  # Optional
    )

    # Create collaborative tasks
    tasks = [
        orchestrator.create_collaborative_task(
            task_id="research_phase",
            task_type="research-specialist",
            prompt="Research best practices for microservices architecture",
            required_capabilities=["research", "architecture", "web"],
            collaboration_type=CollaborationType.PARALLEL_WORK,
            shared_workspace=True,
        ),
        orchestrator.create_collaborative_task(
            task_id="design_phase",
            task_type="system-architect",
            prompt="Design microservices architecture based on research",
            required_capabilities=["architecture", "design", "systems"],
            collaboration_type=CollaborationType.SEQUENTIAL_HANDOFF,
            enable_peer_review=True,
            dependencies=["research_phase"],
        ),
        orchestrator.create_collaborative_task(
            task_id="implementation",
            task_type="development-specialist",
            prompt="Implement core microservices components",
            required_capabilities=["development", "microservices", "api"],
            collaboration_type=CollaborationType.PEER_REVIEW,
            enable_handoffs=True,
            dependencies=["design_phase"],
        ),
    ]

    # Execute collaborative workflow
    results = await orchestrator.execute_batch(tasks)

    # Generate collaboration report
    report = await orchestrator.generate_collaboration_report()

    print(f"Executed {len(tasks)} collaborative tasks")
    print(f"Collaboration sessions: {len(report['sessions'])}")
    print(f"Messages sent: {report['collaboration_summary']['messages_sent']}")

    return results


if __name__ == "__main__":
    # Run example
    asyncio.run(collaboration_example())
