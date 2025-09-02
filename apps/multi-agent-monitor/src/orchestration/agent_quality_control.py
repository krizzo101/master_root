"""
Agent Quality Control and Action Confirmation System
Ensures agent outputs meet quality standards before merging
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class QualityStatus(Enum):
    """Quality check status levels"""

    PENDING = "pending"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class ActionType(Enum):
    """Types of agent actions that need confirmation"""

    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    API_CALL = "api_call"
    DATABASE_CHANGE = "database_change"
    SYSTEM_COMMAND = "system_command"
    DEPENDENCY_ADD = "dependency_add"


@dataclass
class AgentAction:
    """Represents an action taken by an agent"""

    agent_id: str
    agent_type: str
    action_type: ActionType
    description: str
    file_path: Optional[Path] = None
    content_preview: Optional[str] = None
    risk_level: str = "low"  # low, medium, high
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class QualityMetrics:
    """Metrics for agent output quality"""

    code_coverage: Optional[float] = None
    test_pass_rate: Optional[float] = None
    linting_score: Optional[float] = None
    documentation_completeness: Optional[float] = None
    security_score: Optional[float] = None
    performance_impact: Optional[str] = None

    def overall_score(self) -> float:
        """Calculate overall quality score"""
        scores = []
        if self.code_coverage is not None:
            scores.append(self.code_coverage)
        if self.test_pass_rate is not None:
            scores.append(self.test_pass_rate)
        if self.linting_score is not None:
            scores.append(self.linting_score)
        if self.documentation_completeness is not None:
            scores.append(self.documentation_completeness)
        if self.security_score is not None:
            scores.append(self.security_score)

        return sum(scores) / len(scores) if scores else 0.0


class AgentQualityControl:
    """
    Manages quality control and action confirmation for agents.
    Ensures agent outputs meet standards before allowing merge.
    """

    def __init__(self, repo_path: Path, auto_approve_threshold: float = 0.8):
        self.repo_path = repo_path
        self.auto_approve_threshold = auto_approve_threshold
        self.pending_actions: Dict[str, List[AgentAction]] = {}
        self.quality_reports: Dict[str, QualityMetrics] = {}
        self.approval_log = []

    def register_agent_action(self, action: AgentAction) -> None:
        """Register an action that needs review"""
        if action.agent_id not in self.pending_actions:
            self.pending_actions[action.agent_id] = []

        self.pending_actions[action.agent_id].append(action)
        logger.info(
            f"Registered action: {action.action_type.value} from {action.agent_id}"
        )

    def analyze_agent_output(
        self, agent_id: str, worktree_path: Path
    ) -> QualityMetrics:
        """
        Analyze the quality of an agent's output.

        Returns:
            QualityMetrics with scores for various quality aspects
        """

        metrics = QualityMetrics()

        # Find agent's workspace
        workspace = (
            worktree_path
            / "apps/multi-agent-monitor"
            / f"agent_workspace_{agent_id.split('_')[-1]}"
        )

        if not workspace.exists():
            logger.warning(f"Workspace not found for {agent_id}")
            return metrics

        # Analyze Python files
        python_files = list(workspace.glob("**/*.py"))

        if python_files:
            # Check test coverage (simplified)
            test_files = [f for f in python_files if f.name.startswith("test_")]
            non_test_files = [f for f in python_files if not f.name.startswith("test_")]

            if non_test_files:
                metrics.code_coverage = len(test_files) / len(non_test_files) * 100

            # Run tests if any
            if test_files:
                passed = 0
                total = len(test_files)

                for test_file in test_files:
                    try:
                        result = subprocess.run(
                            ["python", str(test_file)],
                            cwd=self.repo_path,
                            capture_output=True,
                            timeout=10,
                        )
                        if result.returncode == 0:
                            passed += 1
                    except:
                        pass

                metrics.test_pass_rate = (passed / total * 100) if total > 0 else 0

            # Check linting (simplified)
            try:
                result = subprocess.run(
                    ["ruff", "check", "--exit-zero"] + [str(f) for f in python_files],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

                # Count issues
                issues = len([l for l in result.stdout.split("\n") if ".py:" in l])
                total_lines = sum(len(f.read_text().split("\n")) for f in python_files)

                # Score based on issues per 100 lines
                if total_lines > 0:
                    issues_per_100 = (issues / total_lines) * 100
                    metrics.linting_score = max(0, 100 - (issues_per_100 * 10))
                else:
                    metrics.linting_score = 100

            except:
                metrics.linting_score = None

        # Check documentation
        doc_files = list(workspace.glob("**/*.md"))
        if doc_files:
            # Simple heuristic: documentation exists
            metrics.documentation_completeness = 100 if doc_files else 0

        # Security check (simplified - look for obvious issues)
        security_issues = 0
        for py_file in python_files:
            content = py_file.read_text()
            # Check for hardcoded secrets, eval, exec, etc.
            dangerous_patterns = [
                "eval(",
                "exec(",
                "os.system(",
                "subprocess.call(",
                "password =",
                "api_key =",
                "secret =",
            ]
            for pattern in dangerous_patterns:
                if pattern in content:
                    security_issues += 1

        metrics.security_score = max(0, 100 - (security_issues * 20))

        # Store metrics
        self.quality_reports[agent_id] = metrics

        return metrics

    def validate_agent_task(
        self, agent_id: str, task_requirements: Dict
    ) -> Dict[str, Any]:
        """
        Validate that agent completed its task according to requirements.

        Args:
            agent_id: Agent identifier
            task_requirements: Dict with expected outputs/criteria

        Returns:
            Validation report
        """

        validation = {
            "agent_id": agent_id,
            "requirements_met": [],
            "requirements_missing": [],
            "warnings": [],
            "errors": [],
            "success": False,
        }

        # Check if agent has pending actions
        if agent_id not in self.pending_actions:
            validation["errors"].append("No actions recorded for agent")
            return validation

        actions = self.pending_actions[agent_id]

        # Check required files
        if "required_files" in task_requirements:
            created_files = [
                a.file_path.name
                for a in actions
                if a.action_type == ActionType.FILE_CREATE and a.file_path
            ]

            for required_file in task_requirements["required_files"]:
                if required_file in created_files:
                    validation["requirements_met"].append(f"Created {required_file}")
                else:
                    validation["requirements_missing"].append(
                        f"Missing {required_file}"
                    )

        # Check file content requirements
        if "content_checks" in task_requirements:
            for check in task_requirements["content_checks"]:
                file_pattern = check.get("file_pattern")
                must_contain = check.get("must_contain", [])
                must_not_contain = check.get("must_not_contain", [])

                # Find matching files
                matching_actions = [
                    a
                    for a in actions
                    if a.file_path and file_pattern in str(a.file_path)
                ]

                for action in matching_actions:
                    if action.content_preview:
                        for required in must_contain:
                            if required in action.content_preview:
                                validation["requirements_met"].append(
                                    f"{action.file_path.name} contains '{required}'"
                                )
                            else:
                                validation["requirements_missing"].append(
                                    f"{action.file_path.name} missing '{required}'"
                                )

                        for forbidden in must_not_contain:
                            if forbidden in action.content_preview:
                                validation["errors"].append(
                                    f"{action.file_path.name} contains forbidden '{forbidden}'"
                                )

        # Check action limits
        if "max_file_changes" in task_requirements:
            file_changes = len(
                [
                    a
                    for a in actions
                    if a.action_type in [ActionType.FILE_CREATE, ActionType.FILE_MODIFY]
                ]
            )

            if file_changes > task_requirements["max_file_changes"]:
                validation["warnings"].append(
                    f"Too many file changes: {file_changes} > {task_requirements['max_file_changes']}"
                )

        # Determine success
        validation["success"] = (
            len(validation["requirements_missing"]) == 0
            and len(validation["errors"]) == 0
        )

        return validation

    def review_agent_output(
        self,
        agent_id: str,
        worktree_path: Path,
        task_requirements: Optional[Dict] = None,
    ) -> Tuple[QualityStatus, str]:
        """
        Review agent output and determine approval status.

        Returns:
            (status, reason)
        """

        print(f"\n🔍 Reviewing output from {agent_id}...")

        # Get quality metrics
        metrics = self.analyze_agent_output(agent_id, worktree_path)
        overall_score = metrics.overall_score()

        print(f"   📊 Quality Score: {overall_score:.1f}/100")

        # Validate task requirements if provided
        validation_report = None
        if task_requirements:
            validation_report = self.validate_agent_task(agent_id, task_requirements)

            if not validation_report["success"]:
                reason = f"Task validation failed: {validation_report['requirements_missing']}"
                print(f"   ❌ {reason}")
                return QualityStatus.NEEDS_REVISION, reason

        # Check for high-risk actions
        if agent_id in self.pending_actions:
            high_risk_actions = [
                a for a in self.pending_actions[agent_id] if a.risk_level == "high"
            ]

            if high_risk_actions:
                reason = f"Contains {len(high_risk_actions)} high-risk actions requiring manual review"
                print(f"   ⚠️  {reason}")
                return QualityStatus.REVIEWING, reason

        # Auto-approve if score is high enough
        if overall_score >= (self.auto_approve_threshold * 100):
            reason = (
                f"Auto-approved: quality score {overall_score:.1f} exceeds threshold"
            )
            print(f"   ✅ {reason}")

            # Log approval
            self.approval_log.append(
                {
                    "agent_id": agent_id,
                    "status": QualityStatus.AUTO_APPROVED,
                    "score": overall_score,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics.__dict__,
                }
            )

            return QualityStatus.AUTO_APPROVED, reason

        # Needs improvement
        issues = []
        if metrics.test_pass_rate and metrics.test_pass_rate < 100:
            issues.append(f"tests failing ({metrics.test_pass_rate:.0f}% pass rate)")
        if metrics.security_score and metrics.security_score < 80:
            issues.append(f"security concerns (score: {metrics.security_score:.0f})")
        if metrics.linting_score and metrics.linting_score < 70:
            issues.append(f"code quality issues (score: {metrics.linting_score:.0f})")

        reason = f"Quality below threshold: {', '.join(issues)}"
        print(f"   ⚠️  {reason}")

        return QualityStatus.NEEDS_REVISION, reason

    def get_quality_report(self, agent_id: str) -> Dict:
        """Get detailed quality report for an agent"""

        report = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": None,
            "actions": [],
            "approval_status": None,
        }

        if agent_id in self.quality_reports:
            metrics = self.quality_reports[agent_id]
            report["metrics"] = {
                "overall_score": metrics.overall_score(),
                "code_coverage": metrics.code_coverage,
                "test_pass_rate": metrics.test_pass_rate,
                "linting_score": metrics.linting_score,
                "documentation_completeness": metrics.documentation_completeness,
                "security_score": metrics.security_score,
            }

        if agent_id in self.pending_actions:
            report["actions"] = [
                {
                    "type": a.action_type.value,
                    "description": a.description,
                    "risk_level": a.risk_level,
                    "file": str(a.file_path) if a.file_path else None,
                }
                for a in self.pending_actions[agent_id]
            ]

        # Check approval log
        for entry in self.approval_log:
            if entry["agent_id"] == agent_id:
                report["approval_status"] = entry["status"].value
                break

        return report

    def require_human_approval(self, agent_id: str) -> bool:
        """
        Check if human approval is required for agent's actions.

        Returns:
            True if human approval needed
        """

        if agent_id not in self.pending_actions:
            return False

        # Check for high-risk actions
        for action in self.pending_actions[agent_id]:
            if action.risk_level == "high":
                return True

            # Specific action types that need approval
            if action.action_type in [
                ActionType.FILE_DELETE,
                ActionType.DATABASE_CHANGE,
                ActionType.SYSTEM_COMMAND,
            ]:
                return True

        # Check quality score
        if agent_id in self.quality_reports:
            score = self.quality_reports[agent_id].overall_score()
            if score < 60:  # Below 60% requires human review
                return True

        return False

    def export_quality_summary(self) -> Dict:
        """Export summary of all agent quality checks"""

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.quality_reports),
            "auto_approved": 0,
            "needs_revision": 0,
            "pending_review": 0,
            "average_quality": 0,
            "agents": [],
        }

        total_score = 0

        for agent_id, metrics in self.quality_reports.items():
            score = metrics.overall_score()
            total_score += score

            status = "pending"
            for entry in self.approval_log:
                if entry["agent_id"] == agent_id:
                    status = entry["status"].value
                    if status == "auto_approved":
                        summary["auto_approved"] += 1
                    elif status == "needs_revision":
                        summary["needs_revision"] += 1
                    break

            if status == "pending":
                summary["pending_review"] += 1

            summary["agents"].append(
                {
                    "agent_id": agent_id,
                    "quality_score": score,
                    "status": status,
                    "action_count": len(self.pending_actions.get(agent_id, [])),
                }
            )

        if summary["total_agents"] > 0:
            summary["average_quality"] = total_score / summary["total_agents"]

        return summary
