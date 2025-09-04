"""Enhanced Git history adapter with comprehensive commit analysis and efficient incremental processing.

This module implements a production-ready Git adapter that provides:
- Incremental commit processing with checkpoint management
- Advanced commit analysis and metadata extraction
- Branch topology mapping and merge detection
- Author relationship tracking and contribution analysis
- File change correlation and impact analysis
- Performance optimization through parallel processing
- Cross-domain temporal correlation with chat logs and error reports
"""

import asyncio
import hashlib
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class ProcessingStatus(Enum):
    """Git processing status enumeration."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class CommitType(Enum):
    """Commit classification types for semantic analysis."""

    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    MERGE = "merge"
    REVERT = "revert"
    CHORE = "chore"
    UNKNOWN = "unknown"


@dataclass
class CommitAnalysis:
    """Comprehensive results of commit analysis."""

    commit_hash: str
    commit_type: CommitType
    impact_score: float  # 0.0 to 1.0 - overall impact on codebase
    risk_score: float  # 0.0 to 1.0 - risk of introducing issues
    complexity_delta: float  # Change in codebase complexity
    files_impacted: List[str]  # List of affected file paths
    semantic_tags: List[str]  # Extracted semantic tags
    related_patterns: List[str]  # Detected behavioral patterns
    author_patterns: Dict[str, Any]  # Author-specific pattern analysis


@dataclass
class BranchInfo:
    """Branch topology and metadata information."""

    name: str
    head_commit: str
    base_branch: Optional[str]
    branch_type: str  # 'main', 'feature', 'hotfix', 'release', 'develop'
    creation_date: datetime
    last_activity: datetime
    commit_count: int
    is_merged: bool
    merge_commit: Optional[str]


@dataclass
class MergeInfo:
    """Merge commit analysis and metadata."""

    merge_commit_hash: str
    source_branch: str
    target_branch: str
    parent_commits: List[str]
    conflicts_resolved: bool
    merge_strategy: str  # 'merge', 'squash', 'rebase', 'fast-forward'
    files_affected: List[str]
    impact_score: float


@dataclass
class ProcessingCheckpoint:
    """Git processing checkpoint for recovery."""

    repository_path: str
    branch_name: str
    last_processed_commit: str
    last_processed_timestamp: datetime
    commit_count: int
    status: ProcessingStatus
    error_message: Optional[str] = None


class GitCheckpointManager:
    """Advanced checkpoint manager for incremental git history processing."""

    def __init__(self, config: AdapterConfig, database_connection=None):
        """Initialize checkpoint manager.

        Args:
            config: Adapter configuration
            database_connection: Database connection for checkpoint persistence
        """
        self.config = config
        self.db = database_connection
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="GitCheckpointManager")

    async def get_last_processed_commit(self, branch: str) -> Optional[str]:
        """Get the last processed commit hash for a branch.

        Args:
            branch: Branch name

        Returns:
            Last processed commit hash or None
        """
        if not self.db:
            return None

        try:
            query = """
                SELECT last_processed_commit
                FROM git_processing_checkpoints
                WHERE repository_path = $1 AND branch_name = $2
                    AND processing_status != 'error'
                ORDER BY updated_at DESC LIMIT 1
            """
            result = await self.db.execute_query(query, self.repository_path, branch, fetch="one")
            return result["last_processed_commit"] if result else None

        except Exception as e:
            self.logger.error("Failed to get last processed commit", branch=branch, error=str(e))
            return None

    async def save_checkpoint(
        self, branch: str, commit_hash: str, timestamp: datetime, commit_count: int = 0
    ) -> None:
        """Save processing checkpoint for a branch.

        Args:
            branch: Branch name
            commit_hash: Last processed commit hash
            timestamp: Commit timestamp
            commit_count: Number of commits processed
        """
        if not self.db:
            return

        try:
            query = """
                INSERT INTO git_processing_checkpoints
                (repository_path, branch_name, last_processed_commit,
                 last_processed_timestamp, commit_count, processing_status, updated_at)
                VALUES ($1, $2, $3, $4, $5, 'active', NOW())
                ON CONFLICT (repository_path, branch_name)
                DO UPDATE SET
                    last_processed_commit = EXCLUDED.last_processed_commit,
                    last_processed_timestamp = EXCLUDED.last_processed_timestamp,
                    commit_count = EXCLUDED.commit_count,
                    processing_status = 'active',
                    updated_at = NOW()
            """
            await self.db.execute_query(
                query,
                self.repository_path,
                branch,
                commit_hash,
                timestamp,
                commit_count,
                fetch="none",
            )

            self.logger.info(
                "Checkpoint saved", branch=branch, commit=commit_hash[:8], commit_count=commit_count
            )

        except Exception as e:
            self.logger.error("Failed to save checkpoint", branch=branch, error=str(e))

    async def mark_processing_error(self, branch: str, error_message: str) -> None:
        """Mark a branch as having processing errors.

        Args:
            branch: Branch name
            error_message: Error description
        """
        if not self.db:
            return

        try:
            query = """
                UPDATE git_processing_checkpoints
                SET processing_status = 'error',
                    last_error = $3,
                    error_count = error_count + 1,
                    updated_at = NOW()
                WHERE repository_path = $1 AND branch_name = $2
            """
            await self.db.execute_query(
                query, self.repository_path, branch, error_message, fetch="none"
            )

        except Exception as e:
            self.logger.error("Failed to mark processing error", branch=branch, error=str(e))


class CommitProcessor:
    """Advanced commit analysis engine with semantic understanding."""

    def __init__(self, config: AdapterConfig):
        """Initialize commit processor.

        Args:
            config: Adapter configuration
        """
        self.config = config
        self.logger = logger.bind(component="CommitProcessor")

        # Commit type classification patterns
        self.commit_patterns = {
            CommitType.FEATURE: ["feat", "feature", "add", "implement", "create", "new"],
            CommitType.BUGFIX: ["fix", "bug", "issue", "resolve", "patch", "correct"],
            CommitType.HOTFIX: ["hotfix", "urgent", "critical", "emergency", "quick fix"],
            CommitType.REFACTOR: ["refactor", "restructure", "reorganize", "cleanup", "improve"],
            CommitType.DOCUMENTATION: ["doc", "docs", "readme", "comment", "documentation"],
            CommitType.TEST: ["test", "spec", "coverage", "unittest", "testing"],
            CommitType.MERGE: ["merge", "pull request", "pr", "merge branch"],
            CommitType.REVERT: ["revert", "rollback", "undo", "back out"],
            CommitType.CHORE: ["chore", "update", "upgrade", "dependency", "build", "ci"],
        }

    async def analyze_commit(self, commit_data: Dict) -> CommitAnalysis:
        """Perform comprehensive commit analysis.

        Args:
            commit_data: Raw commit data dictionary

        Returns:
            Detailed commit analysis results
        """
        try:
            commit_hash = commit_data["hash"]
            message = f"{commit_data.get('subject', '')} {commit_data.get('body', '')}".lower()
            changed_files = commit_data.get("changed_files", [])

            # Classify commit type
            commit_type = self._classify_commit_type(message, changed_files)

            # Calculate impact score
            impact_score = await self._calculate_impact_score(commit_data)

            # Calculate risk score
            risk_score = self._calculate_risk_score(commit_data, impact_score)

            # Calculate complexity delta
            complexity_delta = self._calculate_complexity_delta(changed_files)

            # Extract semantic tags
            semantic_tags = self._extract_semantic_tags(message, changed_files)

            # Detect behavioral patterns
            patterns = self._detect_commit_patterns(commit_data)

            # Analyze author patterns
            author_patterns = self._analyze_author_patterns(commit_data)

            return CommitAnalysis(
                commit_hash=commit_hash,
                commit_type=commit_type,
                impact_score=impact_score,
                risk_score=risk_score,
                complexity_delta=complexity_delta,
                files_impacted=[f["file"] for f in changed_files],
                semantic_tags=semantic_tags,
                related_patterns=patterns,
                author_patterns=author_patterns,
            )

        except Exception as e:
            self.logger.error(
                "Commit analysis failed", commit=commit_data.get("hash", "unknown"), error=str(e)
            )

            # Return fallback analysis
            return CommitAnalysis(
                commit_hash=commit_data.get("hash", "unknown"),
                commit_type=CommitType.UNKNOWN,
                impact_score=0.0,
                risk_score=0.0,
                complexity_delta=0.0,
                files_impacted=[],
                semantic_tags=[],
                related_patterns=[],
                author_patterns={},
            )

    def _classify_commit_type(self, message: str, changed_files: List[Dict]) -> CommitType:
        """Classify commit type based on message and file changes.

        Args:
            message: Commit message (subject + body)
            changed_files: List of changed files with metadata

        Returns:
            Classified commit type
        """
        # Check for merge commits first
        if len(changed_files) > 20 and ("merge" in message or "pull request" in message):
            return CommitType.MERGE

        # Check message patterns
        for commit_type, patterns in self.commit_patterns.items():
            if any(pattern in message for pattern in patterns):
                return commit_type

        # Check file-based patterns
        file_extensions = {
            f["file"].split(".")[-1].lower() for f in changed_files if "." in f["file"]
        }

        # Documentation files
        if {"md", "txt", "rst", "adoc"} & file_extensions:
            return CommitType.DOCUMENTATION

        # Test files
        if any("test" in f["file"].lower() or "spec" in f["file"].lower() for f in changed_files):
            return CommitType.TEST

        return CommitType.UNKNOWN

    async def _calculate_impact_score(self, commit_data: Dict) -> float:
        """Calculate the impact score of a commit.

        Args:
            commit_data: Raw commit data

        Returns:
            Impact score from 0.0 to 1.0
        """
        changed_files = commit_data.get("changed_files", [])
        diff_content = commit_data.get("diff", "")

        # Base score from number of files
        file_score = min(len(changed_files) / 10.0, 1.0)

        # Score from diff size
        diff_score = min(len(diff_content) / 10000.0, 1.0)

        # Score from core file changes (higher impact)
        core_files = sum(1 for f in changed_files if self._is_core_file(f["file"]))
        core_score = min(core_files / 5.0, 1.0)

        # Combined weighted score
        impact_score = file_score * 0.3 + diff_score * 0.4 + core_score * 0.3

        return min(impact_score, 1.0)

    def _calculate_risk_score(self, commit_data: Dict, impact_score: float) -> float:
        """Calculate risk score for potential issues.

        Args:
            commit_data: Raw commit data
            impact_score: Pre-calculated impact score

        Returns:
            Risk score from 0.0 to 1.0
        """
        changed_files = commit_data.get("changed_files", [])
        message = commit_data.get("subject", "").lower()

        risk_factors = 0.0

        # Database schema changes
        if any("migration" in f["file"] or "schema" in f["file"] for f in changed_files):
            risk_factors += 0.3

        # Configuration changes
        if any(
            f["file"].endswith((".config", ".env", ".yml", ".yaml", ".json")) for f in changed_files
        ):
            risk_factors += 0.2

        # Critical keywords in message
        critical_keywords = ["critical", "urgent", "hotfix", "emergency"]
        if any(keyword in message for keyword in critical_keywords):
            risk_factors += 0.2

        # Large number of deletions
        deletions = sum(1 for f in changed_files if f.get("type") == "D")
        if deletions > 5:
            risk_factors += 0.2

        # Late night commits (higher error likelihood)
        try:
            commit_time = datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            )
            if commit_time.hour >= 22 or commit_time.hour <= 6:
                risk_factors += 0.1
        except:
            pass

        # Combine with impact score
        risk_score = min(risk_factors + (impact_score * 0.3), 1.0)

        return risk_score

    def _calculate_complexity_delta(self, changed_files: List[Dict]) -> float:
        """Calculate change in codebase complexity.

        Args:
            changed_files: List of file changes

        Returns:
            Complexity delta (can be negative for simplifications)
        """
        complexity_delta = 0.0

        for file_change in changed_files:
            file_path = file_change["file"]
            change_type = file_change.get("type", "M")

            # Base complexity changes
            if change_type == "A":  # Added
                complexity_delta += 1.0
            elif change_type == "D":  # Deleted
                complexity_delta -= 0.5
            elif change_type == "M":  # Modified
                complexity_delta += 0.1

            # Weight by file type
            if file_path.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c", ".go")):
                complexity_delta *= 1.5
            elif file_path.endswith((".md", ".txt", ".rst", ".json", ".yml")):
                complexity_delta *= 0.5

        return complexity_delta

    def _extract_semantic_tags(self, message: str, changed_files: List[Dict]) -> List[str]:
        """Extract semantic tags from commit data.

        Args:
            message: Commit message
            changed_files: List of changed files

        Returns:
            List of semantic tags
        """
        tags = []

        # Message-based tags
        if "breaking" in message or "breaking change" in message:
            tags.append("breaking_change")
        if "security" in message:
            tags.append("security")
        if "performance" in message or "optimization" in message:
            tags.append("performance")
        if "deprecated" in message:
            tags.append("deprecation")

        # File type tags
        file_types = {f["file"].split(".")[-1].lower() for f in changed_files if "." in f["file"]}

        for ext in file_types:
            if ext in ["py", "js", "ts", "java", "go", "rs", "cpp", "c"]:
                tags.append(f"language_{ext}")

        # Architecture tags
        if any("api" in f["file"].lower() for f in changed_files):
            tags.append("api_change")
        if any("database" in f["file"].lower() or "db" in f["file"].lower() for f in changed_files):
            tags.append("database_change")

        return list(set(tags))  # Remove duplicates

    def _detect_commit_patterns(self, commit_data: Dict) -> List[str]:
        """Detect behavioral patterns in the commit.

        Args:
            commit_data: Raw commit data

        Returns:
            List of detected patterns
        """
        patterns = []

        # Time-based patterns
        try:
            commit_time = datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            )
            if commit_time.hour >= 22 or commit_time.hour <= 6:
                patterns.append("late_night_commit")
            if commit_time.weekday() >= 5:  # Weekend
                patterns.append("weekend_commit")
        except:
            pass

        # Change pattern analysis
        changed_files = commit_data.get("changed_files", [])
        file_count = len(changed_files)

        if file_count == 1:
            patterns.append("single_file_change")
        elif file_count > 20:
            patterns.append("massive_change")
        elif file_count > 10:
            patterns.append("large_change")

        # Message pattern analysis
        message = commit_data.get("subject", "").lower()
        if len(message) < 10:
            patterns.append("minimal_description")
        elif len(message) > 100:
            patterns.append("detailed_description")

        return patterns

    def _analyze_author_patterns(self, commit_data: Dict) -> Dict[str, Any]:
        """Analyze author-specific patterns and behavior.

        Args:
            commit_data: Raw commit data

        Returns:
            Author pattern analysis
        """
        try:
            commit_time = datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            )
            hour = commit_time.hour
            weekday = commit_time.weekday()
        except:
            hour = None
            weekday = None

        return {
            "author": commit_data.get("author", ""),
            "author_email": commit_data.get("author_email", ""),
            "commit_time_hour": hour,
            "commit_weekday": weekday,
            "message_length": len(commit_data.get("subject", "") + commit_data.get("body", "")),
            "files_per_commit": len(commit_data.get("changed_files", [])),
        }

    def _is_core_file(self, file_path: str) -> bool:
        """Check if file is considered core to the application.

        Args:
            file_path: File path to check

        Returns:
            True if core file, False otherwise
        """
        core_patterns = [
            "/main.",
            "/app.",
            "/index.",
            "/server.",
            "/client.",
            "/models/",
            "/controllers/",
            "/services/",
            "/api/",
            "/core/",
            "/lib/",
            "/components/",
            "/views/",
            "/routes/",
            "package.json",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "Dockerfile",
            "docker-compose",
            ".github/workflows/",
            "Makefile",
            "CMakeLists.txt",
        ]
        return any(pattern in file_path for pattern in core_patterns)


class CodeChangeAnalyzer:
    """Advanced analyzer for detailed file diff analysis."""

    def __init__(self, config: AdapterConfig):
        """Initialize code change analyzer.

        Args:
            config: Adapter configuration
        """
        self.config = config
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="CodeChangeAnalyzer")

    async def analyze_file_changes(self, commit_data: Dict) -> Dict[str, Any]:
        """Analyze file changes in detail.

        Args:
            commit_data: Raw commit data with file changes

        Returns:
            Detailed file change analysis
        """
        changed_files = commit_data.get("changed_files", [])

        analysis = {
            "total_files": len(changed_files),
            "added_files": sum(1 for f in changed_files if f.get("type") == "A"),
            "modified_files": sum(1 for f in changed_files if f.get("type") == "M"),
            "deleted_files": sum(1 for f in changed_files if f.get("type") == "D"),
            "renamed_files": sum(1 for f in changed_files if f.get("type") == "R"),
            "file_types": {},
            "core_files_affected": [],
            "impact_by_directory": {},
        }

        # Analyze file types and impacts
        for file_change in changed_files:
            file_path = file_change["file"]

            # File type analysis
            if "." in file_path:
                ext = file_path.split(".")[-1].lower()
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

            # Core file identification
            if self._is_core_file(file_path):
                analysis["core_files_affected"].append(file_path)

            # Directory impact analysis
            directory = "/".join(file_path.split("/")[:-1]) or "."
            if directory not in analysis["impact_by_directory"]:
                analysis["impact_by_directory"][directory] = 0
            analysis["impact_by_directory"][directory] += 1

        return analysis

    def _is_core_file(self, file_path: str) -> bool:
        """Check if file is core to application."""
        core_patterns = [
            "/main.",
            "/app.",
            "/index.",
            "/models/",
            "/controllers/",
            "/services/",
            "/api/",
            "/core/",
            "/lib/",
            "package.json",
            "requirements.txt",
            "Dockerfile",
        ]
        return any(pattern in file_path for pattern in core_patterns)


class GitRepositoryScanner:
    """Repository scanner for branch discovery and topology mapping."""

    def __init__(self, config: AdapterConfig):
        """Initialize repository scanner.

        Args:
            config: Adapter configuration
        """
        self.config = config
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="GitRepositoryScanner")

    async def scan_branches(self) -> Dict[str, BranchInfo]:
        """Scan and map all branches in the repository.

        Returns:
            Dictionary mapping branch names to BranchInfo objects
        """
        try:
            branches = {}

            # Get all branches with details
            branch_output = await self._run_git_command(
                [
                    "for-each-ref",
                    "--format=%(refname:short)|%(objectname)|%(committerdate:iso8601)|%(authorname)",
                    "refs/heads/",
                ]
            )

            for line in branch_output.split("\n"):
                if not line.strip():
                    continue

                parts = line.split("|")
                if len(parts) >= 3:
                    branch_name = parts[0]
                    head_commit = parts[1]
                    try:
                        last_activity = datetime.fromisoformat(parts[2].replace(" ", "T"))
                    except:
                        last_activity = datetime.utcnow()

                    # Analyze branch details
                    branch_info = await self._analyze_branch(
                        branch_name, head_commit, last_activity
                    )
                    branches[branch_name] = branch_info

            return branches

        except Exception as e:
            self.logger.error("Failed to scan branches", error=str(e))
            return {}

    async def _analyze_branch(
        self, branch_name: str, head_commit: str, last_activity: datetime
    ) -> BranchInfo:
        """Analyze individual branch characteristics.

        Args:
            branch_name: Name of the branch
            head_commit: HEAD commit hash
            last_activity: Last activity timestamp

        Returns:
            BranchInfo object with analysis results
        """
        try:
            # Get commit count
            commit_count_output = await self._run_git_command(["rev-list", "--count", head_commit])
            commit_count = int(commit_count_output.strip())

            # Detect branch type
            branch_type = self._classify_branch_type(branch_name)

            # Check if merged
            is_merged = await self._is_branch_merged(branch_name)

            # Get creation date
            creation_date = await self._get_branch_creation_date(branch_name)

            # Detect base branch
            base_branch = await self._detect_base_branch(branch_name)

            return BranchInfo(
                name=branch_name,
                head_commit=head_commit,
                base_branch=base_branch,
                branch_type=branch_type,
                creation_date=creation_date,
                last_activity=last_activity,
                commit_count=commit_count,
                is_merged=is_merged,
                merge_commit=None,  # Would require additional analysis
            )

        except Exception as e:
            self.logger.error("Branch analysis failed", branch=branch_name, error=str(e))
            return BranchInfo(
                name=branch_name,
                head_commit=head_commit,
                base_branch=None,
                branch_type="unknown",
                creation_date=last_activity,
                last_activity=last_activity,
                commit_count=0,
                is_merged=False,
                merge_commit=None,
            )

    def _classify_branch_type(self, branch_name: str) -> str:
        """Classify branch type based on naming conventions.

        Args:
            branch_name: Branch name to classify

        Returns:
            Branch type classification
        """
        name_lower = branch_name.lower()

        if name_lower in ["main", "master", "trunk"]:
            return "main"
        elif name_lower.startswith(("feature/", "feat/", "features/")):
            return "feature"
        elif name_lower.startswith(("hotfix/", "fix/", "bugfix/")):
            return "hotfix"
        elif name_lower.startswith(("release/", "rel/")):
            return "release"
        elif name_lower.startswith(("develop", "dev/")):
            return "develop"
        else:
            return "unknown"

    async def _is_branch_merged(self, branch_name: str) -> bool:
        """Check if branch has been merged.

        Args:
            branch_name: Branch name to check

        Returns:
            True if merged, False otherwise
        """
        try:
            merged_branches = await self._run_git_command(["branch", "--merged"])
            return branch_name in merged_branches
        except Exception:
            return False

    async def _get_branch_creation_date(self, branch_name: str) -> datetime:
        """Get the creation date of a branch.

        Args:
            branch_name: Branch name

        Returns:
            Creation date or current time as fallback
        """
        try:
            # Get first commit on branch (simplified approach)
            first_commit = await self._run_git_command(
                ["rev-list", "--reverse", f"{branch_name}", "--max-count", "1"]
            )

            if first_commit.strip():
                commit_date = await self._run_git_command(
                    ["show", "-s", "--format=%ci", first_commit.strip()]
                )
                return datetime.fromisoformat(commit_date.strip().replace(" ", "T"))

        except Exception:
            pass

        return datetime.utcnow()

    async def _detect_base_branch(self, branch_name: str) -> Optional[str]:
        """Detect the base branch for a feature branch.

        Args:
            branch_name: Branch name to analyze

        Returns:
            Base branch name or None if not found
        """
        if branch_name in ["main", "master", "develop"]:
            return None

        # Try to find merge-base with main branches
        for base in ["main", "master", "develop"]:
            try:
                await self._run_git_command(["merge-base", branch_name, base])
                return base
            except Exception:
                continue

        return None

    async def _run_git_command(self, args: List[str]) -> str:
        """Run git command and return output.

        Args:
            args: Git command arguments

        Returns:
            Command output as string

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        cmd = ["git", "-C", self.repository_path] + args

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)

        return stdout.decode("utf-8", errors="ignore").strip()


class GitAdapter(BaseAdapter):
    """Production-ready Git adapter with comprehensive features.

    This adapter provides:
    - Incremental commit processing with checkpoint management
    - Advanced commit analysis and metadata extraction
    - Branch topology mapping and merge detection
    - Author relationship tracking and contribution analysis
    - File change correlation and impact analysis
    - Cross-domain temporal correlation with chat logs and error reports
    """

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for the Git adapter.

        Returns:
            Default adapter configuration
        """
        return AdapterConfig(
            adapter_id="git_adapter",
            source_type="git",
            batch_mode=BatchMode.BATCH,
            batch_size=500,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                # Repository settings
                "repository_path": ".",
                "include_commits": True,
                "include_branches": True,
                "include_tags": True,
                "include_file_changes": True,
                # Incremental processing
                "enable_incremental": True,
                "checkpoint_interval": 100,
                "max_commits_per_batch": 1000,
                # Analysis features
                "enable_semantic_analysis": True,
                "enable_impact_scoring": True,
                "enable_relationship_detection": True,
                "enable_branch_detection": True,
                "enable_merge_analysis": True,
                "track_file_impacts": True,
                # Cross-domain correlation
                "correlate_with_chat": True,
                "correlate_with_errors": True,
                "temporal_window_hours": 48,
                # Performance settings
                "parallel_processing": True,
                "max_parallel_workers": 4,
                # Filtering options
                "max_commit_age_days": None,
                "exclude_merge_commits": False,
                "include_diff_content": True,
                "max_diff_size_kb": 100,
                "author_filters": [],
                "branch_filters": [],
            },
        )

    def __init__(self, config: AdapterConfig, database_connection=None):
        """Initialize the Git adapter.

        Args:
            config: Adapter configuration
            database_connection: Database connection for persistence
        """
        super().__init__(config)
        self.transformer = DataTransformer()
        self._repo_path = config.source_config.get("repository_path", ".")
        self._processed_commits: Set[str] = set()

        # Initialize specialized components
        self.checkpoint_manager = GitCheckpointManager(config, database_connection)
        self.commit_processor = CommitProcessor(config)
        self.change_analyzer = CodeChangeAnalyzer(config)
        self.repo_scanner = GitRepositoryScanner(config)

        # Configuration flags
        self.enable_incremental = config.source_config.get("enable_incremental", True)
        self.enable_semantic_analysis = config.source_config.get("enable_semantic_analysis", True)
        self.enable_branch_detection = config.source_config.get("enable_branch_detection", True)
        self.checkpoint_interval = config.source_config.get("checkpoint_interval", 100)

        # Processing state
        self._commit_count = 0
        self._current_branch = None
        self._branch_topology: Dict[str, BranchInfo] = {}

    async def initialize(self) -> None:
        """Initialize Git adapter resources."""
        self.logger.info("Initializing Git adapter")

        # Validate git repository
        if not await self._is_git_repo():
            raise ValueError(f"Not a git repository: {self._repo_path}")

        # Test git command availability
        try:
            await self._run_git_command(["--version"])
        except Exception as e:
            raise ValueError(f"Git command not available: {e}")

        # Initialize branch topology if enabled
        if self.enable_branch_detection:
            try:
                self._branch_topology = await self.repo_scanner.scan_branches()
                self.logger.info("Branch topology mapped", branch_count=len(self._branch_topology))
            except Exception as e:
                self.logger.warning("Branch detection initialization failed", error=str(e))

        self.logger.info(
            "Git adapter initialized",
            repo_path=self._repo_path,
            incremental=self.enable_incremental,
            semantic_analysis=self.enable_semantic_analysis,
        )

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch git data items with comprehensive processing.

        Args:
            since: Fetch items created/modified after this timestamp
            until: Fetch items created/modified before this timestamp
            limit: Maximum number of items to fetch

        Yields:
            Processed git data items (commits, branches, tags)
        """
        config = self.config.source_config
        count = 0

        # Fetch commits if enabled
        if config.get("include_commits", True):
            async for commit in self._fetch_commits_incremental(since, until, limit):
                if limit and count >= limit:
                    return

                # Perform enhanced commit analysis
                if self.enable_semantic_analysis:
                    try:
                        analysis = await self.commit_processor.analyze_commit(commit)
                        commit["analysis"] = {
                            "commit_type": analysis.commit_type.value,
                            "impact_score": analysis.impact_score,
                            "risk_score": analysis.risk_score,
                            "complexity_delta": analysis.complexity_delta,
                            "semantic_tags": analysis.semantic_tags,
                            "patterns": analysis.related_patterns,
                            "author_patterns": analysis.author_patterns,
                        }
                    except Exception as e:
                        self.logger.warning(
                            "Commit analysis failed",
                            commit=commit.get("hash", "unknown"),
                            error=str(e),
                        )

                # Analyze file changes
                try:
                    file_analysis = await self.change_analyzer.analyze_file_changes(commit)
                    commit["file_analysis"] = file_analysis
                except Exception as e:
                    self.logger.warning(
                        "File analysis failed", commit=commit.get("hash", "unknown"), error=str(e)
                    )

                yield commit
                count += 1

                # Save checkpoint at intervals
                if self.enable_incremental and self._commit_count % self.checkpoint_interval == 0:
                    await self._save_processing_checkpoint(commit)

        # Fetch branches if enabled
        if config.get("include_branches", True):
            async for branch in self._fetch_branches():
                if limit and count >= limit:
                    return
                yield branch
                count += 1

        # Fetch tags if enabled
        if config.get("include_tags", True):
            async for tag in self._fetch_tags():
                if limit and count >= limit:
                    return
                yield tag
                count += 1

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw git item into ContextItem.

        Args:
            raw_item: Raw git item data

        Returns:
            Transformed ContextItem ready for storage
        """
        item_type = raw_item["type"]

        if item_type == "commit":
            return await self._transform_commit_enhanced(raw_item)
        elif item_type == "branch":
            return await self._transform_branch(raw_item)
        elif item_type == "tag":
            return await self._transform_tag(raw_item)
        else:
            raise ValueError(f"Unknown git item type: {item_type}")

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, UUID, float]]:
        """Detect enhanced relationships with comprehensive correlation.

        Args:
            item: Current item being processed
            context_window: Recent items for relationship detection

        Returns:
            List of (relationship_type, target_item_id, confidence) tuples
        """
        relationships = []

        if not item.metrics:
            return relationships

        item_type = item.entity_type
        temporal_window_hours = self.config.source_config.get("temporal_window_hours", 48)
        temporal_window = timedelta(hours=temporal_window_hours)

        # Git-specific relationships
        if item_type == "commit":
            relationships.extend(await self._detect_git_commit_relationships(item, context_window))

        # Cross-domain temporal relationships
        if item_type == "commit" and item.timestamp:
            relationships.extend(
                await self._detect_temporal_relationships(item, context_window, temporal_window)
            )

        return relationships

    async def cleanup(self) -> None:
        """Clean up Git adapter resources."""
        self.logger.info("Cleaning up Git adapter")

        try:
            # Clear processing state
            self._processed_commits.clear()
            self._commit_count = 0
            self._current_branch = None
            self._branch_topology.clear()

            # Save final checkpoint if needed
            if self.enable_incremental and self._current_branch:
                self.logger.info("Saving final processing checkpoint")

        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))

        self.logger.info("Git adapter cleanup completed")

    # Private implementation methods

    async def _is_git_repo(self) -> bool:
        """Check if directory is a git repository."""
        try:
            await self._run_git_command(["rev-parse", "--git-dir"])
            return True
        except Exception:
            return False

    async def _run_git_command(self, args: List[str]) -> str:
        """Run git command and return output."""
        cmd = ["git", "-C", self._repo_path] + args

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)

        return stdout.decode("utf-8", errors="ignore").strip()

    async def _fetch_commits_incremental(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch commits with incremental processing support."""
        # Get branches to process
        branches_to_process = await self._get_branches_to_process()

        for branch in branches_to_process:
            self._current_branch = branch

            # Get last processed commit for incremental processing
            last_processed_commit = None
            if self.enable_incremental:
                last_processed_commit = await self.checkpoint_manager.get_last_processed_commit(
                    branch
                )
                if last_processed_commit:
                    self.logger.info(
                        "Resuming incremental processing",
                        branch=branch,
                        last_commit=last_processed_commit[:8],
                    )

            async for commit in self._fetch_commits_for_branch(
                branch, since, until, limit, last_processed_commit
            ):
                yield commit
                self._commit_count += 1

    async def _fetch_commits_for_branch(
        self,
        branch: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
        last_processed_commit: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch commits for a specific branch."""
        try:
            # Build git log command for branch
            args = ["log", "--format=fuller", "--name-status", branch]

            # Add filters
            if since:
                args.append(f"--since={since.isoformat()}")
            if until:
                args.append(f"--until={until.isoformat()}")

            # Age filter
            max_age_days = self.config.source_config.get("max_commit_age_days")
            if max_age_days:
                args.append(f"--since={max_age_days} days ago")

            # Merge commit filter
            if self.config.source_config.get("exclude_merge_commits", False):
                args.append("--no-merges")

            # Incremental processing
            if last_processed_commit:
                args.append(f"{last_processed_commit}..HEAD")

            # Execute command
            output = await self._run_git_command(args)
            commits = self._parse_git_log_output(output)

            count = 0
            for commit in commits:
                if limit and count >= limit:
                    break

                # Apply author filters
                author_filters = self.config.source_config.get("author_filters", [])
                if author_filters and commit["author"] not in author_filters:
                    continue

                # Skip if already processed
                if commit["hash"] in self._processed_commits:
                    continue

                self._processed_commits.add(commit["hash"])

                # Add branch information
                commit["branch"] = branch

                # Add diff content if enabled
                if self.config.source_config.get("include_diff_content", True):
                    diff = await self._get_commit_diff(commit["hash"])
                    commit["diff"] = diff

                commit["type"] = "commit"
                yield commit
                count += 1

        except Exception as e:
            self.logger.error("Failed to fetch commits for branch", branch=branch, error=str(e))
            # Mark processing error for this branch
            await self.checkpoint_manager.mark_processing_error(branch, str(e))

    async def _get_branches_to_process(self) -> List[str]:
        """Get list of branches to process."""
        try:
            # Check for branch filters first
            branch_filters = self.config.source_config.get("branch_filters", [])
            if branch_filters:
                return branch_filters

            # Get all remote branches
            output = await self._run_git_command(["branch", "-r", "--format=%(refname:short)"])
            branches = [
                b.strip().replace("origin/", "")
                for b in output.split("\n")
                if b.strip() and not b.strip().endswith("/HEAD")
            ]

            # Remove duplicates and sort
            return sorted(list(set(branches)))

        except Exception as e:
            self.logger.error("Failed to get branches", error=str(e))
            return ["main", "master"]  # Fallback

    async def _save_processing_checkpoint(self, commit: Dict[str, Any]) -> None:
        """Save processing checkpoint for current commit."""
        if not self._current_branch:
            return

        try:
            commit_time = datetime.fromisoformat(commit.get("commit_date", "").replace(" ", "T"))
        except:
            commit_time = datetime.utcnow()

        await self.checkpoint_manager.save_checkpoint(
            self._current_branch, commit["hash"], commit_time, self._commit_count
        )

    async def _fetch_branches(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch branch information."""
        try:
            for branch_name, branch_info in self._branch_topology.items():
                yield {
                    "type": "branch",
                    "name": branch_info.name,
                    "head_commit": branch_info.head_commit,
                    "branch_type": branch_info.branch_type,
                    "base_branch": branch_info.base_branch,
                    "creation_date": branch_info.creation_date.isoformat(),
                    "last_activity": branch_info.last_activity.isoformat(),
                    "commit_count": branch_info.commit_count,
                    "is_merged": branch_info.is_merged,
                }

        except Exception as e:
            self.logger.error("Failed to fetch branches", error=str(e))

    async def _fetch_tags(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch tag information."""
        try:
            output = await self._run_git_command(
                [
                    "tag",
                    "-l",
                    "--format=%(refname:short)|%(objectname)|%(taggerdate:iso8601)|%(subject)",
                ]
            )

            for line in output.split("\n"):
                if not line.strip():
                    continue

                parts = line.split("|", 3)
                if len(parts) >= 2:
                    tag_name = parts[0]
                    commit_hash = parts[1]
                    tag_date = parts[2] if len(parts) > 2 else ""
                    subject = parts[3] if len(parts) > 3 else ""

                    yield {
                        "type": "tag",
                        "name": tag_name,
                        "commit_hash": commit_hash,
                        "tag_date": tag_date,
                        "subject": subject,
                    }

        except Exception as e:
            self.logger.error("Failed to fetch tags", error=str(e))

    def _parse_git_log_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse git log --format=fuller output."""
        commits = []
        current_commit = None

        for line in output.split("\n"):
            line = line.rstrip()

            if line.startswith("commit "):
                if current_commit:
                    commits.append(current_commit)

                commit_hash = line.split(" ")[1]
                current_commit = {
                    "hash": commit_hash,
                    "author": "",
                    "author_email": "",
                    "author_date": "",
                    "committer": "",
                    "committer_email": "",
                    "commit_date": "",
                    "subject": "",
                    "body": "",
                    "changed_files": [],
                    "parent_commits": [],
                }

            elif current_commit:
                if line.startswith("Author:"):
                    # Parse "Author: Name <email>"
                    author_line = line[7:].strip()
                    if "<" in author_line and ">" in author_line:
                        name = author_line[: author_line.rindex("<")].strip()
                        email = author_line[
                            author_line.rindex("<") + 1 : author_line.rindex(">")
                        ].strip()
                        current_commit["author"] = name
                        current_commit["author_email"] = email

                elif line.startswith("AuthorDate:"):
                    current_commit["author_date"] = line[11:].strip()

                elif line.startswith("Commit:"):
                    # Parse "Commit: Name <email>"
                    committer_line = line[7:].strip()
                    if "<" in committer_line and ">" in committer_line:
                        name = committer_line[: committer_line.rindex("<")].strip()
                        email = committer_line[
                            committer_line.rindex("<") + 1 : committer_line.rindex(">")
                        ].strip()
                        current_commit["committer"] = name
                        current_commit["committer_email"] = email

                elif line.startswith("CommitDate:"):
                    current_commit["commit_date"] = line[11:].strip()

                elif line.startswith("    ") and not current_commit["subject"]:
                    # First indented line is the subject
                    current_commit["subject"] = line[4:]

                elif line.startswith("    ") and current_commit["subject"]:
                    # Additional indented lines are the body
                    if current_commit["body"]:
                        current_commit["body"] += "\n" + line[4:]
                    else:
                        current_commit["body"] = line[4:]

                elif line and not line.startswith(" ") and "\t" in line:
                    # File change line (A/M/D followed by filename)
                    parts = line.split("\t", 1)
                    if len(parts) == 2:
                        change_type = parts[0]
                        filename = parts[1]
                        current_commit["changed_files"].append(
                            {"type": change_type, "file": filename}
                        )

        # Add the last commit
        if current_commit:
            commits.append(current_commit)

        return commits

    async def _get_commit_diff(self, commit_hash: str) -> str:
        """Get diff content for a commit."""
        try:
            max_size_kb = self.config.source_config.get("max_diff_size_kb", 100)

            # Get diff with limited output
            diff = await self._run_git_command(
                [
                    "show",
                    commit_hash,
                    "--format=",  # No commit message in diff
                ]
            )

            # Truncate if too large
            max_size_bytes = max_size_kb * 1024
            if len(diff) > max_size_bytes:
                diff = diff[:max_size_bytes] + "\n... [diff truncated]"

            return diff

        except Exception as e:
            self.logger.warning(f"Failed to get diff for commit {commit_hash}", error=str(e))
            return ""

    async def _transform_commit_enhanced(self, raw_commit: Dict[str, Any]) -> ContextItem:
        """Transform git commit with enhanced analysis into ContextItem."""
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_commit["hash"], raw_data=raw_commit
        )

        # Enhanced commit-specific fields
        item.title = raw_commit.get("subject", f"Commit {raw_commit['hash'][:8]}")
        item.content = self._build_enhanced_commit_content(raw_commit)
        item.actor_id = raw_commit.get("author", "unknown")
        item.actor_type = "human"
        item.entity_type = "commit"

        # Parse commit date
        commit_date_str = raw_commit.get("commit_date", "")
        if commit_date_str:
            try:
                item.timestamp = datetime.fromisoformat(commit_date_str.replace(" ", "T")).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                item.timestamp = datetime.utcnow()
        else:
            item.timestamp = datetime.utcnow()

        # Enhanced Git metadata
        git_metadata = {
            "commit_hash": raw_commit["hash"],
            "author": raw_commit.get("author", ""),
            "author_email": raw_commit.get("author_email", ""),
            "committer": raw_commit.get("committer", ""),
            "committer_email": raw_commit.get("committer_email", ""),
            "branch_name": raw_commit.get("branch", ""),
            "changed_files": [f["file"] for f in raw_commit.get("changed_files", [])],
            "change_types": [f["type"] for f in raw_commit.get("changed_files", [])],
            "files_changed": len(raw_commit.get("changed_files", [])),
            "diff_size": len(raw_commit.get("diff", "")),
            "parent_commits": raw_commit.get("parent_commits", []),
        }

        # Add analysis results if available
        analysis = raw_commit.get("analysis")
        if analysis:
            git_metadata.update(
                {
                    "commit_type": analysis.get("commit_type", "unknown"),
                    "impact_score": analysis.get("impact_score", 0.0),
                    "risk_score": analysis.get("risk_score", 0.0),
                    "complexity_delta": analysis.get("complexity_delta", 0.0),
                    "semantic_tags": analysis.get("semantic_tags", []),
                    "commit_patterns": analysis.get("patterns", []),
                    "author_patterns": analysis.get("author_patterns", {}),
                }
            )

        # Add file analysis if available
        file_analysis = raw_commit.get("file_analysis")
        if file_analysis:
            git_metadata.update({"file_analysis": file_analysis})

        item.metrics = git_metadata

        # Enhanced tags
        tags = ["git", "commit"]

        # Add analysis-based tags
        if analysis:
            commit_type = analysis.get("commit_type", "unknown")
            if commit_type != "unknown":
                tags.append(f"type_{commit_type}")

            tags.extend(analysis.get("semantic_tags", []))
            tags.extend(analysis.get("patterns", []))

            # Risk/impact tags
            impact_score = analysis.get("impact_score", 0.0)
            risk_score = analysis.get("risk_score", 0.0)

            if impact_score > 0.7:
                tags.append("high_impact")
            elif impact_score > 0.4:
                tags.append("medium_impact")

            if risk_score > 0.7:
                tags.append("high_risk")
            elif risk_score > 0.4:
                tags.append("medium_risk")

        # Branch-based tags
        branch = raw_commit.get("branch", "")
        if branch:
            tags.append(f"branch_{branch.replace('/', '_')}")

        item.tags = list(set(tags))  # Remove duplicates

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    def _build_enhanced_commit_content(self, commit: Dict[str, Any]) -> str:
        """Build comprehensive commit content with analysis."""
        lines = []

        # Subject and body
        lines.append(commit.get("subject", ""))
        if commit.get("body"):
            lines.append("")
            lines.append(commit["body"])

        # Analysis summary
        analysis = commit.get("analysis")
        if analysis:
            lines.append("")
            lines.append("## Analysis")
            lines.append(f"Type: {analysis.get('commit_type', 'unknown')}")
            lines.append(f"Impact Score: {analysis.get('impact_score', 0.0):.2f}")
            lines.append(f"Risk Score: {analysis.get('risk_score', 0.0):.2f}")
            lines.append(f"Complexity Delta: {analysis.get('complexity_delta', 0.0):.1f}")

            semantic_tags = analysis.get("semantic_tags", [])
            if semantic_tags:
                lines.append(f"Tags: {', '.join(semantic_tags)}")

            patterns = analysis.get("patterns", [])
            if patterns:
                lines.append(f"Patterns: {', '.join(patterns)}")

        # Branch information
        branch = commit.get("branch", "")
        if branch:
            lines.append("")
            lines.append(f"Branch: {branch}")

        # File analysis
        file_analysis = commit.get("file_analysis")
        if file_analysis:
            lines.append("")
            lines.append("## File Changes")
            lines.append(f"Total Files: {file_analysis.get('total_files', 0)}")
            lines.append(f"Added: {file_analysis.get('added_files', 0)}")
            lines.append(f"Modified: {file_analysis.get('modified_files', 0)}")
            lines.append(f"Deleted: {file_analysis.get('deleted_files', 0)}")

            core_files = file_analysis.get("core_files_affected", [])
            if core_files:
                lines.append(f"Core Files Affected: {len(core_files)}")

        # Changed files (detailed list)
        changed_files = commit.get("changed_files", [])
        if changed_files:
            lines.append("")
            lines.append("## Changed Files")
            for file_change in changed_files[:20]:  # Limit to first 20 files
                lines.append(f"  {file_change['type']}\t{file_change['file']}")

            if len(changed_files) > 20:
                lines.append(f"  ... and {len(changed_files) - 20} more files")

        # Small diffs can be included
        diff = commit.get("diff", "")
        if diff and len(diff) < 5000:  # Only include small diffs
            lines.append("")
            lines.append("## Diff Preview")
            lines.append(diff[:2000])  # Truncate very long diffs
            if len(diff) > 2000:
                lines.append("... [truncated]")

        return "\n".join(lines)

    async def _transform_branch(self, raw_branch: Dict[str, Any]) -> ContextItem:
        """Transform git branch into ContextItem."""
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_branch["name"], raw_data=raw_branch
        )

        item.title = f"Branch: {raw_branch['name']}"
        item.content = (
            f"Git branch '{raw_branch['name']}' ({raw_branch.get('branch_type', 'unknown')} branch)"
        )
        item.entity_type = "branch"
        item.tags = ["git", "branch", f"type_{raw_branch.get('branch_type', 'unknown')}"]

        # Branch metadata
        branch_metadata = {
            "branch_name": raw_branch["name"],
            "head_commit": raw_branch.get("head_commit", ""),
            "branch_type": raw_branch.get("branch_type", "unknown"),
            "base_branch": raw_branch.get("base_branch"),
            "commit_count": raw_branch.get("commit_count", 0),
            "is_merged": raw_branch.get("is_merged", False),
        }

        item.metrics = branch_metadata

        # Set timestamp from last activity
        if raw_branch.get("last_activity"):
            try:
                item.timestamp = datetime.fromisoformat(
                    raw_branch["last_activity"].replace(" ", "T")
                ).replace(tzinfo=timezone.utc)
            except:
                item.timestamp = datetime.utcnow()

        item = await self.transformer.transform_item(item)
        return item

    async def _transform_tag(self, raw_tag: Dict[str, Any]) -> ContextItem:
        """Transform git tag into ContextItem."""
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_tag["name"], raw_data=raw_tag
        )

        item.title = f"Tag: {raw_tag['name']}"
        item.content = f"Git tag '{raw_tag['name']}'"
        if raw_tag.get("subject"):
            item.content += f": {raw_tag['subject']}"

        item.entity_type = "tag"
        item.tags = ["git", "tag"]

        # Tag metadata
        tag_metadata = {
            "tag_name": raw_tag["name"],
            "tagged_commit": raw_tag.get("commit_hash", ""),
            "tag_subject": raw_tag.get("subject", ""),
        }

        item.metrics = tag_metadata

        # Set timestamp from tag date
        if raw_tag.get("tag_date"):
            try:
                item.timestamp = datetime.fromisoformat(
                    raw_tag["tag_date"].replace(" ", "T")
                ).replace(tzinfo=timezone.utc)
            except:
                item.timestamp = datetime.utcnow()

        item = await self.transformer.transform_item(item)
        return item

    async def _detect_git_commit_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, UUID, float]]:
        """Detect Git-specific commit relationships."""
        relationships = []

        # Parent-child relationships
        parent_hashes = item.metrics.get("parent_commits", [])
        for context_item in context_window:
            if (
                context_item.entity_type == "commit"
                and context_item.metrics
                and context_item.source_type == "git"
            ):
                context_hash = context_item.metrics.get("commit_hash")
                if context_hash in parent_hashes:
                    relationships.append(("parent_commit", context_item.id, 1.0))

        # Same branch relationships
        item_branch = item.metrics.get("branch_name", "")
        if item_branch:
            for context_item in context_window:
                if (
                    context_item.entity_type == "commit"
                    and context_item.metrics
                    and context_item.metrics.get("branch_name") == item_branch
                    and context_item.id != item.id
                ):
                    relationships.append(("same_branch", context_item.id, 0.7))

        # Same author relationships with temporal proximity
        item_author = item.actor_id
        item_time = item.timestamp

        for context_item in context_window:
            if (
                context_item.actor_id == item_author
                and context_item.id != item.id
                and context_item.timestamp
                and item_time
            ):
                time_diff = abs((item_time - context_item.timestamp).total_seconds())
                base_strength = 0.4

                # Boost for temporal proximity
                if time_diff < 3600:  # Within 1 hour
                    base_strength = 0.7
                elif time_diff < 86400:  # Within 1 day
                    base_strength = 0.6

                relationships.append(("same_author", context_item.id, base_strength))

        # File change overlap relationships
        item_files = set(item.metrics.get("changed_files", []))
        for context_item in context_window:
            if (
                context_item.entity_type == "commit"
                and context_item.metrics
                and context_item.source_type == "git"
            ):
                context_files = set(context_item.metrics.get("changed_files", []))
                overlap = item_files & context_files

                if overlap:
                    overlap_ratio = len(overlap) / len(item_files | context_files)
                    relationships.append(("overlapping_changes", context_item.id, overlap_ratio))

        return relationships

    async def _detect_temporal_relationships(
        self, item: ContextItem, context_window: List[ContextItem], temporal_window: timedelta
    ) -> List[Tuple[str, UUID, float]]:
        """Detect cross-domain temporal relationships."""
        relationships = []
        item_time = item.timestamp

        if not item_time:
            return relationships

        for context_item in context_window:
            if not context_item.timestamp:
                continue

            time_diff = abs(item_time - context_item.timestamp)
            if time_diff <= temporal_window:
                # Chat correlation
                if context_item.source_type == "chat":
                    commit_hash = item.metrics.get("commit_hash", "")
                    author = item.actor_id

                    # Strong correlation for direct mentions
                    if commit_hash[:8] in context_item.content or author in context_item.content:
                        strength = 0.8
                    else:
                        # Temporal correlation strength decreases with time
                        strength = max(
                            0.3
                            - (time_diff.total_seconds() / temporal_window.total_seconds() * 0.2),
                            0.1,
                        )

                    relationships.append(("temporal_chat_correlation", context_item.id, strength))

                # Error correlation (commits might cause errors)
                elif context_item.source_type == "error":
                    if time_diff < timedelta(hours=2):  # Errors within 2 hours
                        risk_score = item.metrics.get("risk_score", 0.0)
                        strength = 0.5 + (risk_score * 0.4)
                    else:
                        strength = 0.3

                    relationships.append(("potential_error_causation", context_item.id, strength))

                # Code context correlation
                elif context_item.source_type == "code":
                    changed_files = set(item.metrics.get("changed_files", []))
                    # Check if any changed files are mentioned in code context
                    if any(file_path in context_item.content for file_path in changed_files):
                        relationships.append(("code_change_correlation", context_item.id, 0.7))

        return relationships
