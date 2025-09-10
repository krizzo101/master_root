"""
Merger module for HECATON - handles patch integration from agent worktrees
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..config.merge_back import MergeBackConfig
from ..resources.worktree import WorktreeManager

logger = logging.getLogger(__name__)


@dataclass
class PatchManifest:
    """Metadata for an exported patch"""

    patch_file: str
    agent_id: str
    agent_role: str
    commit_sha: str
    files_changed: List[str]
    insertions: int
    deletions: int
    task_hash: str
    run_id: str
    sequence: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatchManifest":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConflictReport:
    """Report for a conflicted patch"""

    patch_file: str
    agent_id: str
    conflicted_files: List[str]
    conflict_diff: str
    error_message: str


@dataclass
class GatesReport:
    """Report from quality gates execution"""

    success: bool
    passed_gates: List[str]
    failed_gates: List[Tuple[str, str]]  # (command, error_output)
    logs: str


class Merger:
    """Handles merging agent patches back to main repository"""

    def __init__(
        self, config: MergeBackConfig, worktree_manager: WorktreeManager, repo_path: Path = None
    ):
        """
        Initialize merger

        Args:
            config: Merge-back configuration
            worktree_manager: Worktree manager for creating staging worktrees
            repo_path: Path to main repository (defaults to cwd)
        """
        self.config = config
        self.worktree_manager = worktree_manager
        self.repo_path = Path(repo_path or os.getcwd())

    def prepare_staging(self, run_id: str, target_branch: str = None) -> Path:
        """
        Prepare staging worktree for integration

        Args:
            run_id: Run identifier
            target_branch: Target branch to integrate into

        Returns:
            Path to staging worktree
        """
        target = target_branch or self.config.target_branch
        integration_branch = self.config.get_integration_branch(run_id)

        logger.info(f"Preparing staging worktree for {integration_branch} from {target}")

        # Fetch latest changes
        subprocess.run(
            ["git", "fetch", "--all", "--prune"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Check if target branch exists
        try:
            # Try remote branch first
            subprocess.run(
                ["git", "rev-parse", f"origin/{target}"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )
            base_ref = f"origin/{target}"
        except subprocess.CalledProcessError:
            # Fall back to local branch
            subprocess.run(
                ["git", "rev-parse", target], cwd=self.repo_path, check=True, capture_output=True
            )
            base_ref = target

        # Create or reset integration branch
        subprocess.run(
            ["git", "checkout", "-B", integration_branch, base_ref],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        # Create staging worktree
        staging_path = self.worktree_manager.create(f"staging_{run_id}", branch=integration_branch)

        logger.info(f"Staging worktree created at {staging_path}")
        return staging_path

    def order_patches(
        self,
        manifests: List[PatchManifest],
        path_order: List[str] = None,
        role_weight: Dict[str, int] = None,
    ) -> List[PatchManifest]:
        """
        Order patches for deterministic application

        Args:
            manifests: List of patch manifests
            path_order: Path ordering (uses config default if None)
            role_weight: Role weights (uses config default if None)

        Returns:
            Ordered list of patch manifests
        """
        path_order = path_order or self.config.path_order
        role_weight = role_weight or self.config.role_weight

        def get_path_priority(manifest: PatchManifest) -> int:
            """Get priority based on file paths"""
            for i, path_prefix in enumerate(path_order):
                if any(f.startswith(path_prefix) for f in manifest.files_changed):
                    return i
            return len(path_order)  # Default priority for unmatched paths

        def get_role_priority(manifest: PatchManifest) -> int:
            """Get priority based on agent role"""
            return role_weight.get(manifest.agent_role, 50)

        # Sort by: path priority, then role weight, then sequence, then agent_id
        ordered = sorted(
            manifests,
            key=lambda m: (get_path_priority(m), get_role_priority(m), m.sequence, m.agent_id),
        )

        logger.info(f"Ordered {len(ordered)} patches for application")
        return ordered

    def apply_patches(
        self, staging_path: Path, ordered_patches: List[PatchManifest]
    ) -> Tuple[List[PatchManifest], List[ConflictReport]]:
        """
        Apply patches to staging worktree

        Args:
            staging_path: Path to staging worktree
            ordered_patches: Ordered list of patches to apply

        Returns:
            Tuple of (applied patches, conflict reports)
        """
        applied = []
        conflicts = []

        for manifest in ordered_patches:
            patch_path = Path(manifest.patch_file)

            if not patch_path.exists():
                logger.warning(f"Patch file not found: {patch_path}")
                continue

            logger.info(f"Applying patch from {manifest.agent_id} ({manifest.agent_role})")

            try:
                # Try to apply patch with 3-way merge
                result = subprocess.run(
                    ["git", "am", "--3way", "--keep-cr", str(patch_path)],
                    cwd=staging_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    applied.append(manifest)
                    logger.info(f"Successfully applied patch from {manifest.agent_id}")
                else:
                    # Conflict occurred
                    logger.warning(f"Conflict applying patch from {manifest.agent_id}")

                    # Get conflict details
                    conflict_files = self._get_conflict_files(staging_path)
                    conflict_diff = self._get_conflict_diff(staging_path, conflict_files)

                    # Abort the failed am
                    subprocess.run(["git", "am", "--abort"], cwd=staging_path, capture_output=True)

                    # Create conflict report
                    conflict = ConflictReport(
                        patch_file=str(patch_path),
                        agent_id=manifest.agent_id,
                        conflicted_files=conflict_files,
                        conflict_diff=conflict_diff,
                        error_message=result.stderr,
                    )
                    conflicts.append(conflict)

                    # Move patch to conflicts directory
                    conflicts_dir = Path(self.config.patch_dir) / manifest.run_id / "conflicts"
                    conflicts_dir.mkdir(parents=True, exist_ok=True)

                    conflict_patch = conflicts_dir / patch_path.name
                    patch_path.rename(conflict_patch)

            except Exception as e:
                logger.error(f"Error applying patch from {manifest.agent_id}: {e}")
                conflicts.append(
                    ConflictReport(
                        patch_file=str(patch_path),
                        agent_id=manifest.agent_id,
                        conflicted_files=[],
                        conflict_diff="",
                        error_message=str(e),
                    )
                )

        logger.info(f"Applied {len(applied)} patches, {len(conflicts)} conflicts")
        return applied, conflicts

    def run_gates(self, staging_path: Path, commands: List[str] = None) -> GatesReport:
        """
        Run quality gates on staging worktree

        Args:
            staging_path: Path to staging worktree
            commands: Gate commands to run (uses config default if None)

        Returns:
            Gates execution report
        """
        commands = commands or self.config.gate_commands
        passed = []
        failed = []
        all_logs = []

        for cmd in commands:
            logger.info(f"Running gate: {cmd}")
            all_logs.append(f"=== Running: {cmd} ===")

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,  # nosec B602 - Command is from trusted config
                    cwd=staging_path,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout per gate
                )

                all_logs.append(result.stdout)
                if result.stderr:
                    all_logs.append(f"STDERR: {result.stderr}")

                if result.returncode == 0:
                    passed.append(cmd)
                    logger.info(f"Gate passed: {cmd}")
                else:
                    failed.append((cmd, result.stderr or result.stdout))
                    logger.warning(f"Gate failed: {cmd}")

            except subprocess.TimeoutExpired:
                error_msg = "Gate timed out after 5 minutes"
                failed.append((cmd, error_msg))
                all_logs.append(error_msg)
                logger.error(f"Gate timed out: {cmd}")

            except Exception as e:
                error_msg = str(e)
                failed.append((cmd, error_msg))
                all_logs.append(f"ERROR: {error_msg}")
                logger.error(f"Gate error: {cmd} - {e}")

        return GatesReport(
            success=len(failed) == 0,
            passed_gates=passed,
            failed_gates=failed,
            logs="\n".join(all_logs),
        )

    def create_pr_or_land(
        self, staging_path: Path, run_id: str, pr_title: str = None, pr_body: str = None
    ) -> Dict[str, Any]:
        """
        Create PR or directly land changes

        Args:
            staging_path: Path to staging worktree
            run_id: Run identifier
            pr_title: PR title (auto-generated if None)
            pr_body: PR body (auto-generated if None)

        Returns:
            Result dictionary with PR URL or merge SHA
        """
        integration_branch = self.config.get_integration_branch(run_id)

        if self.config.dry_run:
            logger.info("DRY RUN: Skipping PR/merge")
            return {"dry_run": True, "integration_branch": integration_branch}

        # Push integration branch
        logger.info(f"Pushing {integration_branch}")
        subprocess.run(
            ["git", "push", "-u", "origin", integration_branch],
            cwd=staging_path,
            check=True,
            capture_output=True,
        )

        if self.config.land_direct:
            # Direct merge
            logger.info(f"Direct merging {integration_branch} to {self.config.target_branch}")

            subprocess.run(
                ["git", "checkout", self.config.target_branch],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
            )

            result = subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    integration_branch,
                    "-m",
                    f"Merge integration/{run_id} from HECATON",
                ],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Get merge commit SHA
            merge_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Push to remote
            subprocess.run(["git", "push"], cwd=self.repo_path, check=True, capture_output=True)

            return {"merged": True, "merge_sha": merge_sha}

        elif self.config.open_pr:
            # Create PR
            pr_title = pr_title or f"HECATON Integration: {run_id}"
            pr_body = pr_body or self._generate_pr_body(run_id)

            # Check if gh CLI is available
            try:
                subprocess.run(["gh", "--version"], check=True, capture_output=True)

                # Create PR using gh CLI
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--base",
                        self.config.target_branch,
                        "--head",
                        integration_branch,
                        "--title",
                        pr_title,
                        "--body",
                        pr_body,
                        "--label",
                        "hecaton",
                    ],
                    cwd=staging_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    pr_url = result.stdout.strip()
                    logger.info(f"Created PR: {pr_url}")
                    return {"pr_created": True, "pr_url": pr_url}
                else:
                    logger.warning(f"Failed to create PR: {result.stderr}")
                    return {
                        "pr_created": False,
                        "error": result.stderr,
                        "manual_pr_instructions": self._get_manual_pr_instructions(
                            integration_branch
                        ),
                    }

            except (subprocess.CalledProcessError, FileNotFoundError):
                # gh CLI not available
                logger.info("gh CLI not available, providing manual instructions")
                return {
                    "pr_created": False,
                    "manual_pr_instructions": self._get_manual_pr_instructions(integration_branch),
                }

        return {"no_action": True}

    def emit_reports(
        self,
        run_id: str,
        applied: List[PatchManifest],
        conflicts: List[ConflictReport],
        gates: GatesReport,
        pr_result: Dict[str, Any],
    ) -> Path:
        """
        Emit comprehensive reports and artifacts

        Args:
            run_id: Run identifier
            applied: Applied patches
            conflicts: Conflict reports
            gates: Gates report
            pr_result: PR/merge result

        Returns:
            Path to artifacts directory
        """
        artifacts_dir = self.config.get_artifacts_path(run_id)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Write manifest
        manifest_data = {
            "run_id": run_id,
            "patches": {
                "total": len(applied) + len(conflicts),
                "applied": len(applied),
                "conflicted": len(conflicts),
            },
            "applied_manifests": [vars(m) for m in applied],
            "target_branch": self.config.target_branch,
            "integration_branch": self.config.get_integration_branch(run_id),
        }

        with open(artifacts_dir / "manifest.json", "w") as f:
            json.dump(manifest_data, f, indent=2)

        # Write conflicts report
        if conflicts:
            conflicts_data = [
                {
                    "patch_file": c.patch_file,
                    "agent_id": c.agent_id,
                    "conflicted_files": c.conflicted_files,
                    "error": c.error_message,
                }
                for c in conflicts
            ]

            with open(artifacts_dir / "conflicts.json", "w") as f:
                json.dump(conflicts_data, f, indent=2)

            # Human-readable conflicts report
            with open(artifacts_dir / "conflicts.md", "w") as f:
                f.write("# Merge Conflicts Report\n\n")
                for c in conflicts:
                    f.write(f"## Agent: {c.agent_id}\n")
                    f.write(f"**Patch:** {c.patch_file}\n")
                    f.write(f"**Files:** {', '.join(c.conflicted_files)}\n")
                    if c.conflict_diff:
                        f.write(f"```diff\n{c.conflict_diff}\n```\n")
                    f.write("\n")

        # Write gates report
        gates_data = {
            "success": gates.success,
            "passed": gates.passed_gates,
            "failed": [{"command": cmd, "error": err} for cmd, err in gates.failed_gates],
        }

        with open(artifacts_dir / "gates.json", "w") as f:
            json.dump(gates_data, f, indent=2)

        with open(artifacts_dir / "gates.md", "w") as f:
            f.write("# Quality Gates Report\n\n")
            f.write(f"**Status:** {'✅ PASSED' if gates.success else '❌ FAILED'}\n\n")

            if gates.passed_gates:
                f.write("## Passed Gates\n")
                for cmd in gates.passed_gates:
                    f.write(f"- ✅ `{cmd}`\n")
                f.write("\n")

            if gates.failed_gates:
                f.write("## Failed Gates\n")
                for cmd, err in gates.failed_gates:
                    f.write(f"- ❌ `{cmd}`\n")
                    if err:
                        f.write(f"  ```\n  {err}\n  ```\n")
                f.write("\n")

        # Write integration log
        with open(artifacts_dir / "integration.log", "w") as f:
            f.write(gates.logs)

        # Write run summary
        summary = {
            "run_id": run_id,
            "timestamp": str(Path.ctime(artifacts_dir)),
            "config": {
                "target_branch": self.config.target_branch,
                "dry_run": self.config.dry_run,
                "land_direct": self.config.land_direct,
            },
            "results": {
                "patches_applied": len(applied),
                "conflicts": len(conflicts),
                "gates_passed": gates.success,
                "pr_result": pr_result,
            },
        }

        summary_file = artifacts_dir / f"hecaton_run_{run_id}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Reports written to {artifacts_dir}")
        return artifacts_dir

    def _get_conflict_files(self, staging_path: Path) -> List[str]:
        """Get list of conflicted files"""
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            cwd=staging_path,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().split("\n") if result.stdout else []

    def _get_conflict_diff(self, staging_path: Path, files: List[str]) -> str:
        """Get conflict diff for files"""
        if not files:
            return ""

        diffs = []
        for file in files[:5]:  # Limit to first 5 files
            result = subprocess.run(
                ["git", "diff", "--unified=3", file],
                cwd=staging_path,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                diffs.append(f"=== {file} ===\n{result.stdout}")

        return "\n".join(diffs)

    def _generate_pr_body(self, run_id: str) -> str:
        """Generate PR body"""
        return f"""## HECATON Integration Run: {run_id}

This PR contains merged changes from parallel agent execution.

### Integration Details
- **Run ID:** {run_id}
- **Target Branch:** {self.config.target_branch}
- **Integration Branch:** {self.config.get_integration_branch(run_id)}

### Artifacts
Check `.hecaton/artifacts/{run_id}/` for detailed reports.

---
*Generated by HECATON Multi-Agent Orchestration System*
"""

    def _get_manual_pr_instructions(self, integration_branch: str) -> str:
        """Get manual PR creation instructions"""
        return f"""
To create a PR manually:

1. Visit your repository on GitHub
2. Go to Pull Requests → New Pull Request
3. Set base branch: {self.config.target_branch}
4. Set compare branch: {integration_branch}
5. Add title: "HECATON Integration: [run_id]"
6. Add label: "hecaton"
7. Create the PR

Or use the GitHub CLI:
```bash
gh pr create --base {self.config.target_branch} --head {integration_branch} \
  --title "HECATON Integration" --label hecaton
```
"""
