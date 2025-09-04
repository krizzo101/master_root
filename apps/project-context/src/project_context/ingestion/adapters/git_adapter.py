"""Enhanced Git history adapter with comprehensive commit analysis and incremental processing."""

import asyncio
import hashlib
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple
from uuid import UUID

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class ProcessingStatus(Enum):
    """Git processing status."""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class CommitType(Enum):
    """Commit classification types."""

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
    """Results of comprehensive commit analysis."""

    commit_hash: str
    commit_type: CommitType
    impact_score: float  # 0.0 to 1.0
    risk_score: float  # 0.0 to 1.0
    complexity_delta: float
    files_impacted: List[str]
    semantic_tags: List[str]
    related_patterns: List[str]
    author_patterns: Dict[str, Any]


@dataclass
class BranchInfo:
    """Branch topology information."""

    name: str
    head_commit: str
    base_branch: Optional[str]
    branch_type: str  # 'feature', 'hotfix', 'release', 'main'
    creation_date: datetime
    last_activity: datetime
    commit_count: int
    is_merged: bool
    merge_commit: Optional[str]


@dataclass
class MergeInfo:
    """Merge commit analysis."""

    merge_commit_hash: str
    source_branch: str
    target_branch: str
    parent_commits: List[str]
    conflicts_resolved: bool
    merge_strategy: str
    files_affected: List[str]
    impact_score: float


@dataclass
class ProcessingCheckpoint:
    """Git processing checkpoint."""

    repository_path: str
    branch_name: str
    last_processed_commit: str
    last_processed_timestamp: datetime
    commit_count: int
    status: ProcessingStatus
    error_message: Optional[str] = None


class GitCheckpointManager:
    """Manages processing checkpoints for incremental git history ingestion."""

    def __init__(self, config: AdapterConfig, database_connection=None):
        self.config = config
        self.db = database_connection
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="GitCheckpointManager")

    async def get_last_processed_commit(self, branch: str) -> Optional[str]:
        """Get the last processed commit hash for a branch."""
        if not self.db:
            return None

        try:
            query = """
                SELECT last_processed_commit
                FROM git_processing_checkpoints
                WHERE repository_path = $1 AND branch_name = $2
                ORDER BY updated_at DESC LIMIT 1
            """
            result = await self.db.fetchrow(query, self.repository_path, branch)
            return result["last_processed_commit"] if result else None
        except Exception as e:
            self.logger.error("Failed to get last processed commit", error=str(e))
            return None

    async def save_checkpoint(
        self, branch: str, commit_hash: str, timestamp: datetime, commit_count: int = 0
    ):
        """Save processing checkpoint for a branch."""
        if not self.db:
            return

        try:
            query = """
                INSERT INTO git_processing_checkpoints
                (repository_path, branch_name, last_processed_commit, last_processed_timestamp, commit_count, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
                ON CONFLICT (repository_path, branch_name)
                DO UPDATE SET
                    last_processed_commit = EXCLUDED.last_processed_commit,
                    last_processed_timestamp = EXCLUDED.last_processed_timestamp,
                    commit_count = EXCLUDED.commit_count,
                    updated_at = NOW()
            """
            await self.db.execute(
                query,
                self.repository_path,
                branch,
                commit_hash,
                timestamp,
                commit_count,
            )
            self.logger.info("Checkpoint saved", branch=branch, commit=commit_hash[:8])
        except Exception as e:
            self.logger.error("Failed to save checkpoint", error=str(e))


class CommitProcessor:
    """Advanced commit analysis with semantic understanding and impact assessment."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.logger = logger.bind(component="CommitProcessor")

        # Commit type patterns
        self.commit_patterns = {
            CommitType.FEATURE: ["feat", "feature", "add", "implement", "create"],
            CommitType.BUGFIX: ["fix", "bug", "issue", "resolve", "patch"],
            CommitType.HOTFIX: ["hotfix", "urgent", "critical", "emergency"],
            CommitType.REFACTOR: ["refactor", "restructure", "reorganize", "cleanup"],
            CommitType.DOCUMENTATION: ["doc", "readme", "comment", "docs"],
            CommitType.TEST: ["test", "spec", "coverage", "unittest"],
            CommitType.MERGE: ["merge", "pull request", "pr"],
            CommitType.REVERT: ["revert", "rollback", "undo"],
            CommitType.CHORE: ["chore", "update", "upgrade", "dependency"],
        }

    async def analyze_commit(self, commit_data: Dict) -> CommitAnalysis:
        """Perform comprehensive commit analysis."""
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

            # Detect patterns
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
                "Commit analysis failed",
                commit=commit_data.get("hash", "unknown"),
                error=str(e),
            )
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

    def _classify_commit_type(
        self, message: str, changed_files: List[Dict]
    ) -> CommitType:
        """Classify commit type based on message and changed files."""
        # Check for merge commits
        if len(changed_files) > 20 and "merge" in message:
            return CommitType.MERGE

        # Check message patterns
        for commit_type, patterns in self.commit_patterns.items():
            if any(pattern in message for pattern in patterns):
                return commit_type

        # Check file patterns
        file_extensions = {
            f["file"].split(".")[-1].lower() for f in changed_files if "." in f["file"]
        }

        if {"md", "txt", "rst"} & file_extensions:
            return CommitType.DOCUMENTATION

        if {"test", "spec"} & {f["file"].split("/")[-1].lower() for f in changed_files}:
            return CommitType.TEST

        return CommitType.UNKNOWN

    async def _calculate_impact_score(self, commit_data: Dict) -> float:
        """Calculate the impact score of a commit on the codebase."""
        changed_files = commit_data.get("changed_files", [])
        diff_content = commit_data.get("diff", "")

        # Base score from number of files
        file_score = min(len(changed_files) / 10.0, 1.0)

        # Score from diff size
        diff_score = min(len(diff_content) / 10000.0, 1.0)

        # Score from file types (core files have higher impact)
        core_files = sum(1 for f in changed_files if self._is_core_file(f["file"]))
        core_score = min(core_files / 5.0, 1.0)

        # Combine scores
        impact_score = file_score * 0.3 + diff_score * 0.4 + core_score * 0.3

        return min(impact_score, 1.0)

    def _calculate_risk_score(self, commit_data: Dict, impact_score: float) -> float:
        """Calculate risk score for the commit."""
        changed_files = commit_data.get("changed_files", [])
        message = commit_data.get("subject", "").lower()

        # High-risk indicators
        risk_factors = 0.0

        # Database schema changes
        if any(
            "migration" in f["file"] or "schema" in f["file"] for f in changed_files
        ):
            risk_factors += 0.3

        # Configuration changes
        if any(
            f["file"].endswith((".config", ".env", ".yml", ".yaml"))
            for f in changed_files
        ):
            risk_factors += 0.2

        # Critical keywords
        critical_keywords = ["critical", "urgent", "hotfix", "emergency"]
        if any(keyword in message for keyword in critical_keywords):
            risk_factors += 0.2

        # Large number of deletions
        total_deletions = sum(1 for f in changed_files if f.get("type") == "D")
        if total_deletions > 5:
            risk_factors += 0.2

        # Combine with impact score
        risk_score = min(risk_factors + (impact_score * 0.3), 1.0)

        return risk_score

    def _calculate_complexity_delta(self, changed_files: List[Dict]) -> float:
        """Calculate complexity change from the commit."""
        complexity_delta = 0.0

        for file_change in changed_files:
            file_path = file_change["file"]
            change_type = file_change.get("type", "M")

            if change_type == "A":  # Added
                complexity_delta += 1.0
            elif change_type == "D":  # Deleted
                complexity_delta -= 0.5
            elif change_type == "M":  # Modified
                complexity_delta += 0.1

            # Weight by file type
            if file_path.endswith((".py", ".js", ".ts", ".java", ".cpp", ".c")):
                complexity_delta *= 1.5
            elif file_path.endswith((".md", ".txt", ".rst")):
                complexity_delta *= 0.5

        return complexity_delta

    def _extract_semantic_tags(
        self, message: str, changed_files: List[Dict]
    ) -> List[str]:
        """Extract semantic tags from commit."""
        tags = []

        # From message
        if "breaking" in message:
            tags.append("breaking_change")
        if "security" in message:
            tags.append("security")
        if "performance" in message:
            tags.append("performance")

        # From files
        file_types = {
            f["file"].split(".")[-1].lower() for f in changed_files if "." in f["file"]
        }
        tags.extend(
            f"language_{ext}"
            for ext in file_types
            if ext in ["py", "js", "ts", "java", "go"]
        )

        return tags

    def _detect_commit_patterns(self, commit_data: Dict) -> List[str]:
        """Detect patterns in commit."""
        patterns = []

        # Time-based patterns
        try:
            commit_time = datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            )
            if commit_time.hour >= 22 or commit_time.hour <= 6:
                patterns.append("late_night_commit")
        except:
            pass

        # File pattern analysis
        changed_files = [f["file"] for f in commit_data.get("changed_files", [])]
        if len(changed_files) == 1:
            patterns.append("single_file_change")
        elif len(changed_files) > 20:
            patterns.append("massive_change")

        return patterns

    def _analyze_author_patterns(self, commit_data: Dict) -> Dict[str, Any]:
        """Analyze author-specific patterns."""
        try:
            commit_time = datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            )
            hour = commit_time.hour
        except:
            hour = None

        return {
            "author": commit_data.get("author", ""),
            "commit_time_hour": hour,
            "message_length": len(
                commit_data.get("subject", "") + commit_data.get("body", "")
            ),
        }

    def _is_core_file(self, file_path: str) -> bool:
        """Check if file is considered core to the application."""
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


class CodeChangeAnalyzer:
    """Code change analyzer for detailed diff analysis."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="CodeChangeAnalyzer")

    async def analyze_file_changes(self, commit_data: Dict) -> Dict[str, Any]:
        """Analyze file changes in detail."""
        changed_files = commit_data.get("changed_files", [])
        analysis = {
            "total_files": len(changed_files),
            "added_files": sum(1 for f in changed_files if f.get("type") == "A"),
            "modified_files": sum(1 for f in changed_files if f.get("type") == "M"),
            "deleted_files": sum(1 for f in changed_files if f.get("type") == "D"),
            "file_types": {},
            "core_files_affected": [],
        }

        # Analyze file types
        for file_change in changed_files:
            file_path = file_change["file"]
            if "." in file_path:
                ext = file_path.split(".")[-1].lower()
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

            if self._is_core_file(file_path):
                analysis["core_files_affected"].append(file_path)

        return analysis

    def _is_core_file(self, file_path: str) -> bool:
        """Check if file is considered core to the application."""
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
        self.config = config
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="GitRepositoryScanner")

    async def scan_branches(self) -> Dict[str, BranchInfo]:
        """Scan and map all branches in the repository."""
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
                        last_activity = datetime.fromisoformat(
                            parts[2].replace(" ", "T")
                        )
                    except:
                        last_activity = datetime.utcnow()

                    # Get basic branch info
                    branch_info = BranchInfo(
                        name=branch_name,
                        head_commit=head_commit,
                        base_branch=None,
                        branch_type=self._classify_branch_type(branch_name),
                        creation_date=last_activity,
                        last_activity=last_activity,
                        commit_count=0,
                        is_merged=False,
                        merge_commit=None,
                    )
                    branches[branch_name] = branch_info

            return branches

        except Exception as e:
            self.logger.error("Failed to scan branches", error=str(e))
            return {}

    def _classify_branch_type(self, branch_name: str) -> str:
        """Classify branch type based on naming conventions."""
        name_lower = branch_name.lower()

        if name_lower in ["main", "master", "trunk"]:
            return "main"
        elif name_lower.startswith(("feature/", "feat/")):
            return "feature"
        elif name_lower.startswith(("hotfix/", "fix/")):
            return "hotfix"
        elif name_lower.startswith(("release/", "rel/")):
            return "release"
        elif name_lower.startswith("develop"):
            return "develop"
        else:
            return "unknown"

    async def _run_git_command(self, args: List[str]) -> str:
        """Run git command and return output."""
        cmd = ["git", "-C", self.repository_path] + args

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, stdout, stderr
                )

            return stdout.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            self.logger.error(f"Git command failed: {' '.join(cmd)}", error=str(e))
            raise


class GitAdapter(BaseAdapter):
    """Enhanced Git adapter with comprehensive commit analysis and incremental processing.

    Features:
    - Incremental commit processing with checkpoint management
    - Advanced commit analysis and metadata extraction
    - Branch topology mapping and merge detection
    - Author relationship tracking and contribution analysis
    - File change correlation and impact analysis
    - Performance optimization through parallel processing
    """

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for enhanced git adapter."""
        return AdapterConfig(
            adapter_id="enhanced_git",
            source_type="git",
            batch_mode=BatchMode.BATCH,
            batch_size=500,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                "repository_path": ".",
                "enable_incremental": True,
                "checkpoint_interval": 100,
                "max_commits_per_batch": 1000,
                "enable_semantic_analysis": True,
                "enable_impact_scoring": True,
                "enable_relationship_detection": True,
                "enable_branch_detection": True,
                "enable_merge_analysis": True,
                "track_file_impacts": True,
                "correlate_with_chat": True,
                "correlate_with_errors": True,
                "temporal_window_hours": 48,
                "parallel_processing": True,
                "max_parallel_workers": 4,
                "include_commits": True,
                "include_branches": True,
                "include_tags": True,
                "include_file_changes": True,
                "max_commit_age_days": None,
                "exclude_merge_commits": False,
                "include_diff_content": True,
                "max_diff_size_kb": 100,
                "author_filters": [],
                "branch_filters": [],
            },
        )

    def __init__(self, config: AdapterConfig, database_connection=None):
        """Initialize enhanced git adapter."""
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
        self.enable_semantic_analysis = config.source_config.get(
            "enable_semantic_analysis", True
        )
        self.enable_branch_detection = config.source_config.get(
            "enable_branch_detection", True
        )
        self.checkpoint_interval = config.source_config.get("checkpoint_interval", 100)

        # Processing state
        self._commit_count = 0
        self._current_branch = None

    async def initialize(self) -> None:
        """Initialize enhanced git adapter resources."""
        self.logger.info("Initializing enhanced git adapter")

        # Validate git repository
        if not await self._is_git_repo():
            raise ValueError(f"Not a git repository: {self._repo_path}")

        # Test git command availability
        try:
            await self._run_git_command(["--version"])
        except Exception as e:
            raise ValueError(f"Git command not available: {e}")

        # Initialize branch scanning if enabled
        if self.enable_branch_detection:
            try:
                branches = await self.repo_scanner.scan_branches()
                self.logger.info(
                    "Branch detection initialized", branch_count=len(branches)
                )
            except Exception as e:
                self.logger.warning(
                    "Branch detection initialization failed", error=str(e)
                )

        self.logger.info(
            "Enhanced git adapter initialized",
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
        """Fetch git data items with incremental processing support."""
        config = self.config.source_config
        count = 0

        # Fetch commits if enabled
        if config.get("include_commits", True):
            async for commit in self._fetch_commits_incremental(since, until, limit):
                if limit and count >= limit:
                    return

                # Perform commit analysis if enabled
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

                yield commit
                count += 1

                # Save checkpoint at intervals
                if (
                    self.enable_incremental
                    and self._commit_count % self.checkpoint_interval == 0
                ):
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
        """Transform raw git item into ContextItem with enhanced analysis."""
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
    ) -> List[tuple]:
        """Detect enhanced relationships with other git items and cross-domain context."""
        relationships = []

        if not item.metrics:
            return relationships

        item_type = item.entity_type

        # Parent-child relationships for commits
        if item_type == "commit":
            parent_hashes = item.metrics.get("parent_commits", [])

            for context_item in context_window:
                if context_item.entity_type != "commit" or not context_item.metrics:
                    continue

                context_hash = context_item.metrics.get("commit_hash")
                if context_hash in parent_hashes:
                    relationships.append(("parent_commit", context_item.id, 1.0))

                # Check if this commit is a parent of the context commit
                context_parents = context_item.metrics.get("parent_commits", [])
                item_hash = item.metrics.get("commit_hash")
                if item_hash in context_parents:
                    relationships.append(("child_commit", context_item.id, 1.0))

        # Enhanced branch relationships
        if item_type == "commit":
            item_branch = item.metrics.get(
                "branch_name", item.metrics.get("branch", "")
            )
            for context_item in context_window:
                if context_item.entity_type == "commit" and context_item.metrics:
                    context_branch = context_item.metrics.get(
                        "branch_name", context_item.metrics.get("branch", "")
                    )
                    if item_branch and context_branch and item_branch == context_branch:
                        relationships.append(("same_branch", context_item.id, 0.7))
                elif (
                    context_item.entity_type == "branch"
                    and context_item.source_id == item_branch
                ):
                    relationships.append(("on_branch", context_item.id, 0.9))

        # Enhanced author relationships with temporal proximity
        item_author = item.actor_id
        item_time = item.timestamp
        for context_item in context_window:
            if context_item.actor_id == item_author and context_item.id != item.id:
                base_strength = 0.4

                # Boost relationship strength for temporal proximity
                if context_item.timestamp and item_time:
                    time_diff = abs(
                        (item_time - context_item.timestamp).total_seconds()
                    )
                    if time_diff < 3600:  # Within 1 hour
                        base_strength = 0.7
                    elif time_diff < 86400:  # Within 1 day
                        base_strength = 0.6

                relationships.append(("same_author", context_item.id, base_strength))

        # Enhanced file change relationships with impact scoring
        if item_type == "commit":
            item_files = set(item.metrics.get("changed_files", []))
            item_impact = item.metrics.get("impact_score", 0.0)

            for context_item in context_window:
                if context_item.entity_type == "commit" and context_item.metrics:
                    context_files = set(context_item.metrics.get("changed_files", []))
                    if item_files & context_files:  # Intersection
                        overlap_ratio = len(item_files & context_files) / len(
                            item_files | context_files
                        )

                        # Boost relationship strength for high-impact commits
                        context_impact = context_item.metrics.get("impact_score", 0.0)
                        impact_boost = (item_impact + context_impact) / 2.0 * 0.3
                        final_strength = min(overlap_ratio + impact_boost, 1.0)

                        relationships.append(
                            ("overlapping_changes", context_item.id, final_strength)
                        )

        # Commit type relationships (similar types of commits)
        if item_type == "commit" and item.metrics.get("commit_type"):
            item_commit_type = item.metrics.get("commit_type")
            for context_item in context_window:
                if (
                    context_item.entity_type == "commit"
                    and context_item.metrics
                    and context_item.metrics.get("commit_type") == item_commit_type
                ):
                    relationships.append(("same_commit_type", context_item.id, 0.5))

        # Risk/impact correlation relationships
        if item_type == "commit":
            item_risk = item.metrics.get("risk_score", 0.0)
            item_impact = item.metrics.get("impact_score", 0.0)

            if item_risk > 0.7 or item_impact > 0.7:  # High risk/impact commits
                for context_item in context_window:
                    if context_item.entity_type == "commit" and context_item.metrics:
                        context_risk = context_item.metrics.get("risk_score", 0.0)
                        context_impact = context_item.metrics.get("impact_score", 0.0)

                        if context_risk > 0.7 or context_impact > 0.7:
                            strength = (
                                0.3 + (min(item_risk + item_impact, 2.0) / 2.0) * 0.3
                            )
                            relationships.append(
                                (
                                    "high_risk_impact_correlation",
                                    context_item.id,
                                    strength,
                                )
                            )

        # Cross-domain relationships (with chat, errors, code)
        temporal_window_hours = self.config.source_config.get(
            "temporal_window_hours", 48
        )
        temporal_window = timedelta(hours=temporal_window_hours)

        if item_type == "commit" and item_time:
            for context_item in context_window:
                if not context_item.timestamp:
                    continue

                time_diff = abs(item_time - context_item.timestamp)
                if time_diff <= temporal_window:
                    # Chat correlation
                    if context_item.source_type == "chat":
                        # Check for commit hash mentions or author mentions
                        commit_hash = item.metrics.get("commit_hash", "")
                        author = item.actor_id

                        if (
                            commit_hash[:8] in context_item.content
                            or author in context_item.content
                        ):
                            strength = 0.8
                        else:
                            # Temporal correlation
                            strength = max(
                                0.3
                                - (
                                    time_diff.total_seconds()
                                    / (temporal_window.total_seconds())
                                ),
                                0.1,
                            )

                        relationships.append(
                            ("temporal_chat_correlation", context_item.id, strength)
                        )

                    # Error correlation
                    elif context_item.source_type == "error":
                        # Higher correlation for commits that might have caused errors
                        if time_diff < timedelta(
                            hours=2
                        ):  # Errors within 2 hours of commit
                            risk_score = item.metrics.get("risk_score", 0.0)
                            strength = 0.5 + (risk_score * 0.4)
                        else:
                            strength = 0.3

                        relationships.append(
                            ("potential_error_causation", context_item.id, strength)
                        )

                    # Code context correlation
                    elif context_item.source_type == "code":
                        # Check if code context involves files changed in this commit
                        changed_files = set(item.metrics.get("changed_files", []))
                        if any(
                            file_path in context_item.content
                            for file_path in changed_files
                        ):
                            relationships.append(
                                ("code_change_correlation", context_item.id, 0.7)
                            )

        return relationships

    async def cleanup(self) -> None:
        """Clean up enhanced git adapter resources."""
        self.logger.info("Cleaning up enhanced git adapter")

        try:
            # Clear processing state
            self._processed_commits.clear()
            self._commit_count = 0
            self._current_branch = None

            # Save final checkpoint if needed
            if self.enable_incremental and self._current_branch:
                self.logger.info("Saving final processing checkpoint")

        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))

        self.logger.info("Enhanced git adapter cleanup completed")

    # Private methods

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

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, stdout, stderr
                )

            return stdout.decode("utf-8", errors="ignore").strip()

        except Exception as e:
            self.logger.error(f"Git command failed: {' '.join(cmd)}", error=str(e))
            raise

    async def _fetch_commits(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch commit history."""
        # Build git log command
        args = ["log", "--format=fuller", "--name-status"]

        # Add date filters
        if since:
            args.append(f"--since={since.isoformat()}")
        if until:
            args.append(f"--until={until.isoformat()}")

        # Add age filter
        max_age_days = self.config.source_config.get("max_commit_age_days")
        if max_age_days:
            args.append(f"--since={max_age_days} days ago")

        # Add merge commit filter
        if self.config.source_config.get("exclude_merge_commits", False):
            args.append("--no-merges")

        # Add branch filters
        branch_filters = self.config.source_config.get("branch_filters", [])
        if branch_filters:
            for branch in branch_filters:
                args.append(branch)
        else:
            args.append("--all")

        try:
            output = await self._run_git_command(args)

            # Parse git log output
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

                # Add diff content if enabled
                if self.config.source_config.get("include_diff_content", True):
                    diff = await self._get_commit_diff(commit["hash"])
                    commit["diff"] = diff

                commit["type"] = "commit"
                yield commit
                count += 1

        except Exception as e:
            self.logger.error("Failed to fetch commits", error=str(e))

    async def _fetch_commits_incremental(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch commits with incremental processing support."""

        # Get branches to process
        branch_filters = self.config.source_config.get("branch_filters", [])
        branches_to_process = (
            branch_filters if branch_filters else await self._get_all_branches()
        )

        for branch in branches_to_process:
            self._current_branch = branch

            # Get last processed commit for incremental processing
            last_processed_commit = None
            if self.enable_incremental:
                last_processed_commit = (
                    await self.checkpoint_manager.get_last_processed_commit(branch)
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

        # Build git log command for branch
        args = ["log", "--format=fuller", "--name-status", branch]

        # Add date filters
        if since:
            args.append(f"--since={since.isoformat()}")
        if until:
            args.append(f"--until={until.isoformat()}")

        # Add age filter
        max_age_days = self.config.source_config.get("max_commit_age_days")
        if max_age_days:
            args.append(f"--since={max_age_days} days ago")

        # Add merge commit filter
        if self.config.source_config.get("exclude_merge_commits", False):
            args.append("--no-merges")

        # If we have a last processed commit, start from there
        if last_processed_commit:
            args.append(f"{last_processed_commit}..HEAD")

        try:
            output = await self._run_git_command(args)

            # Parse git log output
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
            self.logger.error(
                "Failed to fetch commits for branch", branch=branch, error=str(e)
            )

    async def _get_all_branches(self) -> List[str]:
        """Get list of all branches."""
        try:
            output = await self._run_git_command(
                ["branch", "-r", "--format=%(refname:short)"]
            )
            branches = [line.strip() for line in output.split("\n") if line.strip()]

            # Filter out remote prefixes
            local_branches = []
            for branch in branches:
                if "/" in branch:
                    local_branches.append(branch.split("/")[-1])
                else:
                    local_branches.append(branch)

            return list(set(local_branches))  # Remove duplicates
        except Exception as e:
            self.logger.error("Failed to get branches", error=str(e))
            return ["main", "master"]  # Default fallback

    async def _save_processing_checkpoint(self, commit: Dict[str, Any]):
        """Save processing checkpoint for current commit."""
        if not self._current_branch:
            return

        try:
            commit_time = datetime.fromisoformat(
                commit.get("commit_date", "").replace(" ", "T")
            )
        except:
            commit_time = datetime.utcnow()

        await self.checkpoint_manager.save_checkpoint(
            self._current_branch, commit["hash"], commit_time, self._commit_count
        )

    async def _fetch_branches(self) -> AsyncIterator[Dict[str, Any]]:
        """Fetch branch information."""
        try:
            # Get local branches
            output = await self._run_git_command(
                [
                    "branch",
                    "-v",
                    "--format=%(refname:short) %(objectname) %(committerdate:iso8601) %(subject)",
                ]
            )

            for line in output.split("\n"):
                if not line.strip():
                    continue

                parts = line.split(" ", 3)
                if len(parts) >= 4:
                    branch_name = parts[0]
                    commit_hash = parts[1]
                    commit_date = parts[2]
                    subject = parts[3] if len(parts) > 3 else ""

                    yield {
                        "type": "branch",
                        "name": branch_name,
                        "commit_hash": commit_hash,
                        "last_commit_date": commit_date,
                        "last_commit_subject": subject,
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
                    "--format=%(refname:short) %(objectname) %(taggerdate:iso8601) %(subject)",
                ]
            )

            for line in output.split("\n"):
                if not line.strip():
                    continue

                parts = line.split(" ", 3)
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
                    f"--max-count={max_size_kb * 1024}",  # Limit output size
                ]
            )

            # Truncate if too large
            max_size_bytes = max_size_kb * 1024
            if len(diff) > max_size_bytes:
                diff = diff[:max_size_bytes] + "\n... [diff truncated]"

            return diff

        except Exception as e:
            self.logger.warning(
                f"Failed to get diff for commit {commit_hash}", error=str(e)
            )
            return ""

    async def _transform_commit(self, raw_commit: Dict[str, Any]) -> ContextItem:
        """Transform git commit into ContextItem."""
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_commit["hash"], raw_data=raw_commit
        )

        # Commit-specific fields
        item.title = raw_commit.get("subject", f"Commit {raw_commit['hash'][:8]}")
        item.content = self._build_commit_content(raw_commit)
        item.actor_id = raw_commit.get("author", "unknown")
        item.actor_type = "human"  # Git commits are typically from humans

        # Parse commit date
        commit_date_str = raw_commit.get("commit_date", "")
        if commit_date_str:
            try:
                item.timestamp = datetime.fromisoformat(
                    commit_date_str.replace(" ", "T")
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                item.timestamp = datetime.utcnow()
        else:
            item.timestamp = datetime.utcnow()

        # Git metadata
        git_metadata = {
            "commit_hash": raw_commit["hash"],
            "author": raw_commit.get("author", ""),
            "author_email": raw_commit.get("author_email", ""),
            "committer": raw_commit.get("committer", ""),
            "committer_email": raw_commit.get("committer_email", ""),
            "changed_files": [f["file"] for f in raw_commit.get("changed_files", [])],
            "change_types": [f["type"] for f in raw_commit.get("changed_files", [])],
            "diff_size": len(raw_commit.get("diff", "")),
            "parent_commits": raw_commit.get("parent_commits", []),
        }

        item.metrics = git_metadata
        item.entity_type = "commit"

        # Add tags based on commit characteristics
        tags = ["git", "commit"]

        # Add tags based on changed files
        changed_files = raw_commit.get("changed_files", [])
        if any(f["type"] == "A" for f in changed_files):
            tags.append("added_files")
        if any(f["type"] == "M" for f in changed_files):
            tags.append("modified_files")
        if any(f["type"] == "D" for f in changed_files):
            tags.append("deleted_files")

        # Add tags based on content
        subject = raw_commit.get("subject", "").lower()
        if "fix" in subject or "bug" in subject:
            tags.append("bugfix")
        if "feat" in subject or "feature" in subject:
            tags.append("feature")
        if "refactor" in subject:
            tags.append("refactoring")
        if "test" in subject:
            tags.append("testing")
        if "doc" in subject or "readme" in subject:
            tags.append("documentation")

        item.tags = tags

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    async def _transform_commit_enhanced(
        self, raw_commit: Dict[str, Any]
    ) -> ContextItem:
        """Transform git commit into ContextItem with enhanced analysis."""
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_commit["hash"], raw_data=raw_commit
        )

        # Commit-specific fields
        item.title = raw_commit.get("subject", f"Commit {raw_commit['hash'][:8]}")
        item.content = self._build_commit_content_enhanced(raw_commit)
        item.actor_id = raw_commit.get("author", "unknown")
        item.actor_type = "human"

        # Parse commit date
        commit_date_str = raw_commit.get("commit_date", "")
        if commit_date_str:
            try:
                item.timestamp = datetime.fromisoformat(
                    commit_date_str.replace(" ", "T")
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                item.timestamp = datetime.utcnow()
        else:
            item.timestamp = datetime.utcnow()

        # Enhanced Git metadata including analysis results
        git_metadata = {
            "commit_hash": raw_commit["hash"],
            "author": raw_commit.get("author", ""),
            "author_email": raw_commit.get("author_email", ""),
            "committer": raw_commit.get("committer", ""),
            "committer_email": raw_commit.get("committer_email", ""),
            "branch_name": raw_commit.get("branch", ""),
            "changed_files": [f["file"] for f in raw_commit.get("changed_files", [])],
            "change_types": [f["type"] for f in raw_commit.get("changed_files", [])],
            "files_changed_count": len(raw_commit.get("changed_files", [])),
            "diff_size": len(raw_commit.get("diff", "")),
            "parent_commits": raw_commit.get("parent_commits", []),
        }

        # Include analysis data if available
        if "analysis" in raw_commit:
            analysis = raw_commit["analysis"]
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

        item.metrics = git_metadata
        item.entity_type = "commit"

        # Enhanced tags based on analysis
        tags = ["git", "commit"]

        # Add analysis-based tags
        if "analysis" in raw_commit:
            analysis = raw_commit["analysis"]
            commit_type = analysis.get("commit_type", "unknown")
            if commit_type != "unknown":
                tags.append(commit_type)

            # Add semantic tags
            tags.extend(analysis.get("semantic_tags", []))

            # Add pattern-based tags
            patterns = analysis.get("patterns", [])
            tags.extend(patterns)

            # Add risk/impact based tags
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

        # Add traditional tags based on changed files
        changed_files = raw_commit.get("changed_files", [])
        if any(f["type"] == "A" for f in changed_files):
            tags.append("added_files")
        if any(f["type"] == "M" for f in changed_files):
            tags.append("modified_files")
        if any(f["type"] == "D" for f in changed_files):
            tags.append("deleted_files")

        # Add branch-based tags
        branch_name = raw_commit.get("branch", "")
        if branch_name:
            tags.append(f"branch_{branch_name.replace('/', '_')}")

        item.tags = list(set(tags))  # Remove duplicates

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    def _build_commit_content_enhanced(self, commit: Dict[str, Any]) -> str:
        """Build enhanced commit content with analysis information."""
        lines = []

        # Subject and body
        lines.append(commit.get("subject", ""))
        if commit.get("body"):
            lines.append("")
            lines.append(commit["body"])

        # Analysis information if available
        if "analysis" in commit:
            analysis = commit["analysis"]
            lines.append("")
            lines.append("=== Commit Analysis ===")
            lines.append(f"Type: {analysis.get('commit_type', 'unknown')}")
            lines.append(f"Impact Score: {analysis.get('impact_score', 0.0):.2f}")
            lines.append(f"Risk Score: {analysis.get('risk_score', 0.0):.2f}")
            lines.append(
                f"Complexity Delta: {analysis.get('complexity_delta', 0.0):.1f}"
            )

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

        # Changed files
        changed_files = commit.get("changed_files", [])
        if changed_files:
            lines.append("")
            lines.append("Changed files:")
            for file_change in changed_files[:20]:  # Limit to first 20 files
                lines.append(f"  {file_change['type']}\t{file_change['file']}")

            if len(changed_files) > 20:
                lines.append(f"  ... and {len(changed_files) - 20} more files")

        # Diff content (if available and not too large)
        diff = commit.get("diff", "")
        if diff and len(diff) < 10000:  # Only include small diffs in content
            lines.append("")
            lines.append("Diff:")
            lines.append(diff)

        return "\n".join(lines)

    async def _transform_branch(self, raw_branch: Dict[str, Any]) -> ContextItem:
        """Transform git branch into ContextItem."""
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_branch["name"], raw_data=raw_branch
        )

        item.title = f"Branch: {raw_branch['name']}"
        item.content = f"Git branch '{raw_branch['name']}'"
        item.entity_type = "branch"
        item.tags = ["git", "branch"]

        # Branch metadata
        branch_metadata = {
            "branch_name": raw_branch["name"],
            "head_commit": raw_branch.get("commit_hash", ""),
            "last_commit_subject": raw_branch.get("last_commit_subject", ""),
        }

        item.metrics = branch_metadata

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    async def _transform_tag(self, raw_tag: Dict[str, Any]) -> ContextItem:
        """Transform git tag into ContextItem."""
        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="git", source_id=raw_tag["name"], raw_data=raw_tag
        )

        item.title = f"Tag: {raw_tag['name']}"
        item.content = f"Git tag '{raw_tag['name']}'"
        item.entity_type = "tag"
        item.tags = ["git", "tag"]

        # Tag metadata
        tag_metadata = {
            "tag_name": raw_tag["name"],
            "tagged_commit": raw_tag.get("commit_hash", ""),
            "tag_subject": raw_tag.get("subject", ""),
        }

        item.metrics = tag_metadata

        # Apply transformations
        item = await self.transformer.transform_item(item)

        return item

    def _build_commit_content(self, commit: Dict[str, Any]) -> str:
        """Build comprehensive commit content."""
        lines = []

        # Subject and body
        lines.append(commit.get("subject", ""))
        if commit.get("body"):
            lines.append("")
            lines.append(commit["body"])

        # Changed files
        changed_files = commit.get("changed_files", [])
        if changed_files:
            lines.append("")
            lines.append("Changed files:")
            for file_change in changed_files[:20]:  # Limit to first 20 files
                lines.append(f"  {file_change['type']}\t{file_change['file']}")

            if len(changed_files) > 20:
                lines.append(f"  ... and {len(changed_files) - 20} more files")

        # Diff content (if available and not too large)
        diff = commit.get("diff", "")
        if diff and len(diff) < 10000:  # Only include small diffs in content
            lines.append("")
            lines.append("Diff:")
            lines.append(diff)

        return "\n".join(lines)
