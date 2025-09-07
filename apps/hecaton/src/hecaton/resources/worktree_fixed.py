"""
Fixed Git Worktree Manager for HECATON
Handles worktrees outside the main repo directory properly
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..utils.debug_logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorktreeInfo:
    """Information about an active worktree"""

    worktree_path: Path
    branch_name: str
    created_at: datetime


class WorktreeManager:
    """
    Manages isolated git worktrees for parallel agent execution.
    Fixed version that handles external worktree directories properly.
    """

    def __init__(self, base_path: Optional[Path] = None, repo_path: Optional[Path] = None):
        """
        Initialize worktree manager

        Args:
            base_path: Base directory for worktrees (can be outside repo)
            repo_path: Path to the main git repository
        """
        if base_path is None:
            base_path = Path("/home/opsvi/hecaton_worktrees")
        if repo_path is None:
            repo_path = Path("/home/opsvi/master_root")

        self.base_path = Path(base_path)
        self.repo_path = Path(repo_path)
        self.active_worktrees: Dict[str, WorktreeInfo] = {}

        # Create base directory if needed
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"WorktreeManager initialized at {self.base_path}")
        logger.debug_data("repo_path", str(self.repo_path))

    def create(self, agent_id: str) -> Path:
        """
        Create a new worktree for an agent

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Path to the created worktree
        """
        logger.debug_enter("create", agent_id=agent_id)

        # Generate unique worktree name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worktree_name = f"{agent_id}_{timestamp}"
        worktree_path = self.base_path / worktree_name

        # Generate branch name
        branch_name = f"hecaton/{timestamp}/{agent_id}"

        logger.debug_step(f"Creating worktree: {worktree_path}")
        logger.debug_data("branch_name", branch_name)

        try:
            # Check if branch exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            if result.returncode == 0:
                # Branch exists, use it
                logger.debug_step("Branch exists, using existing branch")
                cmd = ["git", "worktree", "add", str(worktree_path), branch_name]
            else:
                # Create new branch
                logger.debug_step("Creating new branch")
                cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path)]

            # Create worktree
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, check=True
            )

            # Store worktree info
            self.active_worktrees[agent_id] = WorktreeInfo(
                worktree_path=worktree_path, branch_name=branch_name, created_at=datetime.now()
            )

            logger.info(f"Created worktree for {agent_id} at {worktree_path}")
            logger.debug_exit("create", result=str(worktree_path))
            return worktree_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e}")
            logger.debug_data("stderr", e.stderr if hasattr(e, "stderr") else "")
            raise

    def cleanup(self, agent_id: str, force: bool = True):
        """
        Clean up a worktree after agent completion.
        Fixed to handle external worktree directories properly.

        Args:
            agent_id: Agent identifier
            force: Force removal even if there are changes
        """
        logger.debug_enter("cleanup", agent_id=agent_id, force=force)

        if agent_id not in self.active_worktrees:
            logger.warning(f"No worktree found for agent {agent_id}")
            return

        worktree = self.active_worktrees[agent_id]

        try:
            # First, try to remove worktree normally
            cmd = ["git", "worktree", "remove", str(worktree.worktree_path)]
            if force:
                cmd.append("--force")

            logger.debug_step(f"Removing worktree: {' '.join(cmd)}")

            result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                logger.warning(f"Worktree removal failed: {result.stderr}")

                # Try to prune worktrees first
                logger.debug_step("Pruning worktrees")
                subprocess.run(
                    ["git", "worktree", "prune"], cwd=self.repo_path, capture_output=True
                )

                # If directory still exists, remove it manually
                if worktree.worktree_path.exists():
                    logger.debug_step("Manually removing worktree directory")
                    import shutil

                    shutil.rmtree(worktree.worktree_path, ignore_errors=True)

            # Try to delete branch (don't fail if it doesn't work)
            try:
                logger.debug_step(f"Deleting branch: {worktree.branch_name}")
                subprocess.run(
                    ["git", "branch", "-D", worktree.branch_name],
                    cwd=self.repo_path,
                    capture_output=True,
                    timeout=5,
                )
            except:
                logger.debug_step("Branch deletion failed (non-critical)")

            # Remove from registry
            del self.active_worktrees[agent_id]

            logger.info(f"Cleaned up worktree for {agent_id}")
            logger.debug_exit("cleanup", result="success")

        except Exception as e:
            # Log but don't fail - cleanup errors are non-critical
            logger.warning(f"Failed to cleanup worktree: {e}")
            logger.debug_error(e, "cleanup")

            # Still remove from registry
            if agent_id in self.active_worktrees:
                del self.active_worktrees[agent_id]

    def cleanup_all(self, force: bool = True):
        """Clean up all active worktrees"""
        logger.debug_enter("cleanup_all", force=force)

        agents = list(self.active_worktrees.keys())
        for agent_id in agents:
            self.cleanup(agent_id, force=force)

        logger.debug_exit("cleanup_all")

    def get_worktree_path(self, agent_id: str) -> Optional[Path]:
        """Get the worktree path for an agent"""
        if agent_id in self.active_worktrees:
            return self.active_worktrees[agent_id].worktree_path
        return None

    def list_active_worktrees(self) -> Dict[str, Dict]:
        """List all active worktrees"""
        result = {}
        for agent_id, info in self.active_worktrees.items():
            result[agent_id] = {
                "path": str(info.worktree_path),
                "branch": info.branch_name,
                "created_at": info.created_at.isoformat(),
            }
        return result
