"""
Git Worktree Manager for Multi-Agent Isolation
Core functionality for managing agent-specific worktrees
"""

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentWorktree:
    """Represents an agent's isolated worktree"""

    agent_id: str
    agent_type: str
    worktree_path: Path
    branch_name: str
    created_at: datetime
    status: str = "active"
    commits: List[str] = None

    def __post_init__(self):
        if self.commits is None:
            self.commits = []


class WorktreeManager:
    """
    Manages git worktrees for multi-agent parallel execution.
    Each agent gets an isolated workspace to prevent conflicts.
    """

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path("/home/opsvi/master_root")
        self.worktrees_base = Path("/home/opsvi/agent_worktrees")
        self.shared_space = Path("/home/opsvi/agent_shared")
        self.registry_file = self.worktrees_base / ".worktree_registry.json"
        self.active_worktrees: Dict[str, AgentWorktree] = {}

        # Initialize directories
        self.worktrees_base.mkdir(parents=True, exist_ok=True)
        self.shared_space.mkdir(parents=True, exist_ok=True)

        # Create shared subdirectories
        (self.shared_space / "messages").mkdir(exist_ok=True)
        (self.shared_space / "outputs").mkdir(exist_ok=True)
        (self.shared_space / "metrics").mkdir(exist_ok=True)
        (self.shared_space / "locks").mkdir(exist_ok=True)

        # Load existing registry
        self._load_registry()

    def _load_registry(self):
        """Load existing worktree registry"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file) as f:
                    data = json.load(f)
                    for agent_id, info in data.items():
                        self.active_worktrees[agent_id] = AgentWorktree(
                            agent_id=agent_id,
                            agent_type=info["agent_type"],
                            worktree_path=Path(info["worktree_path"]),
                            branch_name=info["branch_name"],
                            created_at=datetime.fromisoformat(info["created_at"]),
                            status=info.get("status", "active"),
                            commits=info.get("commits", []),
                        )
            except Exception as e:
                logger.warning(f"Could not load registry: {e}")

    def _save_registry(self):
        """Persist worktree registry"""
        data = {}
        for agent_id, worktree in self.active_worktrees.items():
            data[agent_id] = {
                "agent_type": worktree.agent_type,
                "worktree_path": str(worktree.worktree_path),
                "branch_name": worktree.branch_name,
                "created_at": worktree.created_at.isoformat(),
                "status": worktree.status,
                "commits": worktree.commits,
            }

        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2)

    def create_agent_worktree(
        self,
        agent_id: str,
        agent_type: str,
        base_branch: str = "main",
        execution_id: str = None,
    ) -> AgentWorktree:
        """
        Create isolated worktree for an agent.

        Args:
            agent_id: Unique identifier for agent
            agent_type: Type of agent (e.g., 'requirements-analyst')
            base_branch: Branch to base worktree on
            execution_id: Optional execution context ID

        Returns:
            AgentWorktree object with paths and info
        """

        # Generate unique branch name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"agent/{agent_type}/{timestamp}"
        if execution_id:
            branch_name = f"agent/{execution_id}/{agent_type}"

        # Determine worktree path
        worktree_name = f"{agent_id}_{agent_type}_{timestamp}"
        worktree_path = self.worktrees_base / worktree_name

        try:
            # Create branch from base
            logger.info(f"Creating branch {branch_name} from {base_branch}")
            # First check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                capture_output=True,
            )
            if result.returncode == 0:
                # Branch exists, delete it first
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                )
            # Save current branch
            current_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Now create fresh branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name, base_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Create worktree
            logger.info(f"Creating worktree at {worktree_path}")
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            # Switch back to original branch
            subprocess.run(
                ["git", "checkout", current_branch],
                cwd=self.repo_path,
                capture_output=True,
            )

            # Create agent workspace within worktree
            agent_workspace = worktree_path / "apps/multi-agent-monitor/agent_workspace"
            agent_workspace.mkdir(parents=True, exist_ok=True)

            # Create agent-specific directories
            (agent_workspace / "inputs").mkdir(exist_ok=True)
            (agent_workspace / "outputs").mkdir(exist_ok=True)
            (agent_workspace / "temp").mkdir(exist_ok=True)

            # Create agent info file
            agent_info = {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "worktree_path": str(worktree_path),
                "branch_name": branch_name,
                "shared_space": str(self.shared_space),
                "created_at": datetime.now().isoformat(),
            }

            info_file = agent_workspace / "agent_info.json"
            with open(info_file, "w") as f:
                json.dump(agent_info, f, indent=2)

            # Register worktree
            worktree = AgentWorktree(
                agent_id=agent_id,
                agent_type=agent_type,
                worktree_path=worktree_path,
                branch_name=branch_name,
                created_at=datetime.now(),
            )

            self.active_worktrees[agent_id] = worktree
            self._save_registry()

            logger.info(f"Successfully created worktree for {agent_id}")
            return worktree

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e.stderr.decode()}")
            raise RuntimeError(f"Worktree creation failed: {e}")

    def get_agent_environment(self, agent_id: str) -> Dict[str, Any]:
        """
        Get environment configuration for an agent.

        Returns:
            Dict with paths and configuration for agent execution
        """

        if agent_id not in self.active_worktrees:
            raise ValueError(f"No worktree for agent {agent_id}")

        worktree = self.active_worktrees[agent_id]

        return {
            "working_directory": str(worktree.worktree_path),
            "agent_workspace": str(
                worktree.worktree_path / "apps/multi-agent-monitor/agent_workspace"
            ),
            "shared_messages": str(self.shared_space / "messages"),
            "shared_outputs": str(self.shared_space / "outputs"),
            "branch_name": worktree.branch_name,
            "agent_type": worktree.agent_type,
            "created_at": worktree.created_at.isoformat(),
        }

    def commit_agent_work(
        self, agent_id: str, message: str, files: List[str] = None
    ) -> str:
        """
        Commit agent's work in their worktree.

        Args:
            agent_id: Agent identifier
            message: Commit message
            files: Specific files to commit (None = all)

        Returns:
            Commit hash
        """

        if agent_id not in self.active_worktrees:
            raise ValueError(f"No worktree for agent {agent_id}")

        worktree = self.active_worktrees[agent_id]

        try:
            # Add files
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file], cwd=worktree.worktree_path, check=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "-A"], cwd=worktree.worktree_path, check=True
                )

            # Commit with agent attribution
            full_message = f"[{worktree.agent_type}] {message}"
            result = subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=worktree.worktree_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Get commit hash
                commit_hash = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=worktree.worktree_path,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()

                worktree.commits.append(commit_hash)
                self._save_registry()

                logger.info(f"Agent {agent_id} committed: {commit_hash[:8]}")
                return commit_hash
            else:
                logger.warning(f"Nothing to commit for agent {agent_id}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Commit failed for agent {agent_id}: {e}")
            raise

    def merge_agent_work(
        self, agent_id: str, target_branch: str = "main", strategy: str = "merge"
    ) -> bool:
        """
        Merge agent's work into target branch.

        Args:
            agent_id: Agent identifier
            target_branch: Branch to merge into
            strategy: 'merge', 'rebase', or 'squash'

        Returns:
            Success status
        """

        if agent_id not in self.active_worktrees:
            raise ValueError(f"No worktree for agent {agent_id}")

        worktree = self.active_worktrees[agent_id]

        try:
            # Switch to target branch in main repo
            subprocess.run(
                ["git", "checkout", target_branch], cwd=self.repo_path, check=True
            )

            if strategy == "merge":
                subprocess.run(
                    [
                        "git",
                        "merge",
                        worktree.branch_name,
                        "--no-ff",
                        "-m",
                        f"Merge {worktree.agent_type} work",
                    ],
                    cwd=self.repo_path,
                    check=True,
                )
            elif strategy == "squash":
                subprocess.run(
                    ["git", "merge", "--squash", worktree.branch_name],
                    cwd=self.repo_path,
                    check=True,
                )
                subprocess.run(
                    ["git", "commit", "-m", f"Squashed {worktree.agent_type} work"],
                    cwd=self.repo_path,
                    check=True,
                )
            elif strategy == "rebase":
                subprocess.run(
                    ["git", "rebase", target_branch],
                    cwd=worktree.worktree_path,
                    check=True,
                )

            logger.info(f"Successfully merged {agent_id} work into {target_branch}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Merge failed: {e}")
            return False

    def cleanup_worktree(self, agent_id: str, force: bool = False):
        """
        Remove agent's worktree and optionally delete branch.

        Args:
            agent_id: Agent identifier
            force: Force removal even if uncommitted changes
        """

        if agent_id not in self.active_worktrees:
            return

        worktree = self.active_worktrees[agent_id]

        try:
            # Remove worktree
            cmd = ["git", "worktree", "remove", str(worktree.worktree_path)]
            if force:
                cmd.append("--force")

            subprocess.run(cmd, cwd=self.repo_path, check=True)

            # Delete branch
            subprocess.run(
                ["git", "branch", "-D", worktree.branch_name],
                cwd=self.repo_path,
                check=False,  # OK if branch doesn't exist
            )

            # Remove from registry
            del self.active_worktrees[agent_id]
            self._save_registry()

            logger.info(f"Cleaned up worktree for {agent_id}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Cleanup failed: {e}")
            if not force:
                logger.info("Try with force=True to override")

    def list_active_worktrees(self) -> List[Dict[str, Any]]:
        """List all active agent worktrees with status"""

        worktrees = []

        for agent_id, worktree in self.active_worktrees.items():
            # Check git status
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=worktree.worktree_path,
                    capture_output=True,
                    text=True,
                )

                modified_files = (
                    len(result.stdout.strip().split("\n"))
                    if result.stdout.strip()
                    else 0
                )

                worktrees.append(
                    {
                        "agent_id": agent_id,
                        "agent_type": worktree.agent_type,
                        "branch": worktree.branch_name,
                        "path": str(worktree.worktree_path),
                        "created": worktree.created_at.isoformat(),
                        "commits": len(worktree.commits),
                        "modified_files": modified_files,
                        "status": worktree.status,
                    }
                )
            except:
                worktree.status = "error"
                worktrees.append({"agent_id": agent_id, "status": "error"})

        return worktrees

    def get_shared_message_path(self, from_agent: str, to_agent: str = None) -> Path:
        """Get path for inter-agent messages"""

        if to_agent:
            return self.shared_space / "messages" / f"{from_agent}_to_{to_agent}.json"
        else:
            return self.shared_space / "messages" / f"{from_agent}_broadcast.json"

    def cleanup_all(self, force: bool = False):
        """Remove all worktrees and clean up"""

        for agent_id in list(self.active_worktrees.keys()):
            self.cleanup_worktree(agent_id, force=force)

        logger.info("All worktrees cleaned up")
