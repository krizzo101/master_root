"""
Agent Supervisor - Orchestrates agents with quality control
Monitors agent actions, validates outputs, and manages approvals
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agent_quality_control import (
    ActionType,
    AgentAction,
    AgentQualityControl,
    QualityStatus,
)
from .post_merge_quality import PostMergeQuality
from .selective_merger import SelectiveMerger
from .worktree_manager import WorktreeManager

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Definition of a task for an agent"""

    agent_type: str
    task_description: str
    requirements: Dict[str, Any]
    max_execution_time: int = 300  # seconds
    auto_approve: bool = False
    critical: bool = False  # If True, failure blocks pipeline


class AgentSupervisor:
    """
    Supervises multi-agent execution with quality control.
    Ensures agent outputs meet standards before proceeding.
    """

    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path("/home/opsvi/master_root")
        self.worktree_manager = WorktreeManager(self.repo_path)
        self.merger = SelectiveMerger(self.repo_path)
        self.quality_control = AgentQualityControl(self.repo_path)
        self.post_merge_quality = PostMergeQuality(self.repo_path)

        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_log = []

    def define_agent_task(
        self,
        agent_type: str,
        task_description: str,
        required_files: List[str] = None,
        content_checks: List[Dict] = None,
        max_file_changes: int = 10,
        auto_approve: bool = False,
        critical: bool = False,
    ) -> AgentTask:
        """
        Define a task with requirements for an agent.

        Args:
            agent_type: Type of agent
            task_description: What the agent should do
            required_files: Files that must be created
            content_checks: Content validation rules
            max_file_changes: Maximum allowed file changes
            auto_approve: Allow auto-approval if quality is high
            critical: Whether failure should block pipeline

        Returns:
            AgentTask with requirements
        """

        requirements = {
            "required_files": required_files or [],
            "content_checks": content_checks or [],
            "max_file_changes": max_file_changes,
        }

        return AgentTask(
            agent_type=agent_type,
            task_description=task_description,
            requirements=requirements,
            auto_approve=auto_approve,
            critical=critical,
        )

    async def execute_agent_with_supervision(
        self,
        agent_id: str,
        agent_task: AgentTask,
        worktree_path: Path,
        workspace_path: Path,
    ) -> Dict:
        """
        Execute an agent with full supervision and quality control.

        Returns:
            Execution report with status and metrics
        """

        print(f"\n🤖 Executing {agent_task.agent_type} with supervision...")

        # Track actions (in real implementation, agent would report these)
        # For now, we'll simulate based on file creation

        # Simulate agent execution (replace with real agent execution)
        success = await self._simulate_agent_execution(agent_task, workspace_path)

        # Register agent actions
        created_files = list(workspace_path.glob("*.*"))
        for file_path in created_files:
            if file_path.name != "agent_info.json":
                # Determine action type
                action = AgentAction(
                    agent_id=agent_id,
                    agent_type=agent_task.agent_type,
                    action_type=ActionType.FILE_CREATE,
                    description=f"Created {file_path.name}",
                    file_path=file_path,
                    content_preview=file_path.read_text()[:500]
                    if file_path.suffix in [".py", ".md", ".txt"]
                    else None,
                    risk_level="low"
                    if file_path.suffix in [".md", ".txt"]
                    else "medium",
                )
                self.quality_control.register_agent_action(action)

        # Review output quality
        status, reason = self.quality_control.review_agent_output(
            agent_id=agent_id,
            worktree_path=worktree_path,
            task_requirements=agent_task.requirements,
        )

        # Validate task completion
        validation = self.quality_control.validate_agent_task(
            agent_id=agent_id, task_requirements=agent_task.requirements
        )

        # Build execution report
        report = {
            "agent_id": agent_id,
            "agent_type": agent_task.agent_type,
            "execution_time": datetime.now().isoformat(),
            "quality_status": status.value,
            "quality_reason": reason,
            "validation": validation,
            "files_created": len(created_files),
            "requires_human_approval": False,
            "approved_for_merge": False,
        }

        # Check if human approval needed
        if not agent_task.auto_approve or status == QualityStatus.REVIEWING:
            report[
                "requires_human_approval"
            ] = self.quality_control.require_human_approval(agent_id)

        # Determine if approved for merge
        if status in [QualityStatus.APPROVED, QualityStatus.AUTO_APPROVED]:
            report["approved_for_merge"] = True
        elif status == QualityStatus.NEEDS_REVISION:
            print(f"   ⚠️  Agent needs to revise output: {reason}")
            if agent_task.critical:
                print(f"   ❌ CRITICAL task failed - blocking pipeline")
                report["pipeline_blocked"] = True

        # Stage and commit if approved
        if report["approved_for_merge"] and not report["requires_human_approval"]:
            try:
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=worktree_path,
                    check=True,
                    capture_output=True,
                )

                commit_result = subprocess.run(
                    [
                        "git",
                        "commit",
                        "--no-verify",
                        "-m",
                        f"feat({agent_task.agent_type}): {agent_task.task_description[:50]}",
                    ],
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                )

                if commit_result.returncode == 0:
                    commit_hash = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=worktree_path,
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.strip()[:8]

                    report["commit"] = commit_hash
                    print(f"   ✅ Approved and committed: {commit_hash}")

            except subprocess.CalledProcessError as e:
                logger.error(f"Commit failed: {e}")

        # Log execution
        self.execution_log.append(report)

        return report

    async def _simulate_agent_execution(
        self, agent_task: AgentTask, workspace_path: Path
    ) -> bool:
        """
        Simulate agent execution for testing.
        In production, this would call actual agent.
        """

        workspace_path.mkdir(parents=True, exist_ok=True)

        # Create files based on agent type
        if agent_task.agent_type == "requirements":
            content = f"""# Requirements Document
## Task: {agent_task.task_description}

### Functional Requirements:
- User authentication required
- Data validation must be implemented
- Error handling for all edge cases

### Non-Functional Requirements:
- Response time < 200ms
- Support 1000 concurrent users
- 99.9% uptime SLA

Generated at: {datetime.now().isoformat()}
"""
            (workspace_path / "requirements.md").write_text(content)

        elif agent_task.agent_type == "developer":
            content = '''"""Implementation based on requirements"""

def process_data(data):
    """Process incoming data with validation"""
    if not data:
        raise ValueError("Data cannot be empty")

    # Process data
    result = {"processed": True, "data": data}
    return result

def validate_input(input_data):
    """Validate input data"""
    required_fields = ["id", "name", "value"]

    for field in required_fields:
        if field not in input_data:
            raise KeyError(f"Missing required field: {field}")

    return True
'''
            (workspace_path / "implementation.py").write_text(content)

            # Also create a test file
            test_content = '''"""Tests for implementation"""
import unittest

def test_process_data():
    """Test data processing"""
    result = {"processed": True, "data": "test"}
    assert result["processed"] == True
    print("✓ Test passed")

if __name__ == "__main__":
    test_process_data()
'''
            (workspace_path / "test_implementation.py").write_text(test_content)

        elif agent_task.agent_type == "reviewer":
            content = f"""# Code Review Report

## Review Date: {datetime.now().isoformat()}
## Status: APPROVED

### Strengths:
- Good error handling
- Clear function documentation
- Follows coding standards

### Suggestions:
- Consider adding type hints
- Could benefit from more comprehensive tests
- Add logging for debugging

### Security Review:
- No hardcoded credentials found ✓
- Input validation present ✓
- No SQL injection vulnerabilities ✓

Overall Score: 85/100
"""
            (workspace_path / "review_report.md").write_text(content)

        return True

    async def run_supervised_agents(
        self,
        agent_tasks: List[AgentTask],
        parallel: bool = True,
        stop_on_failure: bool = False,
    ) -> Dict:
        """
        Run multiple agents with supervision and quality control.

        Args:
            agent_tasks: List of tasks for agents
            parallel: Execute agents in parallel if True
            stop_on_failure: Stop execution if any critical task fails

        Returns:
            Summary report of execution
        """

        print("\n" + "=" * 60)
        print("SUPERVISED MULTI-AGENT EXECUTION")
        print("=" * 60)

        # Create base branch
        base_branch = f"supervised/{self.execution_id}"
        subprocess.run(
            ["git", "checkout", "-b", base_branch],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )
        print(f"\n✅ Created supervised branch: {base_branch}")

        # Create worktrees for agents
        agent_configs = []
        for i, task in enumerate(agent_tasks):
            agent_id = f"agent_{i}_{task.agent_type}"

            # Create worktree
            worktree = self.worktree_manager.create_agent_worktree(
                agent_id=agent_id,
                agent_type=task.agent_type,
                base_branch=base_branch,
                execution_id=self.execution_id,
            )

            env = self.worktree_manager.get_agent_environment(agent_id)

            agent_configs.append(
                {
                    "agent_id": agent_id,
                    "task": task,
                    "worktree_path": Path(env["working_directory"]),
                    "workspace_path": Path(env["agent_workspace"]),
                }
            )

        # Execute agents
        if parallel:
            print(
                f"\n📌 Executing {len(agent_tasks)} agents in parallel with supervision..."
            )
            tasks = [
                self.execute_agent_with_supervision(
                    config["agent_id"],
                    config["task"],
                    config["worktree_path"],
                    config["workspace_path"],
                )
                for config in agent_configs
            ]
            results = await asyncio.gather(*tasks)
        else:
            print(
                f"\n📌 Executing {len(agent_tasks)} agents sequentially with supervision..."
            )
            results = []
            for config in agent_configs:
                result = await self.execute_agent_with_supervision(
                    config["agent_id"],
                    config["task"],
                    config["worktree_path"],
                    config["workspace_path"],
                )
                results.append(result)

                # Check if we should stop
                if stop_on_failure and result.get("pipeline_blocked"):
                    print("\n❌ Pipeline blocked due to critical failure")
                    break

        # Summary
        print("\n📊 Execution Summary:")
        approved = sum(1 for r in results if r["approved_for_merge"])
        needs_review = sum(1 for r in results if r["requires_human_approval"])
        failed = sum(1 for r in results if r["quality_status"] == "needs_revision")

        print(f"   ✅ Approved: {approved}/{len(results)}")
        print(f"   👀 Needs Review: {needs_review}/{len(results)}")
        print(f"   ❌ Failed: {failed}/{len(results)}")

        # Merge approved agents
        merged_count = 0
        if approved > 0:
            print("\n📌 Merging approved agent work...")

            for i, result in enumerate(results):
                if (
                    result["approved_for_merge"]
                    and not result["requires_human_approval"]
                ):
                    config = agent_configs[i]
                    agent_type = config["task"].agent_type

                    # Get changed files
                    changed_files = self.merger.get_agent_changes(
                        config["worktree_path"], agent_type
                    )

                    if changed_files:
                        # Merge
                        success = self.merger.cherry_pick_files(
                            source_branch=f"agent/{self.execution_id}/{agent_type}",
                            target_branch=base_branch,
                            files=changed_files,
                        )

                        if success:
                            merged_count += 1
                            print(f"   ✅ Merged {agent_type}")

        # Run post-merge quality checks
        if merged_count > 0:
            print("\n🔍 Running post-merge quality checks...")
            workspaces = [
                self.repo_path
                / "apps/multi-agent-monitor"
                / f"agent_workspace_{task.agent_type}"
                for task in agent_tasks
            ]
            quality_report = self.post_merge_quality.run_quality_checks(workspaces)

        # Generate final report
        final_report = {
            "execution_id": self.execution_id,
            "total_agents": len(agent_tasks),
            "approved": approved,
            "needs_review": needs_review,
            "failed": failed,
            "merged": merged_count,
            "quality_summary": self.quality_control.export_quality_summary(),
            "timestamp": datetime.now().isoformat(),
        }

        # Save report
        report_path = (
            self.repo_path / f"agent_execution_report_{self.execution_id}.json"
        )
        with open(report_path, "w") as f:
            json.dump(final_report, f, indent=2)

        print(f"\n📄 Report saved to: {report_path.name}")

        # Cleanup
        print("\n🧹 Cleaning up worktrees...")
        for config in agent_configs:
            try:
                self.worktree_manager.cleanup_worktree(config["agent_id"], force=True)
            except:
                pass

        # Return to original branch
        subprocess.run(
            ["git", "checkout", "feature/multi-agent-orchestration"],
            cwd=self.repo_path,
            capture_output=True,
        )

        # Keep supervised branch for inspection
        print(f"✅ Supervised branch kept for inspection: {base_branch}")

        return final_report
