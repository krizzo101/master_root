#!/usr/bin/env python3
"""
Safe Multi-Agent Orchestrator
Wraps the team orchestrator with comprehensive safety features
"""

import asyncio
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..orchestration.enhanced_orchestrator import EnhancedOrchestrator
from ..orchestration.team_orchestrator import AgentTeamOrchestrator, ProjectType
from .git_safety_manager import GitSafetyManager, SafetyLevel


class ExecutionMode(Enum):
    """Execution modes for safety"""

    DRY_RUN = "dry_run"  # Preview changes without executing
    SAFE = "safe"  # Execute with all safety features
    REVIEW = "review"  # Execute with mandatory review
    EMERGENCY = "emergency"  # Bypass safety for urgent fixes


class SafeOrchestrator:
    """Safe wrapper for multi-agent orchestration"""

    def __init__(self, project_root: Path = None):
        """Initialize safe orchestrator"""
        self.project_root = project_root or Path.cwd()
        self.safety_manager = GitSafetyManager(self.project_root)
        self.orchestrator = AgentTeamOrchestrator()

        # Safety configuration
        self.safety_config = {
            "mode": ExecutionMode.SAFE,
            "max_agents": 15,
            "require_approval": True,
            "auto_rollback_on_error": True,
            "create_pr": True,
            "protected_branches": ["main", "master", "production"],
            "change_limits": {
                SafetyLevel.LOW: {"files": 50, "lines": 2000},
                SafetyLevel.MEDIUM: {"files": 30, "lines": 1000},
                SafetyLevel.HIGH: {"files": 10, "lines": 500},
                SafetyLevel.CRITICAL: {"files": 5, "lines": 100},
            },
        }

        # Execution tracking
        self.execution_log = []
        self.change_preview = None

    async def safe_execute(
        self,
        project_name: str,
        project_type: ProjectType,
        requirements: str,
        mode: ExecutionMode = ExecutionMode.SAFE,
        safety_level: SafetyLevel = SafetyLevel.MEDIUM,
        phases: List[str] = None,
    ) -> Dict[str, Any]:
        """Execute multi-agent workflow with safety features"""

        print(
            f"""
╔══════════════════════════════════════════════════════════════╗
║              SAFE MULTI-AGENT EXECUTION                      ║
╚══════════════════════════════════════════════════════════════╝

Project: {project_name}
Type: {project_type.value}
Mode: {mode.value}
Safety Level: {safety_level.value}
"""
        )

        # Pre-flight checks
        if not await self._pre_flight_checks(safety_level):
            return {"success": False, "error": "Pre-flight checks failed"}

        # Create safety checkpoint
        if mode != ExecutionMode.DRY_RUN:
            branch_name = self.safety_manager.create_safety_checkpoint(project_name)
            print(f"✅ Working on branch: {branch_name}")

        try:
            # Execute based on mode
            if mode == ExecutionMode.DRY_RUN:
                result = await self._dry_run_execution(
                    project_name, project_type, requirements, phases
                )
            elif mode == ExecutionMode.SAFE:
                result = await self._safe_execution(
                    project_name, project_type, requirements, safety_level, phases
                )
            elif mode == ExecutionMode.REVIEW:
                result = await self._review_execution(
                    project_name, project_type, requirements, safety_level, phases
                )
            elif mode == ExecutionMode.EMERGENCY:
                result = await self._emergency_execution(
                    project_name, project_type, requirements, phases
                )
            else:
                raise ValueError(f"Unknown mode: {mode}")

            # Post-execution review
            if result["success"] and mode != ExecutionMode.DRY_RUN:
                await self._post_execution_review(project_name, safety_level)

            return result

        except Exception as e:
            print(f"❌ Execution failed: {e}")

            # Auto-rollback if configured
            if (
                self.safety_config["auto_rollback_on_error"]
                and mode != ExecutionMode.DRY_RUN
            ):
                print("🔄 Auto-rollback initiated...")
                self.safety_manager.rollback_to_checkpoint()

            return {"success": False, "error": str(e)}

    async def _pre_flight_checks(self, safety_level: SafetyLevel) -> bool:
        """Perform pre-flight safety checks"""
        print("\n📋 Pre-flight Safety Checks:")
        checks_passed = True

        # Check git status
        try:
            status = self.safety_manager._run_git(["status", "--porcelain"])
            if status:
                print("   ⚠️  Uncommitted changes detected")
                print("      Run 'git stash' or commit changes first")
                checks_passed = False
            else:
                print("   ✅ Working directory clean")
        except:
            print("   ❌ Not a git repository")
            checks_passed = False

        # Check current branch
        try:
            branch = self.safety_manager._run_git(["branch", "--show-current"])
            if branch in self.safety_config["protected_branches"]:
                print(f"   ❌ On protected branch: {branch}")
                checks_passed = False
            else:
                print(f"   ✅ Current branch: {branch}")
        except:
            pass

        # Check token availability
        from ..orchestration.secrets_manager import TokenSecretsManager

        token_manager = TokenSecretsManager()
        tokens = token_manager.list_tokens()

        if len(tokens) < 1:
            print("   ❌ No Claude Code tokens available")
            checks_passed = False
        else:
            print(f"   ✅ {len(tokens)} tokens available")

        # Check disk space
        import shutil

        usage = shutil.disk_usage(self.project_root)
        free_gb = usage.free / (1024**3)

        if free_gb < 1:
            print(f"   ⚠️  Low disk space: {free_gb:.2f} GB")
        else:
            print(f"   ✅ Disk space: {free_gb:.2f} GB free")

        return checks_passed

    async def _dry_run_execution(
        self,
        project_name: str,
        project_type: ProjectType,
        requirements: str,
        phases: List[str],
    ) -> Dict:
        """Execute in dry-run mode (preview only)"""
        print("\n🔍 DRY RUN MODE - No changes will be made")

        # Create preview
        preview = {
            "project": project_name,
            "type": project_type.value,
            "phases": phases or "all",
            "estimated_agents": self._estimate_agents(project_type),
            "estimated_time": self._estimate_time(project_type),
            "planned_changes": [],
        }

        # Simulate workflow
        workflow = self._get_workflow_template(project_type)

        for phase in workflow["phases"]:
            phase_preview = {
                "phase": phase["name"],
                "agents": phase.get("agents", []),
                "deliverables": phase.get("deliverables", []),
                "estimated_duration": phase.get("duration", "unknown"),
            }
            preview["planned_changes"].append(phase_preview)

        # Show preview
        print("\n📊 Execution Preview:")
        print(json.dumps(preview, indent=2))

        self.change_preview = preview

        return {"success": True, "mode": "dry_run", "preview": preview}

    async def _safe_execution(
        self,
        project_name: str,
        project_type: ProjectType,
        requirements: str,
        safety_level: SafetyLevel,
        phases: List[str],
    ) -> Dict:
        """Execute with safety features"""
        print(f"\n🛡️ SAFE MODE - Safety level: {safety_level.value}")

        # Set change limits based on safety level
        limits = self.safety_config["change_limits"][safety_level]
        self.safety_manager.config["max_file_changes"] = limits["files"]
        self.safety_manager.config["max_line_changes"] = limits["lines"]

        # Create backup
        backup_path = self.safety_manager.create_backup(f"{project_name}_start")

        # Execute with phase commits
        results = []

        for phase in phases or self._get_workflow_template(project_type)["phases"]:
            print(f"\n🚀 Executing phase: {phase}")

            # Execute phase
            phase_result = await self._execute_phase_safely(
                project_name, project_type, phase, requirements, safety_level
            )

            results.append(phase_result)

            # Check for errors
            if not phase_result["success"]:
                print(f"❌ Phase {phase} failed")

                if self.safety_config["auto_rollback_on_error"]:
                    print("🔄 Rolling back...")
                    self.safety_manager.rollback_to_checkpoint()

                break

            # Validate and commit
            valid, issues = self.safety_manager.validate_changes(phase)

            if valid:
                commit = self.safety_manager.commit_phase_changes(
                    phase=phase,
                    agent=phase_result.get("agent", "unknown"),
                    description=f"Completed {phase}",
                )
                print(f"✅ Phase committed: {commit[:8]}")
            else:
                print(f"⚠️  Validation issues in {phase}:")
                for issue in issues:
                    print(f"   - {issue}")

                if safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
                    print("❌ Stopping due to validation issues")
                    break

        return {
            "success": all(r["success"] for r in results),
            "mode": "safe",
            "results": results,
            "backup": str(backup_path),
        }

    async def _review_execution(
        self,
        project_name: str,
        project_type: ProjectType,
        requirements: str,
        safety_level: SafetyLevel,
        phases: List[str],
    ) -> Dict:
        """Execute with mandatory review"""
        print("\n👀 REVIEW MODE - All changes require approval")

        # Execute in safe mode first
        result = await self._safe_execution(
            project_name, project_type, requirements, safety_level, phases
        )

        if result["success"]:
            # Generate review report
            report = self.safety_manager.generate_review_report()

            # Save report
            report_path = Path(
                f"review_{project_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)

            print(f"\n📝 Review Report Generated: {report_path}")
            print(f"   Files changed: {report['statistics']['total_files']}")
            print(f"   Lines added: {report['statistics']['total_additions']}")
            print(f"   Lines removed: {report['statistics']['total_deletions']}")
            print(f"   Risk level: {report['statistics']['risk_level']}")

            if report["risks"]:
                print("\n⚠️  Risks Identified:")
                for risk in report["risks"]:
                    print(f"   - {risk}")

            # Create pull request if configured
            if self.safety_config["create_pr"]:
                pr_created = await self._create_pull_request(project_name, report)
                if pr_created:
                    print(f"✅ Pull request created for review")

            result["review_required"] = True
            result["report"] = str(report_path)

        return result

    async def _emergency_execution(
        self,
        project_name: str,
        project_type: ProjectType,
        requirements: str,
        phases: List[str],
    ) -> Dict:
        """Emergency execution with minimal safety"""
        print("\n🚨 EMERGENCY MODE - Reduced safety checks")
        print("   ⚠️  Use only for urgent fixes!")

        # Still create a checkpoint
        self.safety_manager.create_safety_checkpoint(f"emergency_{project_name}")

        # Execute with minimal checks
        result = await self.orchestrator.execute_workflow(
            project_name=project_name, requirements=requirements
        )

        # Single commit at end
        if result.get("success"):
            self.safety_manager._run_git(["add", "-A"])
            self.safety_manager._run_git(
                ["commit", "-m", f"🚨 Emergency fix: {project_name}"]
            )

        return result

    async def _execute_phase_safely(
        self,
        project_name: str,
        project_type: ProjectType,
        phase: str,
        requirements: str,
        safety_level: SafetyLevel,
    ) -> Dict:
        """Execute a single phase with safety checks"""

        # TODO: Integrate with actual orchestrator
        # This is a placeholder for the actual execution

        return {
            "success": True,
            "phase": phase,
            "agent": f"agent_{phase}",
            "changes": [],
        }

    async def _post_execution_review(
        self, project_name: str, safety_level: SafetyLevel
    ) -> None:
        """Post-execution review and cleanup"""
        print("\n📊 Post-Execution Review:")

        # Generate final report
        report = self.safety_manager.generate_review_report()

        # Auto-merge for low risk
        if (
            report["statistics"]["risk_level"] == "LOW"
            and safety_level == SafetyLevel.LOW
        ):
            print("✅ Auto-merging (low risk changes)")
            self.safety_manager.merge_to_main(review_passed=True)
        else:
            print(f"📝 Review required (Risk: {report['statistics']['risk_level']})")
            print(f"   Run: python git_safety_manager.py review")
            print(f"   Then: python git_safety_manager.py merge")

    async def _create_pull_request(self, project_name: str, report: Dict) -> bool:
        """Create a pull request for review"""
        try:
            # Get branch names
            current = self.safety_manager.working_branch
            target = self.safety_manager._get_main_branch()

            # Create PR description
            description = f"""
## Multi-Agent Execution: {project_name}

### Summary
- Files changed: {report['statistics']['total_files']}
- Lines added: {report['statistics']['total_additions']}
- Lines removed: {report['statistics']['total_deletions']}
- Risk level: {report['statistics']['risk_level']}

### Changes
{self._format_changes_summary(report['changes'])}

### Risks
{self._format_risks(report['risks'])}

---
Generated by Multi-Agent Monitor
"""

            # Try GitHub CLI if available
            try:
                self.safety_manager._run_git(
                    [
                        "gh",
                        "pr",
                        "create",
                        "--title",
                        f"[Multi-Agent] {project_name}",
                        "--body",
                        description,
                        "--base",
                        target,
                        "--head",
                        current,
                    ]
                )
                return True
            except:
                print("   ℹ️  GitHub CLI not available, PR must be created manually")
                return False

        except Exception as e:
            print(f"   ⚠️  Could not create PR: {e}")
            return False

    def _get_workflow_template(self, project_type: ProjectType) -> Dict:
        """Get workflow template for project type"""
        # Simplified template - should load from YAML
        templates = {
            ProjectType.WEB_APP: {
                "phases": [
                    {"name": "discovery", "agents": ["requirements-analyst"]},
                    {"name": "design", "agents": ["solution-architect"]},
                    {"name": "development", "agents": ["development-specialist"]},
                    {"name": "testing", "agents": ["qa-testing-guru"]},
                ]
            },
            ProjectType.REFACTORING: {
                "phases": [
                    {"name": "analysis", "agents": ["code-analyzer"]},
                    {"name": "planning", "agents": ["refactoring-master"]},
                    {"name": "refactoring", "agents": ["refactoring-master"]},
                    {"name": "validation", "agents": ["qa-testing-guru"]},
                ]
            },
        }

        return templates.get(project_type, templates[ProjectType.WEB_APP])

    def _estimate_agents(self, project_type: ProjectType) -> int:
        """Estimate number of agents for project type"""
        estimates = {
            ProjectType.WEB_APP: 15,
            ProjectType.MICROSERVICES: 10,
            ProjectType.REFACTORING: 8,
            ProjectType.DOCUMENTATION: 3,
        }
        return estimates.get(project_type, 5)

    def _estimate_time(self, project_type: ProjectType) -> str:
        """Estimate execution time"""
        estimates = {
            ProjectType.WEB_APP: "2-3 hours",
            ProjectType.MICROSERVICES: "1-2 hours",
            ProjectType.REFACTORING: "1-2 hours",
            ProjectType.DOCUMENTATION: "30-60 minutes",
        }
        return estimates.get(project_type, "1-2 hours")

    def _format_changes_summary(self, changes: List[Dict]) -> str:
        """Format changes for PR description"""
        if not changes:
            return "No changes"

        summary = []
        for change in changes[:10]:  # Limit to 10
            summary.append(
                f"- `{change['path']}`: +{change['additions']}/-{change['deletions']}"
            )

        if len(changes) > 10:
            summary.append(f"- ... and {len(changes) - 10} more files")

        return "\n".join(summary)

    def _format_risks(self, risks: List[str]) -> str:
        """Format risks for PR description"""
        if not risks:
            return "No risks identified"

        return "\n".join(f"- ⚠️  {risk}" for risk in risks)
