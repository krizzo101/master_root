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

    def __init__(self, config: AdapterConfig, database_connection):
        self.config = config
        self.db = database_connection
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="GitCheckpointManager")

    async def get_last_processed_commit(self, branch: str) -> Optional[str]:
        """Get the last processed commit hash for a branch."""
        try:
            query = """
                SELECT last_processed_commit
                FROM git_processing_checkpoints
                WHERE repository_path = %s AND branch_name = %s
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
        try:
            query = """
                INSERT INTO git_processing_checkpoints
                (repository_path, branch_name, last_processed_commit, last_processed_timestamp, commit_count, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
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

    async def get_processing_state(self, branch: str) -> Optional[ProcessingCheckpoint]:
        """Get complete processing state for a branch."""
        try:
            query = """
                SELECT repository_path, branch_name, last_processed_commit,
                       last_processed_timestamp, commit_count, processing_status, last_error
                FROM git_processing_checkpoints
                WHERE repository_path = %s AND branch_name = %s
            """
            result = await self.db.fetchrow(query, self.repository_path, branch)

            if result:
                return ProcessingCheckpoint(
                    repository_path=result["repository_path"],
                    branch_name=result["branch_name"],
                    last_processed_commit=result["last_processed_commit"],
                    last_processed_timestamp=result["last_processed_timestamp"],
                    commit_count=result["commit_count"],
                    status=ProcessingStatus(result["processing_status"]),
                    error_message=result["last_error"],
                )
            return None
        except Exception as e:
            self.logger.error("Failed to get processing state", error=str(e))
            return None


class CommitAnalyzer:
    """Advanced commit analysis with semantic understanding and impact assessment."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.logger = logger.bind(component="CommitAnalyzer")

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
        # Simple heuristic based on file types and operations
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
        commit_time = datetime.fromisoformat(
            commit_data.get("commit_date", "").replace(" ", "T")
        )
        if commit_time.hour >= 22 or commit_time.hour <= 6:
            patterns.append("late_night_commit")

        # File pattern analysis
        changed_files = [f["file"] for f in commit_data.get("changed_files", [])]
        if len(changed_files) == 1:
            patterns.append("single_file_change")
        elif len(changed_files) > 20:
            patterns.append("massive_change")

        return patterns

    def _analyze_author_patterns(self, commit_data: Dict) -> Dict[str, Any]:
        """Analyze author-specific patterns."""
        return {
            "author": commit_data.get("author", ""),
            "commit_time_hour": datetime.fromisoformat(
                commit_data.get("commit_date", "").replace(" ", "T")
            ).hour
            if commit_data.get("commit_date")
            else None,
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


class BranchMergeDetector:
    """Sophisticated branch topology analysis and merge detection."""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.repository_path = config.source_config.get("repository_path", ".")
        self.logger = logger.bind(component="BranchMergeDetector")

    async def map_branch_topology(self) -> Dict[str, BranchInfo]:
        """Create comprehensive branch topology map."""
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
                if len(parts) >= 4:
                    branch_name = parts[0]
                    head_commit = parts[1]
                    last_activity = datetime.fromisoformat(parts[2].replace(" ", "T"))

                    # Get branch info
                    branch_info = await self._analyze_branch(
                        branch_name, head_commit, last_activity
                    )
                    branches[branch_name] = branch_info

            return branches

        except Exception as e:
            self.logger.error("Failed to map branch topology", error=str(e))
            return {}

    async def detect_merge_commits(self, commit_hash: str) -> Optional[MergeInfo]:
        """Detect and analyze merge commits."""
        try:
            # Check if commit is a merge commit
            parents = await self._run_git_command(
                ["rev-list", "--parents", "-n", "1", commit_hash]
            )

            parent_hashes = parents.split()[1:]  # Skip the commit hash itself

            if len(parent_hashes) < 2:
                return None  # Not a merge commit

            # Get merge commit details
            merge_info = await self._run_git_command(
                ["show", "--format=%s|%P", "--name-only", commit_hash]
            )

            lines = merge_info.split("\n")
            subject_and_parents = lines[0].split("|")
            subject = subject_and_parents[0]
            files_affected = [line for line in lines[1:] if line.strip()]

            # Detect source and target branches
            source_branch, target_branch = await self._detect_merge_branches(
                commit_hash, parent_hashes
            )

            return MergeInfo(
                merge_commit_hash=commit_hash,
                source_branch=source_branch or "unknown",
                target_branch=target_branch or "unknown",
                parent_commits=parent_hashes,
                conflicts_resolved=self._detect_conflicts_resolved(subject),
                merge_strategy=self._detect_merge_strategy(subject),
                files_affected=files_affected,
                impact_score=min(len(files_affected) / 10.0, 1.0),
            )

        except Exception as e:
            self.logger.error(
                "Failed to detect merge commit", commit=commit_hash, error=str(e)
            )
            return None

    async def _analyze_branch(
        self, branch_name: str, head_commit: str, last_activity: datetime
    ) -> BranchInfo:
        """Analyze individual branch characteristics."""
        try:
            # Get commit count
            commit_count_output = await self._run_git_command(
                ["rev-list", "--count", head_commit]
            )
            commit_count = int(commit_count_output.strip())

            # Detect branch type
            branch_type = self._classify_branch_type(branch_name)

            # Check if merged
            is_merged = await self._is_branch_merged(branch_name)

            # Get creation date (first commit on branch)
            creation_date = await self._get_branch_creation_date(branch_name)

            return BranchInfo(
                name=branch_name,
                head_commit=head_commit,
                base_branch=await self._detect_base_branch(branch_name),
                branch_type=branch_type,
                creation_date=creation_date,
                last_activity=last_activity,
                commit_count=commit_count,
                is_merged=is_merged,
                merge_commit=None,  # Would need additional analysis
            )

        except Exception as e:
            self.logger.error(
                "Branch analysis failed", branch=branch_name, error=str(e)
            )
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

    async def _detect_merge_branches(
        self, commit_hash: str, parent_hashes: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Detect source and target branches for a merge commit."""
        try:
            # This is a simplified implementation
            # In practice, would need more sophisticated branch detection
            source_branch = None
            target_branch = None

            # Try to find which branches contain the parent commits
            for parent in parent_hashes[:2]:  # Usually just 2 parents for merge
                branches = await self._run_git_command(
                    ["branch", "--contains", parent, "--format=%(refname:short)"]
                )
                branch_list = [b.strip() for b in branches.split("\n") if b.strip()]

                if not source_branch and branch_list:
                    source_branch = branch_list[0]
                elif not target_branch and branch_list:
                    target_branch = branch_list[0]

            return source_branch, target_branch

        except Exception:
            return None, None

    def _detect_conflicts_resolved(self, subject: str) -> bool:
        """Detect if merge commit resolved conflicts."""
        conflict_indicators = ["conflict", "resolve", "fix merge"]
        return any(indicator in subject.lower() for indicator in conflict_indicators)

    def _detect_merge_strategy(self, subject: str) -> str:
        """Detect merge strategy used."""
        if "fast-forward" in subject.lower():
            return "fast-forward"
        elif "squash" in subject.lower():
            return "squash"
        else:
            return "merge"

    async def _is_branch_merged(self, branch_name: str) -> bool:
        """Check if branch has been merged."""
        try:
            merged_branches = await self._run_git_command(["branch", "--merged"])
            return branch_name in merged_branches
        except Exception:
            return False

    async def _get_branch_creation_date(self, branch_name: str) -> datetime:
        """Get the creation date of a branch."""
        try:
            # Get first commit on branch
            first_commit = await self._run_git_command(
                ["rev-list", "--reverse", branch_name, "|", "head", "-1"]
            )

            commit_date = await self._run_git_command(
                ["show", "-s", "--format=%ci", first_commit.strip()]
            )

            return datetime.fromisoformat(commit_date.strip().replace(" ", "T"))
        except Exception:
            return datetime.utcnow()

    async def _detect_base_branch(self, branch_name: str) -> Optional[str]:
        """Detect the base branch for a feature branch."""
        try:
            # Simplified detection - would need more sophisticated logic
            if branch_name in ["main", "master", "develop"]:
                return None

            # Try to find common ancestor with main branches
            for base in ["main", "master", "develop"]:
                try:
                    await self._run_git_command(["merge-base", branch_name, base])
                    return base
                except Exception:
                    continue

            return None
        except Exception:
            return None

    async def _run_git_command(self, args: List[str]) -> str:
        """Run git command and return output."""
        cmd = ["git", "-C", self.repository_path] + args

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)

        return stdout.decode("utf-8", errors="ignore").strip()


class EnhancedGitAdapter(BaseAdapter):
    """Enhanced Git adapter with incremental processing and comprehensive analysis."""

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
        self.commit_analyzer = CommitAnalyzer(config)
        self.branch_detector = BranchMergeDetector(config)

        # Configuration flags
        self.enable_incremental = config.source_config.get("enable_incremental", True)
        self.enable_semantic_analysis = config.source_config.get(
            "enable_semantic_analysis", True
        )
        self.enable_branch_detection = config.source_config.get(
            "enable_branch_detection", True
        )
        self.checkpoint_interval = config.source_config.get("checkpoint_interval", 100)

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

        # Initialize branch topology if enabled
        if self.enable_branch_detection:
            self.branch_topology = await self.branch_detector.map_branch_topology()
            self.logger.info(
                "Branch topology mapped", branches=len(self.branch_topology)
            )

        self.logger.info("Enhanced git adapter initialized", repo_path=self._repo_path)

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch git data items with incremental processing."""
        config = self.config.source_config

        if self.enable_incremental:
            # Use incremental processing
            async for item in self._fetch_items_incremental(since, until, limit):
                yield item
        else:
            # Use standard processing
            async for item in self._fetch_items_standard(since, until, limit):
                yield item

    async def _fetch_items_incremental(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch items with incremental processing."""
        branches = await self._get_branches_to_process()

        for branch in branches:
            self.logger.info("Processing branch", branch=branch)

            # Get last checkpoint
            last_commit = await self.checkpoint_manager.get_last_processed_commit(
                branch
            )

            # Build git log command for incremental processing
            args = ["log", "--format=fuller", "--name-status", f"{branch}"]

            if last_commit:
                # Only get commits since last processed
                args.append(f"{last_commit}..HEAD")

            if since:
                args.append(f"--since={since.isoformat()}")
            if until:
                args.append(f"--until={until.isoformat()}")

            try:
                output = await self._run_git_command(args)
                commits = self._parse_git_log_output(output)

                processed_count = 0
                for commit in commits:
                    if limit and processed_count >= limit:
                        break

                    # Add enhanced analysis
                    if self.enable_semantic_analysis:
                        commit["analysis"] = await self.commit_analyzer.analyze_commit(
                            commit
                        )

                    # Detect merges
                    if self.enable_branch_detection:
                        merge_info = await self.branch_detector.detect_merge_commits(
                            commit["hash"]
                        )
                        if merge_info:
                            commit["merge_info"] = merge_info

                    commit["type"] = "commit"
                    commit["branch"] = branch

                    yield commit
                    processed_count += 1

                    # Save checkpoint periodically
                    if processed_count % self.checkpoint_interval == 0:
                        await self.checkpoint_manager.save_checkpoint(
                            branch,
                            commit["hash"],
                            datetime.fromisoformat(
                                commit["commit_date"].replace(" ", "T")
                            ),
                            processed_count,
                        )

                # Final checkpoint
                if commits:
                    await self.checkpoint_manager.save_checkpoint(
                        branch,
                        commits[0]["hash"],
                        datetime.fromisoformat(
                            commits[0]["commit_date"].replace(" ", "T")
                        ),
                        processed_count,
                    )

            except Exception as e:
                self.logger.error(
                    "Failed to process branch", branch=branch, error=str(e)
                )

    async def _fetch_items_standard(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Standard fetch implementation (same as original GitAdapter)."""
        config = self.config.source_config
        count = 0

        # Fetch commits if enabled
        if config.get("include_commits", True):
            async for commit in self._fetch_commits_standard(since, until, limit):
                if limit and count >= limit:
                    return
                yield commit
                count += 1

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
        """Transform raw git item into enhanced ContextItem."""
        item_type = raw_item["type"]

        if item_type == "commit":
            return await self._transform_enhanced_commit(raw_item)
        elif item_type == "branch":
            return await self._transform_branch(raw_item)
        elif item_type == "tag":
            return await self._transform_tag(raw_item)
        else:
            raise ValueError(f"Unknown git item type: {item_type}")

    async def _transform_enhanced_commit(
        self, raw_commit: Dict[str, Any]
    ) -> ContextItem:
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
                item.timestamp = datetime.fromisoformat(
                    commit_date_str.replace(" ", "T")
                ).replace(tzinfo=timezone.utc)
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

        # Add analysis results
        analysis = raw_commit.get("analysis")
        if analysis:
            git_metadata.update(
                {
                    "commit_type": analysis.commit_type.value,
                    "impact_score": analysis.impact_score,
                    "risk_score": analysis.risk_score,
                    "complexity_delta": analysis.complexity_delta,
                    "semantic_tags": analysis.semantic_tags,
                    "related_patterns": analysis.related_patterns,
                    "author_patterns": analysis.author_patterns,
                }
            )

        # Add merge information
        merge_info = raw_commit.get("merge_info")
        if merge_info:
            git_metadata.update(
                {
                    "is_merge_commit": True,
                    "source_branch": merge_info.source_branch,
                    "target_branch": merge_info.target_branch,
                    "merge_strategy": merge_info.merge_strategy,
                    "conflicts_resolved": merge_info.conflicts_resolved,
                }
            )

        item.metrics = git_metadata

        # Enhanced tags
        tags = ["git", "commit"]

        if analysis:
            tags.append(f"type_{analysis.commit_type.value}")
            tags.extend(analysis.semantic_tags)

            if analysis.impact_score > 0.7:
                tags.append("high_impact")
            if analysis.risk_score > 0.7:
                tags.append("high_risk")

        # Branch-specific tags
        if raw_commit.get("branch"):
            tags.append(f"branch_{raw_commit['branch']}")

        item.tags = tags

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
            lines.append(f"Type: {analysis.commit_type.value}")
            lines.append(f"Impact Score: {analysis.impact_score:.2f}")
            lines.append(f"Risk Score: {analysis.risk_score:.2f}")
            if analysis.semantic_tags:
                lines.append(f"Tags: {', '.join(analysis.semantic_tags)}")

        # Merge information
        merge_info = commit.get("merge_info")
        if merge_info:
            lines.append("")
            lines.append("## Merge Information")
            lines.append(f"Source Branch: {merge_info.source_branch}")
            lines.append(f"Target Branch: {merge_info.target_branch}")
            lines.append(f"Strategy: {merge_info.merge_strategy}")

        # Changed files
        changed_files = commit.get("changed_files", [])
        if changed_files:
            lines.append("")
            lines.append("## Changed Files")
            for file_change in changed_files[:20]:
                lines.append(f"  {file_change['type']}\t{file_change['file']}")

            if len(changed_files) > 20:
                lines.append(f"  ... and {len(changed_files) - 20} more files")

        return "\n".join(lines)

    # Existing methods from original GitAdapter (with enhancements)
    async def _get_branches_to_process(self) -> List[str]:
        """Get list of branches to process."""
        try:
            output = await self._run_git_command(
                ["branch", "-r", "--format=%(refname:short)"]
            )
            branches = [
                b.strip().replace("origin/", "")
                for b in output.split("\n")
                if b.strip()
            ]

            # Filter branches based on configuration
            branch_filters = self.config.source_config.get("branch_filters", [])
            if branch_filters:
                branches = [b for b in branches if b in branch_filters]

            return branches
        except Exception as e:
            self.logger.error("Failed to get branches", error=str(e))
            return ["main"]  # Fallback to main branch

    # Include all other methods from original GitAdapter...
    # (Methods like _run_git_command, _parse_git_log_output, etc.)

    async def cleanup(self) -> None:
        """Clean up enhanced git adapter resources."""
        self.logger.info("Cleaning up enhanced git adapter")
        self._processed_commits.clear()

        # Additional cleanup for enhanced components
        if hasattr(self, "branch_topology"):
            del self.branch_topology
