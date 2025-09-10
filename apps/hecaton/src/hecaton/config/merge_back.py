"""
Merge-back configuration for HECATON
Handles patch integration from isolated worktrees back to main repo
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class MergeBackConfig:
    """Configuration for merge-back functionality"""

    # Core settings
    enabled: bool = True
    patch_dir: str = ".hecaton/patches"
    artifacts_dir: str = ".hecaton/artifacts"
    integration_prefix: str = "integration/"
    target_branch: str = "main"  # Default target branch

    # Merge behavior
    open_pr: bool = True
    land_direct: bool = False
    keep_worktrees: bool = False
    dry_run: bool = False

    # Patch ordering configuration
    path_order: List[str] = field(
        default_factory=lambda: ["docs", "tests", "src", "scripts", "migrations", "lockfiles"]
    )

    role_weight: Dict[str, int] = field(
        default_factory=lambda: {"review": 10, "docs": 20, "test": 30, "code": 40, "research": 15}
    )

    # Quality gates
    gate_commands: List[str] = field(
        default_factory=lambda: [
            "pre-commit run -a",
            "pytest -q --tb=short || true",  # Allow test failures to be reported
        ]
    )

    # Limits
    max_conflicts: int = 25
    max_patch_size_mb: float = 10.0

    # Git configuration
    git_author_name: str = "hecaton"
    git_author_email: str = "hecaton@local"

    def get_patch_path(self, run_id: str) -> Path:
        """Get path for patches directory for a run"""
        return Path(self.patch_dir) / run_id

    def get_artifacts_path(self, run_id: str) -> Path:
        """Get path for artifacts directory for a run"""
        return Path(self.artifacts_dir) / run_id

    def get_integration_branch(self, run_id: str) -> str:
        """Get integration branch name for a run"""
        return f"{self.integration_prefix}{run_id}"

    def validate(self) -> None:
        """Validate configuration"""
        if self.max_conflicts < 1:
            raise ValueError("max_conflicts must be at least 1")
        if self.max_patch_size_mb <= 0:
            raise ValueError("max_patch_size_mb must be positive")
        if not self.target_branch:
            raise ValueError("target_branch must be specified")
