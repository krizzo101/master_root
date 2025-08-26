#!/usr/bin/env python3
"""
Git Safety Manager for Multi-Agent Operations
Provides checkpoint, rollback, and review capabilities for agent changes
"""

import hashlib
import json
import shutil
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SafetyLevel(Enum):
    """Safety levels for different operations"""

    LOW = "low"  # Documentation, comments
    MEDIUM = "medium"  # Refactoring, non-critical changes
    HIGH = "high"  # Core logic, API changes
    CRITICAL = "critical"  # Deletions, major restructuring


class GitSafetyManager:
    """Manages git operations and safety for multi-agent teams"""

    def __init__(self, project_root: Path = None):
        """Initialize safety manager"""
        self.project_root = project_root or Path.cwd()
        self.checkpoint_branch = None
        self.working_branch = None
        self.backup_dir = self.project_root / ".agent_backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Safety configuration
        self.config = {
            "auto_commit": True,
            "require_review": True,
            "max_file_changes": 100,
            "max_line_changes": 5000,
            "protected_paths": [
                ".git",
                ".env",
                "*.key",
                "*.pem",
                ".secrets",
                "credentials",
            ],
        }

        # Change tracking
        self.changes = []
        self.rollback_points = []

    def create_safety_checkpoint(self, session_name: str) -> str:
        """Create a safety checkpoint before agents start"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"checkpoint/{session_name}/{timestamp}"

        # Create checkpoint branch
        self._run_git(["checkout", "-b", checkpoint_name])
        self.checkpoint_branch = checkpoint_name

        # Create initial commit
        self._run_git(["add", "-A"])
        self._run_git(["commit", "-m", f"🛡️ Safety checkpoint: {session_name} started"])

        # Create working branch for agents
        working_branch = f"agents/{session_name}/{timestamp}"
        self._run_git(["checkout", "-b", working_branch])
        self.working_branch = working_branch

        # Record rollback point
        commit_hash = self._get_current_commit()
        self.rollback_points.append(
            {
                "point": "session_start",
                "commit": commit_hash,
                "branch": working_branch,
                "timestamp": datetime.now().isoformat(),
            }
        )

        print(f"✅ Safety checkpoint created: {checkpoint_name}")
        print(f"✅ Working branch: {working_branch}")

        return working_branch

    def validate_changes(self, phase: str) -> Tuple[bool, List[str]]:
        """Validate changes made by agents"""
        issues = []

        # Get current changes
        status = self._run_git(["status", "--porcelain"])
        changed_files = [line[3:] for line in status.splitlines()]

        # Check file count
        if len(changed_files) > self.config["max_file_changes"]:
            issues.append(
                f"Too many files changed: {len(changed_files)} > {self.config['max_file_changes']}"
            )

        # Check protected paths
        for file in changed_files:
            for protected in self.config["protected_paths"]:
                if protected.startswith("*"):
                    if file.endswith(protected[1:]):
                        issues.append(f"Protected file modified: {file}")
                elif protected in file:
                    issues.append(f"Protected path modified: {file}")

        # Check line changes
        diff_stat = self._run_git(["diff", "--stat"])
        if diff_stat:
            lines = diff_stat.split("\n")[-1] if diff_stat else ""
            if "insertions" in lines or "deletions" in lines:
                # Parse: "X files changed, Y insertions(+), Z deletions(-)"
                total_changes = 0
                parts = lines.split(",")
                for part in parts:
                    if "insertion" in part or "deletion" in part:
                        num = int("".join(filter(str.isdigit, part)) or 0)
                        total_changes += num

                if total_changes > self.config["max_line_changes"]:
                    issues.append(
                        f"Too many line changes: {total_changes} > {self.config['max_line_changes']}"
                    )

        # Check for dangerous operations
        dangerous_patterns = [
            ("rm -rf", "Dangerous deletion command"),
            ("DROP TABLE", "Database destruction"),
            ("DELETE FROM", "Mass deletion"),
            ("force push", "Force push detected"),
            ("--force", "Forced operation"),
        ]

        for file in changed_files:
            if file.endswith((".py", ".sh", ".sql", ".js")):
                try:
                    content = (self.project_root / file).read_text()
                    for pattern, message in dangerous_patterns:
                        if pattern.lower() in content.lower():
                            issues.append(f"{message} in {file}")
                except:
                    pass

        return len(issues) == 0, issues

    def commit_phase_changes(self, phase: str, agent: str, description: str) -> str:
        """Commit changes for a specific phase"""
        if not self.config["auto_commit"]:
            return None

        # Validate changes first
        valid, issues = self.validate_changes(phase)

        if not valid and self.config["require_review"]:
            print(f"⚠️  Validation issues found:")
            for issue in issues:
                print(f"   - {issue}")

            # Create quarantine branch
            quarantine = (
                f"quarantine/{phase}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self._run_git(["checkout", "-b", quarantine])

            # Commit for review
            self._run_git(["add", "-A"])
            self._run_git(
                [
                    "commit",
                    "-m",
                    f"⚠️ [NEEDS REVIEW] {phase}: {description}\n\nAgent: {agent}\nIssues:\n"
                    + "\n".join(issues),
                ]
            )

            print(f"🔒 Changes quarantined for review: {quarantine}")
            return quarantine

        # Commit changes
        self._run_git(["add", "-A"])
        commit_msg = f"🤖 [{phase}] {description}\n\nAgent: {agent}\nAuto-committed by Multi-Agent Monitor"
        self._run_git(["commit", "-m", commit_msg])

        # Record rollback point
        commit_hash = self._get_current_commit()
        self.rollback_points.append(
            {
                "point": f"phase_{phase}",
                "commit": commit_hash,
                "agent": agent,
                "timestamp": datetime.now().isoformat(),
            }
        )

        print(f"✅ Changes committed: {commit_hash[:8]} ({phase})")
        return commit_hash

    def create_backup(self, phase: str) -> Path:
        """Create file backup before changes"""
        backup_name = f"{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_name

        # Get list of tracked files
        tracked = self._run_git(["ls-files"])
        files = tracked.splitlines()

        # Create backup
        backup_path.mkdir(parents=True)
        for file in files:
            src = self.project_root / file
            if src.exists():
                dst = backup_path / file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Create backup manifest
        manifest = {
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "files": len(files),
            "commit": self._get_current_commit(),
        }

        with open(backup_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"📦 Backup created: {backup_path.name}")
        return backup_path

    def rollback_to_checkpoint(self, checkpoint: str = None) -> bool:
        """Rollback to a specific checkpoint"""
        if checkpoint is None and self.rollback_points:
            # Use last checkpoint
            checkpoint = self.rollback_points[-1]["commit"]

        if not checkpoint:
            print("❌ No checkpoint to rollback to")
            return False

        try:
            # Save current state first
            self._run_git(["stash", "push", "-m", "Pre-rollback stash"])

            # Rollback
            self._run_git(["reset", "--hard", checkpoint])

            print(f"✅ Rolled back to checkpoint: {checkpoint[:8]}")
            return True

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def generate_review_report(self) -> Dict:
        """Generate a review report of all changes"""
        report = {
            "session": self.working_branch,
            "checkpoint": self.checkpoint_branch,
            "timestamp": datetime.now().isoformat(),
            "changes": [],
            "statistics": {},
            "risks": [],
        }

        # Get diff statistics
        diff = self._run_git(
            ["diff", f"{self.checkpoint_branch}...{self.working_branch}", "--stat"]
        )
        report["statistics"]["diff"] = diff

        # Get changed files
        changed = self._run_git(
            ["diff", f"{self.checkpoint_branch}...{self.working_branch}", "--name-only"]
        )
        files = changed.splitlines()

        # Analyze each file
        for file in files:
            file_info = {"path": file, "type": Path(file).suffix, "changes": []}

            # Get specific changes
            file_diff = self._run_git(
                [
                    "diff",
                    f"{self.checkpoint_branch}...{self.working_branch}",
                    "--",
                    file,
                ]
            )

            # Count additions/deletions
            additions = len([l for l in file_diff.splitlines() if l.startswith("+")])
            deletions = len([l for l in file_diff.splitlines() if l.startswith("-")])

            file_info["additions"] = additions
            file_info["deletions"] = deletions

            # Check for risks
            if deletions > 100:
                report["risks"].append(f"Large deletion in {file}: {deletions} lines")

            if file.endswith((".env", ".key", ".pem")):
                report["risks"].append(f"Sensitive file modified: {file}")

            report["changes"].append(file_info)

        # Calculate totals
        report["statistics"]["total_files"] = len(files)
        report["statistics"]["total_additions"] = sum(
            f["additions"] for f in report["changes"]
        )
        report["statistics"]["total_deletions"] = sum(
            f["deletions"] for f in report["changes"]
        )
        report["statistics"]["risk_level"] = self._calculate_risk_level(report)

        return report

    def merge_to_main(self, review_passed: bool = False) -> bool:
        """Merge changes to main branch after review"""
        if not review_passed and self.config["require_review"]:
            print("❌ Review required before merge")
            return False

        try:
            # Switch to main/master
            main_branch = self._get_main_branch()
            self._run_git(["checkout", main_branch])

            # Merge working branch
            self._run_git(
                [
                    "merge",
                    self.working_branch,
                    "--no-ff",
                    "-m",
                    f"🔀 Merge multi-agent changes from {self.working_branch}",
                ]
            )

            print(f"✅ Changes merged to {main_branch}")

            # Clean up branches
            self._run_git(["branch", "-d", self.working_branch])
            self._run_git(["branch", "-d", self.checkpoint_branch])

            return True

        except Exception as e:
            print(f"❌ Merge failed: {e}")
            return False

    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output"""
        cmd = ["git"] + args
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"Git command failed: {' '.join(cmd)}\n{result.stderr}")

        return result.stdout.strip()

    def _get_current_commit(self) -> str:
        """Get current commit hash"""
        return self._run_git(["rev-parse", "HEAD"])

    def _get_main_branch(self) -> str:
        """Get name of main branch"""
        branches = self._run_git(["branch", "-a"])
        if "main" in branches:
            return "main"
        elif "master" in branches:
            return "master"
        else:
            # Get default branch from remote
            return self._run_git(["symbolic-ref", "refs/remotes/origin/HEAD"]).split(
                "/"
            )[-1]

    def _calculate_risk_level(self, report: Dict) -> str:
        """Calculate risk level from report"""
        risks = len(report["risks"])
        deletions = report["statistics"]["total_deletions"]

        if risks > 5 or deletions > 1000:
            return "CRITICAL"
        elif risks > 2 or deletions > 500:
            return "HIGH"
        elif risks > 0 or deletions > 100:
            return "MEDIUM"
        else:
            return "LOW"


class SafetyIntegration:
    """Integration with team orchestrator"""

    def __init__(self, orchestrator, safety_manager: GitSafetyManager):
        self.orchestrator = orchestrator
        self.safety = safety_manager

    async def safe_execute_workflow(
        self, project_name: str, requirements: str, dry_run: bool = False
    ) -> Dict:
        """Execute workflow with safety measures"""

        # Create safety checkpoint
        if not dry_run:
            self.safety.create_safety_checkpoint(project_name)

        # Create backup
        self.safety.create_backup("pre_workflow")

        try:
            # Execute workflow with phase commits
            result = await self._execute_with_commits(project_name, requirements)

            # Generate review report
            report = self.safety.generate_review_report()

            # Auto-review based on risk
            if report["statistics"]["risk_level"] in ["LOW", "MEDIUM"]:
                print(
                    f"✅ Auto-review passed (Risk: {report['statistics']['risk_level']})"
                )

                if not dry_run:
                    # Merge changes
                    self.safety.merge_to_main(review_passed=True)
            else:
                print(
                    f"⚠️  Manual review required (Risk: {report['statistics']['risk_level']})"
                )
                print(f"Review report saved to: review_{project_name}.json")

                with open(f"review_{project_name}.json", "w") as f:
                    json.dump(report, f, indent=2)

            return result

        except Exception as e:
            print(f"❌ Workflow failed: {e}")

            # Rollback on failure
            if not dry_run:
                self.safety.rollback_to_checkpoint()

            raise

    async def _execute_with_commits(self, project_name: str, requirements: str) -> Dict:
        """Execute workflow with automatic commits after each phase"""

        # Hook into orchestrator phases
        original_execute = self.orchestrator.execute_phase

        async def wrapped_execute(phase, agent):
            # Execute phase
            result = await original_execute(phase, agent)

            # Commit changes
            if result["success"]:
                self.safety.commit_phase_changes(
                    phase=phase.name,
                    agent=agent,
                    description=f"Completed {phase.name} phase",
                )

            return result

        # Temporarily replace method
        self.orchestrator.execute_phase = wrapped_execute

        try:
            # Execute workflow
            result = await self.orchestrator.execute_workflow(
                project_name, requirements
            )
            return result
        finally:
            # Restore original method
            self.orchestrator.execute_phase = original_execute


# CLI Interface
def main():
    """CLI for safety operations"""
    import sys

    if len(sys.argv) < 2:
        print(
            """
Git Safety Manager

Usage:
    python git_safety_manager.py checkpoint <name>    Create safety checkpoint
    python git_safety_manager.py rollback [commit]    Rollback to checkpoint
    python git_safety_manager.py review               Generate review report
    python git_safety_manager.py merge                Merge after review
    python git_safety_manager.py status              Show safety status
"""
        )
        return

    manager = GitSafetyManager()
    command = sys.argv[1]

    if command == "checkpoint":
        name = sys.argv[2] if len(sys.argv) > 2 else "manual"
        manager.create_safety_checkpoint(name)

    elif command == "rollback":
        commit = sys.argv[2] if len(sys.argv) > 2 else None
        manager.rollback_to_checkpoint(commit)

    elif command == "review":
        report = manager.generate_review_report()
        print(json.dumps(report, indent=2))

    elif command == "merge":
        manager.merge_to_main(review_passed=True)

    elif command == "status":
        print(f"Working branch: {manager.working_branch}")
        print(f"Checkpoint branch: {manager.checkpoint_branch}")
        print(f"Rollback points: {len(manager.rollback_points)}")


if __name__ == "__main__":
    main()
