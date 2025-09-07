#!/usr/bin/env python3
"""
Collaborative Agent Orchestrator
Extends GenericOrchestrator to support real-time agent collaboration
"""

import asyncio
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from generic_orchestrator import (
    AgentTask,
    DependencyManager,
    GenericOrchestrator,
    MessageBus,
    TokenPool,
)

# CRITICAL SAFETY WARNING:
# TokenPool in this system MUST fail catastrophically if token distribution fails.
# NO FALLBACK to single tokens from environment variables is allowed.
# Agents are FORBIDDEN from adding fallback mechanisms to TokenPool usage.

logger = logging.getLogger(__name__)


@dataclass
class CollaborationConfig:
    """Configuration for collaborative execution"""

    enable_messaging: bool = True
    enable_shared_workspace: bool = True
    enable_team_formation: bool = True
    team_formation_mode: str = "auto"  # auto, manual, skill-based
    max_team_size: int = 10
    message_retention_hours: int = 24
    workspace_sync_interval: float = 1.0
    collaboration_timeout: float = 300.0


@dataclass
class AgentCapabilities:
    """Agent capability definitions for team formation"""

    agent_id: str
    skills: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    performance_score: float = 1.0
    availability_score: float = 1.0
    collaboration_score: float = 1.0


@dataclass
class CollaborativeTask(AgentTask):
    """Enhanced task with collaboration features"""

    # Collaboration settings
    collaboration_enabled: bool = True
    team_id: Optional[str] = None
    required_capabilities: List[str] = field(default_factory=list)
    collaboration_mode: str = "shared"  # shared, handoff, review

    # Agent coordination
    assigned_agents: List[str] = field(default_factory=list)
    collaborating_agents: Set[str] = field(default_factory=set)

    # Workspace management
    shared_workspace: Optional[str] = None
    workspace_permissions: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict with collaboration data"""
        data = super().to_dict()
        data.update(
            {
                "collaboration_enabled": self.collaboration_enabled,
                "team_id": self.team_id,
                "required_capabilities": self.required_capabilities,
                "collaboration_mode": self.collaboration_mode,
                "assigned_agents": self.assigned_agents,
                "collaborating_agents": list(self.collaborating_agents),
                "shared_workspace": self.shared_workspace,
                "workspace_permissions": self.workspace_permissions,
            }
        )
        return data


class CollaborationManager:
    """Manages agent collaboration, messaging, and coordination"""

    def __init__(self, config: CollaborationConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir

        # Agent management
        self.active_agents: Dict[str, AgentCapabilities] = {}
        self.agent_teams: Dict[str, List[str]] = {}
        self.agent_status: Dict[str, str] = {}  # idle, working, collaborating

        # Messaging system
        self.message_bus = MessageBus(output_dir / "collaboration_messages")
        self.message_history: List[Dict] = []

        # Workspace management
        self.shared_workspaces: Dict[str, Dict] = {}
        self.workspace_locks: Dict[str, asyncio.Lock] = {}

        # Events and coordination
        self.collaboration_events: List[Dict] = []
        self.coordination_lock = asyncio.Lock()

        logger.info(f"CollaborationManager initialized: {config}")

    async def register_agent(self, agent_id: str, capabilities: AgentCapabilities):
        """Register an agent for collaboration"""
        async with self.coordination_lock:
            self.active_agents[agent_id] = capabilities
            self.agent_status[agent_id] = "idle"
            logger.info(
                f"Agent registered: {agent_id} with skills: {capabilities.skills}"
            )

    async def form_team(self, task: CollaborativeTask) -> List[str]:
        """Form optimal team for a collaborative task"""
        if not task.collaboration_enabled:
            return [task.task_id]  # Single agent

        if self.config.team_formation_mode == "manual":
            return task.assigned_agents or [task.task_id]

        # Auto team formation based on capabilities
        available_agents = [
            agent_id
            for agent_id, status in self.agent_status.items()
            if status in ["idle", "collaborating"]
        ]

        if not task.required_capabilities:
            # Simple round-robin assignment
            team_size = min(len(available_agents), self.config.max_team_size)
            return available_agents[:team_size]

        # Skill-based team formation
        scored_agents = []
        for agent_id in available_agents:
            capabilities = self.active_agents[agent_id]
            skill_score = len(
                set(capabilities.skills) & set(task.required_capabilities)
            )
            total_score = (
                skill_score
                * capabilities.performance_score
                * capabilities.availability_score
            )
            scored_agents.append((agent_id, total_score))

        # Select top agents
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        team_size = min(len(scored_agents), self.config.max_team_size)
        team = [agent_id for agent_id, _ in scored_agents[:team_size]]

        logger.info(f"Formed team for {task.task_id}: {team}")
        return team

    async def create_shared_workspace(
        self, workspace_id: str, team_agents: List[str]
    ) -> Dict:
        """Create shared workspace for team collaboration"""
        workspace_dir = self.output_dir / "shared_workspaces" / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)

        workspace_info = {
            "workspace_id": workspace_id,
            "created_at": datetime.now().isoformat(),
            "team_agents": team_agents,
            "workspace_dir": str(workspace_dir),
            "files": {},
            "activity_log": [],
        }

        self.shared_workspaces[workspace_id] = workspace_info
        self.workspace_locks[workspace_id] = asyncio.Lock()

        # Create workspace metadata file
        metadata_file = workspace_dir / "workspace_metadata.json"
        metadata_file.write_text(json.dumps(workspace_info, indent=2))

        logger.info(f"Created shared workspace: {workspace_id}")
        return workspace_info

    async def send_message(self, from_agent: str, to_agents: List[str], message: Dict):
        """Send collaboration message between agents"""
        if not self.config.enable_messaging:
            return

        timestamp = datetime.now().isoformat()
        message_data = {
            "message_id": str(uuid.uuid4()),
            "from_agent": from_agent,
            "to_agents": to_agents,
            "message": message,
            "timestamp": timestamp,
            "message_type": message.get("type", "general"),
        }

        # Send via message bus
        for to_agent in to_agents:
            await self.message_bus.send(from_agent, to_agent, message_data)

        # Store in history
        self.message_history.append(message_data)

        # Log collaboration event
        self.collaboration_events.append(
            {
                "event_type": "message_sent",
                "timestamp": timestamp,
                "from_agent": from_agent,
                "to_agents": to_agents,
                "message_type": message_data["message_type"],
            }
        )

    async def get_messages(self, agent_id: str) -> List[Dict]:
        """Get pending messages for an agent"""
        if not self.config.enable_messaging:
            return []

        return await self.message_bus.receive(agent_id)

    async def log_collaboration_event(
        self, event_type: str, agent_id: str, details: Dict
    ):
        """Log collaboration event for monitoring"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "details": details,
        }
        self.collaboration_events.append(event)


class CollaborativeOrchestrator(GenericOrchestrator):
    """
    Orchestrator extended with real-time agent collaboration capabilities.
    Maintains full backwards compatibility with GenericOrchestrator.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        collaboration_config: Optional[CollaborationConfig] = None,
    ):
        # Initialize base orchestrator
        super().__init__(output_dir, max_parallel, tokens, use_optimizations)

        # Collaboration configuration
        self.collaboration_config = collaboration_config or CollaborationConfig()

        # Collaboration system
        self.collaboration_manager = CollaborationManager(
            self.collaboration_config, output_dir
        )

        # Execution modes
        self.execution_mode = "traditional"  # traditional, collaborative, hybrid

        # Collaborative task tracking
        self.collaborative_tasks: Dict[str, CollaborativeTask] = {}
        self.team_assignments: Dict[str, List[str]] = {}

        logger.info(f"CollaborativeOrchestrator initialized")
        logger.info(f"Collaboration config: {self.collaboration_config}")

    def enable_collaboration(self):
        """Enable collaborative execution mode"""
        self.execution_mode = "collaborative"
        logger.info("Collaborative execution mode enabled")

    def enable_hybrid_mode(self):
        """Enable hybrid execution mode (some tasks collaborative, others traditional)"""
        self.execution_mode = "hybrid"
        logger.info("Hybrid execution mode enabled")

    async def register_collaborative_agent(
        self, agent_id: str, skills: List[str] = None, specializations: List[str] = None
    ):
        """Register an agent for collaboration"""
        capabilities = AgentCapabilities(
            agent_id=agent_id,
            skills=skills or [],
            specializations=specializations or [],
        )
        await self.collaboration_manager.register_agent(agent_id, capabilities)

    async def execute_collaborative_agent(self, task: CollaborativeTask) -> Dict:
        """Execute an agent with collaboration features"""

        # Check if collaboration is needed
        if not task.collaboration_enabled or self.execution_mode == "traditional":
            # Fall back to traditional execution
            base_task = AgentTask(
                task_id=task.task_id,
                task_type=task.task_type,
                prompt=task.prompt,
                context=task.context,
                dependencies=task.dependencies,
            )
            return await self.execute_agent(base_task)

        # Register agent for this task
        await self.register_collaborative_agent(
            task.task_id,
            skills=task.required_capabilities,
            specializations=[task.task_type],
        )

        # Form team if needed
        team_agents = await self.collaboration_manager.form_team(task)
        task.assigned_agents = team_agents
        task.team_id = f"team_{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create shared workspace if multiple agents
        if len(team_agents) > 1 and self.collaboration_config.enable_shared_workspace:
            workspace_id = f"ws_{task.task_id}"
            workspace = await self.collaboration_manager.create_shared_workspace(
                workspace_id, team_agents
            )
            task.shared_workspace = workspace_id

        # Enhanced prompt with collaboration context
        collaboration_context = self._build_collaboration_context(task, team_agents)
        enhanced_prompt = f"{task.prompt}\n\n{collaboration_context}"

        # Update task prompt
        task.prompt = enhanced_prompt

        # Execute with collaboration features
        result = await self._execute_with_collaboration(task)

        return result

    def _build_collaboration_context(
        self, task: CollaborativeTask, team_agents: List[str]
    ) -> str:
        """Build collaboration context for agent prompt"""
        context_parts = []

        if self.collaboration_config.enable_messaging:
            context_parts.append(
                f"COLLABORATION ENABLED: You are working with team agents: {', '.join(team_agents)}"
            )
            context_parts.append(
                "You can communicate with other agents using the collaboration messaging system."
            )

        if task.shared_workspace:
            workspace_dir = (
                self.output_dir / "shared_workspaces" / task.shared_workspace
            )
            context_parts.append(f"SHARED WORKSPACE: {workspace_dir}")
            context_parts.append(
                "You can read from and write to the shared workspace. "
                "Other agents can see your changes in real-time."
            )

        if task.collaboration_mode == "handoff":
            context_parts.append(
                "HANDOFF MODE: Complete your part of the task and pass it to the next agent."
            )
        elif task.collaboration_mode == "review":
            context_parts.append(
                "REVIEW MODE: Review and provide feedback on work from other agents."
            )
        else:  # shared mode
            context_parts.append(
                "SHARED MODE: Work collaboratively with other agents on the same task."
            )

        return "\n".join(context_parts)

    async def _execute_with_collaboration(self, task: CollaborativeTask) -> Dict:
        """Execute task with collaboration features enabled"""

        session_id = str(uuid.uuid4())

        # Pre-execution collaboration setup
        await self.collaboration_manager.log_collaboration_event(
            "task_started", task.task_id, {"team_agents": task.assigned_agents}
        )

        # Build collaborative command
        cmd = self.claude_cmd.copy()

        # Add collaborative system prompt
        collaborative_system_prompt = (
            "You are part of a collaborative multi-agent team. "
            "Communicate effectively with other agents and work together to achieve the best results. "
            "Use the shared workspace for exchanging information and artifacts."
        )
        cmd.extend(["--append-system-prompt", collaborative_system_prompt])

        # Add shared workspace to accessible directories
        if task.shared_workspace:
            workspace_dir = (
                self.output_dir / "shared_workspaces" / task.shared_workspace
            )
            cmd.extend(["--add-dir", str(workspace_dir)])

        # Add collaboration session info
        cmd.extend(
            [
                "--session-id",
                session_id,
                "--add-dir",
                str(self.output_dir),
                "--",
                task.prompt,
            ]
        )

        # Execute with collaboration monitoring
        result = await self._execute_with_monitoring(task, cmd)

        # Post-execution collaboration
        await self.collaboration_manager.log_collaboration_event(
            "task_completed", task.task_id, {"status": result.get("status", "unknown")}
        )

        return result

    async def _execute_with_monitoring(
        self, task: CollaborativeTask, cmd: List[str]
    ) -> Dict:
        """Execute command with collaboration monitoring"""

        # Get token
        token, token_idx = await self.token_pool.acquire()

        try:
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token

            # Execute
            task.start_time = datetime.now().timestamp()
            task.status = "running"
            await self.dep_manager.mark_running(task.task_id)

            try:
                logger.info(f"Executing collaborative task: {task.task_id}")

                # Check for collaboration messages during execution
                async def check_messages():
                    while task.status == "running":
                        messages = await self.collaboration_manager.get_messages(
                            task.task_id
                        )
                        if messages:
                            logger.info(
                                f"Agent {task.task_id} received {len(messages)} messages"
                            )
                        await asyncio.sleep(
                            self.collaboration_config.workspace_sync_interval
                        )

                # Start message monitoring
                message_task = asyncio.create_task(check_messages())

                # Execute main process
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                # Stop message monitoring
                message_task.cancel()

                task.end_time = datetime.now().timestamp()
                duration = task.end_time - task.start_time

                if process.returncode == 0:
                    task.status = "completed"
                    task.result = json.loads(stdout.decode())
                    await self.dep_manager.mark_completed(task.task_id)
                    self.metrics["completed"] += 1
                    logger.info(
                        f"✓ Collaborative task {task.task_id} completed in {duration:.2f}s"
                    )
                else:
                    task.status = "failed"
                    task.error = stderr.decode()
                    await self.dep_manager.mark_failed(task.task_id)
                    self.metrics["failed"] += 1
                    logger.error(
                        f"✗ Collaborative task {task.task_id} failed: {task.error}"
                    )

                self.metrics["total_duration"] += duration

            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                await self.dep_manager.mark_failed(task.task_id)
                self.metrics["failed"] += 1
                logger.error(f"✗ Collaborative task {task.task_id} exception: {e}")

        finally:
            # Always release the token
            if hasattr(self.token_pool, "release"):
                self.token_pool.release(token_idx)

        # Save collaborative task state
        task_file = self.output_dir / "tasks" / f"{task.task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

        return task.to_dict()

    async def run_collaborative(
        self,
        tasks: List[CollaborativeTask],
        collaboration_config: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute tasks with collaboration features.

        Args:
            tasks: List of CollaborativeTask objects
            collaboration_config: Optional collaboration configuration overrides

        Returns:
            Execution metrics and results
        """

        # Override config if provided
        if collaboration_config:
            for key, value in collaboration_config.items():
                if hasattr(self.collaboration_config, key):
                    setattr(self.collaboration_config, key, value)

        # Enable collaboration
        self.enable_collaboration()

        logger.info("=" * 60)
        logger.info("Collaborative Agent Orchestrator")
        logger.info(f"Collaborative tasks: {len(tasks)}")
        logger.info(f"Collaboration config: {self.collaboration_config}")
        logger.info("=" * 60)

        # Store collaborative tasks
        for task in tasks:
            self.collaborative_tasks[task.task_id] = task

        # Execute tasks with collaboration
        self.metrics["total"] = len(tasks)
        self.metrics["start_time"] = datetime.now().isoformat()

        results = []

        while len(results) < len(tasks):
            # Find ready tasks
            ready_tasks = []
            for task in tasks:
                if task.status == "pending" and await self.dep_manager.can_run(task):
                    ready_tasks.append(task)
                    if len(ready_tasks) >= self.max_parallel:
                        break

            if not ready_tasks:
                # Handle deadlock
                pending = [t for t in tasks if t.status == "pending"]
                if pending:
                    logger.warning(f"Possible deadlock: {len(pending)} tasks pending")
                    for task in pending:
                        task.status = "failed"
                        task.error = "Dependencies not met"
                        results.append(task.to_dict())
                break

            # Execute ready tasks collaboratively
            logger.info(f"Executing collaborative batch of {len(ready_tasks)} tasks")
            batch_results = await asyncio.gather(
                *[self.execute_collaborative_agent(task) for task in ready_tasks],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Collaborative batch execution error: {result}")
                else:
                    results.append(result)

            await asyncio.sleep(0.5)

        self.metrics["end_time"] = datetime.now().isoformat()

        # Save collaboration summary
        await self._save_collaboration_summary()

        logger.info("=" * 60)
        logger.info("COLLABORATIVE EXECUTION COMPLETE")
        logger.info(f"Total: {self.metrics['total']}")
        logger.info(f"Completed: {self.metrics['completed']}")
        logger.info(f"Failed: {self.metrics['failed']}")
        logger.info(
            f"Collaboration events: {len(self.collaboration_manager.collaboration_events)}"
        )
        logger.info("=" * 60)

        return {
            "metrics": self.metrics,
            "results": results,
            "collaboration_events": self.collaboration_manager.collaboration_events,
            "message_history": self.collaboration_manager.message_history,
        }

    async def _save_collaboration_summary(self):
        """Save collaboration execution summary"""
        summary = {
            "execution_mode": self.execution_mode,
            "collaboration_config": asdict(self.collaboration_config),
            "metrics": self.metrics,
            "active_agents": {
                agent_id: asdict(caps)
                for agent_id, caps in self.collaboration_manager.active_agents.items()
            },
            "collaboration_events": self.collaboration_manager.collaboration_events,
            "message_history": self.collaboration_manager.message_history,
            "shared_workspaces": list(
                self.collaboration_manager.shared_workspaces.keys()
            ),
            "generated_at": datetime.now().isoformat(),
        }

        summary_file = self.output_dir / "collaboration_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2))
        logger.info(f"Collaboration summary saved: {summary_file}")


# Backwards compatibility: provide traditional interface
async def run_traditional(
    orchestrator: CollaborativeOrchestrator,
    task_generator: Callable[[], List[AgentTask]],
    result_processor: Optional[Callable[[List[Dict]], None]] = None,
) -> Dict:
    """
    Run orchestrator in traditional mode (backwards compatible)
    """

    # Generate tasks
    tasks = task_generator()

    # Convert to base AgentTask objects to ensure traditional execution
    base_tasks = [
        AgentTask(
            task_id=task.task_id,
            task_type=task.task_type,
            prompt=task.prompt,
            context=task.context,
            dependencies=task.dependencies,
        )
        for task in tasks
    ]

    # Execute in traditional mode
    results = await orchestrator.execute_batch(base_tasks)

    # Process results if processor provided
    if result_processor:
        await result_processor(results)

    return {"metrics": orchestrator.metrics, "results": results}
