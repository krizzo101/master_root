#!/usr/bin/env python3
"""
Collaboration Module for UnifiedOrchestrator
Enables team-based task execution with shared workspaces and handoffs
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..unified.orchestrator_module import ModuleConfig, OrchestratorModule

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    """Types of collaboration between agents"""

    SHARED = "shared"  # Multiple agents work on same task simultaneously
    HANDOFF = "handoff"  # Sequential task handoff between agents
    REVIEW = "review"  # One agent reviews another's work
    PARALLEL = "parallel"  # Independent parallel execution
    CONSENSUS = "consensus"  # Multiple agents must agree on result


@dataclass
class Team:
    """Represents a team of collaborating agents"""

    team_id: str
    name: str
    members: List[str] = field(default_factory=list)
    leader: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    workspace_path: Optional[Path] = None
    active_tasks: Set[str] = field(default_factory=set)
    completed_tasks: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_member(self, agent_id: str):
        """Add a member to the team"""
        if agent_id not in self.members:
            self.members.append(agent_id)
            if not self.leader:
                self.leader = agent_id

    def remove_member(self, agent_id: str):
        """Remove a member from the team"""
        if agent_id in self.members:
            self.members.remove(agent_id)
            if self.leader == agent_id and self.members:
                self.leader = self.members[0]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "team_id": self.team_id,
            "name": self.name,
            "members": self.members,
            "leader": self.leader,
            "created_at": self.created_at.isoformat(),
            "workspace_path": str(self.workspace_path) if self.workspace_path else None,
            "active_tasks": list(self.active_tasks),
            "completed_tasks": list(self.completed_tasks),
            "metadata": self.metadata,
        }


@dataclass
class SharedWorkspace:
    """Shared workspace for team collaboration"""

    workspace_id: str
    team_id: str
    path: Path
    created_at: datetime = field(default_factory=datetime.now)
    last_sync: datetime = field(default_factory=datetime.now)
    files: Dict[str, Dict] = field(default_factory=dict)  # filename -> metadata
    locks: Dict[str, str] = field(default_factory=dict)  # filename -> agent_id

    def acquire_lock(self, filename: str, agent_id: str) -> bool:
        """Acquire a file lock"""
        if filename not in self.locks:
            self.locks[filename] = agent_id
            return True
        return self.locks[filename] == agent_id

    def release_lock(self, filename: str, agent_id: str) -> bool:
        """Release a file lock"""
        if filename in self.locks and self.locks[filename] == agent_id:
            del self.locks[filename]
            return True
        return False

    def is_locked(self, filename: str) -> bool:
        """Check if a file is locked"""
        return filename in self.locks


@dataclass
class TaskHandoff:
    """Represents a task handoff between agents"""

    handoff_id: str
    task_id: str
    from_agent: str
    to_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, accepted, rejected, completed
    notes: Optional[str] = None


class CollaborationModule(OrchestratorModule):
    """
    Module implementing collaboration features for multi-agent teams.
    Manages teams, shared workspaces, and task handoffs.
    """

    def __init__(self, orchestrator, config: ModuleConfig = None):
        super().__init__(orchestrator, config)
        self.teams: Dict[str, Team] = {}
        self.workspaces: Dict[str, SharedWorkspace] = {}
        self.handoffs: Dict[str, TaskHandoff] = {}
        self.agent_teams: Dict[str, str] = {}  # agent_id -> team_id
        self.team_performance: Dict[str, Dict] = defaultdict(
            lambda: {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_duration": 0,
                "handoffs_completed": 0,
                "conflicts_resolved": 0,
            }
        )

        self.teams_dir = None
        self.workspaces_dir = None
        self.sync_task: Optional[asyncio.Task] = None

        # Configuration
        self.max_team_size = config.config.get("max_team_size", 5) if config else 5
        self.sync_interval = (
            config.config.get("sync_interval", 60.0) if config else 60.0
        )

    @property
    def name(self) -> str:
        return "collaboration"

    @property
    def description(self) -> str:
        return "Multi-agent collaboration with teams and shared workspaces"

    async def _initialize(self):
        """Initialize collaboration module"""
        # Setup directories
        self.teams_dir = self.orchestrator.output_dir / "teams"
        self.teams_dir.mkdir(parents=True, exist_ok=True)

        self.workspaces_dir = self.orchestrator.output_dir / "workspaces"
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)

        # Start workspace sync task
        self.sync_task = asyncio.create_task(self._workspace_sync_loop())

        # Load existing teams if any
        await self._load_teams()

        logger.info(
            f"Collaboration module initialized with max team size: {self.max_team_size}"
        )

    async def _load_teams(self):
        """Load existing teams from disk"""
        teams_file = self.teams_dir / "teams.json"
        if teams_file.exists():
            try:
                teams_data = json.loads(teams_file.read_text())
                for team_data in teams_data:
                    team = Team(
                        team_id=team_data["team_id"],
                        name=team_data["name"],
                        members=team_data["members"],
                        leader=team_data.get("leader"),
                        created_at=datetime.fromisoformat(team_data["created_at"]),
                        metadata=team_data.get("metadata", {}),
                    )
                    self.teams[team.team_id] = team

                    # Update agent-team mappings
                    for member in team.members:
                        self.agent_teams[member] = team.team_id

                logger.info(f"Loaded {len(self.teams)} existing teams")
            except Exception as e:
                logger.error(f"Error loading teams: {e}")

    async def _save_teams(self):
        """Save teams to disk"""
        teams_file = self.teams_dir / "teams.json"
        teams_data = [team.to_dict() for team in self.teams.values()]
        teams_file.write_text(json.dumps(teams_data, indent=2, default=str))

    async def _workspace_sync_loop(self):
        """Background task to sync shared workspaces"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self._sync_all_workspaces()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in workspace sync: {e}")

    async def _sync_all_workspaces(self):
        """Sync all active workspaces"""
        for workspace in self.workspaces.values():
            await self._sync_workspace(workspace)

    async def _sync_workspace(self, workspace: SharedWorkspace):
        """Sync a shared workspace"""
        workspace.last_sync = datetime.now()

        # Check for file changes
        if workspace.path.exists():
            current_files = set()
            for file_path in workspace.path.rglob("*"):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(workspace.path))
                    current_files.add(rel_path)

                    # Update file metadata
                    if rel_path not in workspace.files:
                        workspace.files[rel_path] = {
                            "created": datetime.now().isoformat(),
                            "modified": datetime.now().isoformat(),
                            "size": file_path.stat().st_size,
                        }
                    else:
                        workspace.files[rel_path][
                            "modified"
                        ] = datetime.now().isoformat()
                        workspace.files[rel_path]["size"] = file_path.stat().st_size

            # Remove deleted files
            deleted_files = set(workspace.files.keys()) - current_files
            for filename in deleted_files:
                del workspace.files[filename]
                if filename in workspace.locks:
                    del workspace.locks[filename]

        # Save workspace state
        workspace_file = self.workspaces_dir / f"{workspace.workspace_id}.json"
        workspace_file.write_text(
            json.dumps(
                {
                    "workspace_id": workspace.workspace_id,
                    "team_id": workspace.team_id,
                    "path": str(workspace.path),
                    "created_at": workspace.created_at.isoformat(),
                    "last_sync": workspace.last_sync.isoformat(),
                    "files": workspace.files,
                    "locks": workspace.locks,
                },
                indent=2,
            )
        )

    def create_team(self, name: str, members: Optional[List[str]] = None) -> Team:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        team = Team(team_id=team_id, name=name, members=members or [])

        # Create workspace for team
        workspace_path = self.workspaces_dir / team_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        team.workspace_path = workspace_path

        # Create shared workspace
        workspace = SharedWorkspace(
            workspace_id=team_id, team_id=team_id, path=workspace_path
        )
        self.workspaces[team_id] = workspace

        # Register team
        self.teams[team_id] = team

        # Update agent-team mappings
        for member in team.members:
            self.agent_teams[member] = team_id

        logger.info(f"Created team '{name}' with {len(team.members)} members")

        # Save teams
        asyncio.create_task(self._save_teams())

        return team

    def assign_to_team(self, agent_id: str, team_id: str) -> bool:
        """Assign an agent to a team"""
        if team_id not in self.teams:
            logger.error(f"Team {team_id} not found")
            return False

        team = self.teams[team_id]

        if len(team.members) >= self.max_team_size:
            logger.warning(f"Team {team_id} is at maximum capacity")
            return False

        # Remove from current team if any
        if agent_id in self.agent_teams:
            old_team_id = self.agent_teams[agent_id]
            if old_team_id in self.teams:
                self.teams[old_team_id].remove_member(agent_id)

        # Add to new team
        team.add_member(agent_id)
        self.agent_teams[agent_id] = team_id

        logger.info(f"Assigned agent {agent_id} to team {team.name}")

        # Save teams
        asyncio.create_task(self._save_teams())

        return True

    def create_handoff(
        self,
        task_id: str,
        from_agent: str,
        to_agent: str,
        context: Optional[Dict] = None,
        artifacts: Optional[List[str]] = None,
    ) -> TaskHandoff:
        """Create a task handoff between agents"""
        handoff_id = str(uuid.uuid4())
        handoff = TaskHandoff(
            handoff_id=handoff_id,
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            context=context or {},
            artifacts=artifacts or [],
        )

        self.handoffs[handoff_id] = handoff

        logger.info(
            f"Created handoff {handoff_id}: {from_agent} -> {to_agent} for task {task_id}"
        )

        # Save handoff
        handoff_file = self.teams_dir / f"handoff_{handoff_id}.json"
        handoff_file.write_text(
            json.dumps(
                {
                    "handoff_id": handoff.handoff_id,
                    "task_id": handoff.task_id,
                    "from_agent": handoff.from_agent,
                    "to_agent": handoff.to_agent,
                    "timestamp": handoff.timestamp.isoformat(),
                    "context": handoff.context,
                    "artifacts": handoff.artifacts,
                    "status": handoff.status,
                    "notes": handoff.notes,
                },
                indent=2,
            )
        )

        return handoff

    def accept_handoff(self, handoff_id: str, agent_id: str) -> bool:
        """Accept a task handoff"""
        if handoff_id not in self.handoffs:
            return False

        handoff = self.handoffs[handoff_id]
        if handoff.to_agent != agent_id:
            return False

        handoff.status = "accepted"
        logger.info(f"Agent {agent_id} accepted handoff {handoff_id}")

        return True

    def complete_handoff(
        self, handoff_id: str, agent_id: str, notes: Optional[str] = None
    ) -> bool:
        """Complete a task handoff"""
        if handoff_id not in self.handoffs:
            return False

        handoff = self.handoffs[handoff_id]
        if handoff.to_agent != agent_id or handoff.status != "accepted":
            return False

        handoff.status = "completed"
        handoff.notes = notes

        # Update team performance
        from_team = self.agent_teams.get(handoff.from_agent)
        to_team = self.agent_teams.get(handoff.to_agent)

        if from_team:
            self.team_performance[from_team]["handoffs_completed"] += 1
        if to_team and to_team != from_team:
            self.team_performance[to_team]["handoffs_completed"] += 1

        logger.info(f"Handoff {handoff_id} completed by {agent_id}")

        return True

    def get_team_workspace(self, team_id: str) -> Optional[SharedWorkspace]:
        """Get the shared workspace for a team"""
        return self.workspaces.get(team_id)

    def acquire_workspace_lock(
        self, team_id: str, filename: str, agent_id: str
    ) -> bool:
        """Acquire a lock on a file in the team workspace"""
        workspace = self.workspaces.get(team_id)
        if not workspace:
            return False

        return workspace.acquire_lock(filename, agent_id)

    def release_workspace_lock(
        self, team_id: str, filename: str, agent_id: str
    ) -> bool:
        """Release a lock on a file in the team workspace"""
        workspace = self.workspaces.get(team_id)
        if not workspace:
            return False

        return workspace.release_lock(filename, agent_id)

    async def pre_task_execution(self, task: "AgentTask"):
        """Setup collaboration before task execution"""
        # Check if task has team assignment
        if hasattr(task, "team_id") and task.team_id:
            if task.team_id not in self.teams:
                # Create team if it doesn't exist
                team = self.create_team(f"Team {task.team_id}", [])
                task.team_id = team.team_id

            team = self.teams[task.team_id]
            team.active_tasks.add(task.task_id)

            # Assign agents if specified
            if hasattr(task, "assigned_agents"):
                for agent_id in task.assigned_agents:
                    self.assign_to_team(agent_id, task.team_id)

            # Setup collaboration mode
            if hasattr(task, "collaboration_mode"):
                mode = CollaborationMode(task.collaboration_mode)

                if mode == CollaborationMode.SHARED:
                    # Setup shared workspace access
                    workspace = self.get_team_workspace(task.team_id)
                    if workspace:
                        task.workspace_path = workspace.path
                        logger.info(
                            f"Task {task.task_id} using shared workspace: {workspace.path}"
                        )

                elif mode == CollaborationMode.HANDOFF:
                    # Check for pending handoffs
                    for handoff_id, handoff in self.handoffs.items():
                        if (
                            handoff.task_id == task.task_id
                            and handoff.status == "pending"
                        ):
                            # Auto-accept handoff if this is the target agent
                            if (
                                hasattr(task, "agent_id")
                                and task.agent_id == handoff.to_agent
                            ):
                                self.accept_handoff(handoff_id, task.agent_id)
                                task.handoff_context = handoff.context
                                task.handoff_artifacts = handoff.artifacts

    async def post_task_execution(self, task: "AgentTask"):
        """Handle collaboration after task execution"""
        # Update team task status
        if hasattr(task, "team_id") and task.team_id in self.teams:
            team = self.teams[task.team_id]

            if task.task_id in team.active_tasks:
                team.active_tasks.remove(task.task_id)
                team.completed_tasks.add(task.task_id)

            # Update team performance
            self.team_performance[task.team_id][
                "tasks_completed" if task.status == "completed" else "tasks_failed"
            ] += 1

            if hasattr(task, "start_time") and hasattr(task, "end_time"):
                duration = (task.end_time - task.start_time).total_seconds()
                self.team_performance[task.team_id]["total_duration"] += duration

    async def on_task_success(self, task: "AgentTask"):
        """Handle successful task with collaboration"""
        # Check if handoff is needed
        if hasattr(task, "next_agent") and task.next_agent:
            # Create handoff to next agent
            handoff = self.create_handoff(
                task.task_id,
                getattr(task, "agent_id", "unknown"),
                task.next_agent,
                context={"result": task.result} if hasattr(task, "result") else {},
                artifacts=getattr(task, "output_files", []),
            )

            logger.info(f"Created handoff for successful task {task.task_id}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get collaboration metrics"""
        return {
            "total_teams": len(self.teams),
            "active_teams": sum(1 for t in self.teams.values() if t.active_tasks),
            "total_members": sum(len(t.members) for t in self.teams.values()),
            "total_handoffs": len(self.handoffs),
            "completed_handoffs": sum(
                1 for h in self.handoffs.values() if h.status == "completed"
            ),
            "workspaces": len(self.workspaces),
            "team_performance": dict(self.team_performance),
            "largest_team": max(
                (len(t.members) for t in self.teams.values()), default=0
            ),
            "busiest_team": max(
                ((t.team_id, len(t.active_tasks)) for t in self.teams.values()),
                key=lambda x: x[1],
                default=(None, 0),
            ),
        }

    async def _cleanup(self):
        """Cleanup module resources"""
        # Cancel sync task
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        # Save final teams state
        await self._save_teams()

        # Save final collaboration report
        report = {
            "timestamp": datetime.now().isoformat(),
            "teams": [team.to_dict() for team in self.teams.values()],
            "handoffs": [
                {
                    "handoff_id": h.handoff_id,
                    "task_id": h.task_id,
                    "from_agent": h.from_agent,
                    "to_agent": h.to_agent,
                    "status": h.status,
                    "timestamp": h.timestamp.isoformat(),
                }
                for h in self.handoffs.values()
            ],
            "metrics": self.get_metrics(),
        }

        report_file = (
            self.teams_dir
            / f"final_collaboration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.write_text(json.dumps(report, indent=2, default=str))

        logger.info("Collaboration module cleanup complete")
