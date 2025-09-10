"""
Git worktree management for isolated agent execution.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Manages Git worktrees for isolated agent execution."""

    def __init__(
        self,
        base_path: Path = Path("/tmp/tetra_worktrees"),
        repo_path: Optional[Path] = None,
        cleanup_on_exit: bool = True,
    ):
        """
        Initialize worktree manager.

        Args:
            base_path: Base directory for worktrees
            repo_path: Path to main repository
            cleanup_on_exit: Whether to clean up worktrees on exit
        """
        self.base_path = Path(base_path)
        self.repo_path = repo_path or Path.cwd()
        self.cleanup_on_exit = cleanup_on_exit
        self.worktrees = {}

        # Create base directory
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create(self, task_id: str, branch: Optional[str] = None) -> Path:
        """
        Create a new worktree for a task.

        Args:
            task_id: Unique task identifier
            branch: Branch name (creates new if not exists)

        Returns:
            Path to worktree
        """
        worktree_path = self.base_path / task_id

        if worktree_path.exists():
            logger.warning(f"Worktree {worktree_path} already exists")
            return worktree_path

        branch = branch or f"tetra/{task_id}"

        try:
            # Create new branch and worktree
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, str(worktree_path)],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            self.worktrees[task_id] = worktree_path
            logger.info(f"Created worktree at {worktree_path} on branch {branch}")

        except subprocess.CalledProcessError as e:
            # Try without creating branch (if it exists)
            try:
                subprocess.run(
                    ["git", "worktree", "add", str(worktree_path), branch],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.worktrees[task_id] = worktree_path
                logger.info(f"Created worktree at {worktree_path} using existing branch {branch}")
            except subprocess.CalledProcessError:
                logger.error(f"Failed to create worktree: {e.stderr}")
                raise

        return worktree_path

    def cleanup(self, task_id: str) -> None:
        """
        Clean up a worktree.

        Args:
            task_id: Task identifier
        """
        if task_id not in self.worktrees:
            return

        worktree_path = self.worktrees[task_id]

        try:
            # Remove worktree
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            del self.worktrees[task_id]
            logger.info(f"Cleaned up worktree {worktree_path}")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to cleanup worktree: {e.stderr}")
            # Try manual cleanup
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)

    def cleanup_all(self) -> None:
        """Clean up all worktrees."""
        for task_id in list(self.worktrees.keys()):
            self.cleanup(task_id)

    def __del__(self):
        """Cleanup on deletion."""
        if self.cleanup_on_exit:
            self.cleanup_all()
