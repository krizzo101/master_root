"""CI/CD Pipeline Integration Adapter - Unified interface for multiple CI/CD platforms."""

import asyncio
import hashlib
import hmac
from abc import abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ...models.common import ContextItem, ContextRelationship
from ..base_adapter import AdapterConfig, BaseAdapter

logger = structlog.get_logger(__name__)


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLECI = "circleci"


class CICDEventType(Enum):
    """CI/CD event types."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    BUILD_STARTED = "build_started"
    BUILD_COMPLETED = "build_completed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    RELEASE_CREATED = "release_created"
    CHECK_RUN_COMPLETED = "check_run_completed"


class CICDAdapterConfig(AdapterConfig):
    """Configuration for CI/CD adapters."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Platform-specific settings
        self.platform: CICDPlatform = kwargs.get(
            "platform", CICDPlatform.GITHUB_ACTIONS
        )
        self.base_url: str = kwargs.get("base_url", "")
        self.api_token: str = kwargs.get("api_token", "")
        self.webhook_secret: str = kwargs.get("webhook_secret", "")

        # Repository/project filtering
        self.repositories: List[str] = kwargs.get("repositories", [])
        self.projects: List[str] = kwargs.get("projects", [])

        # Event filtering
        self.event_types: List[CICDEventType] = kwargs.get("event_types", [])
        self.track_branches: List[str] = kwargs.get(
            "track_branches", ["main", "master", "develop"]
        )

        # API settings
        self.api_rate_limit: int = kwargs.get(
            "api_rate_limit", 100
        )  # requests per minute
        self.concurrent_requests: int = kwargs.get("concurrent_requests", 10)
        self.request_timeout: int = kwargs.get("request_timeout", 30)

        # Historical sync settings
        self.historical_sync_enabled: bool = kwargs.get("historical_sync_enabled", True)
        self.historical_sync_days: int = kwargs.get("historical_sync_days", 90)
        self.sync_batch_size: int = kwargs.get("sync_batch_size", 100)

        # Correlation settings
        self.enable_commit_correlation: bool = kwargs.get(
            "enable_commit_correlation", True
        )
        self.enable_temporal_correlation: bool = kwargs.get(
            "enable_temporal_correlation", True
        )
        self.temporal_window_hours: int = kwargs.get("temporal_window_hours", 2)

        # Performance and analytics settings
        self.calculate_performance_metrics: bool = kwargs.get(
            "calculate_performance_metrics", True
        )
        self.track_deployment_environments: bool = kwargs.get(
            "track_deployment_environments", True
        )
        self.enable_artifact_tracking: bool = kwargs.get(
            "enable_artifact_tracking", True
        )
        self.enable_quality_gates: bool = kwargs.get("enable_quality_gates", True)

        # Environment progression tracking
        self.environment_promotion_chains: List[List[str]] = kwargs.get(
            "environment_promotion_chains",
            [["dev", "staging", "prod"], ["test", "stage", "production"]],
        )

        # Alert thresholds
        self.failure_rate_threshold: float = kwargs.get(
            "failure_rate_threshold", 0.2
        )  # 20%
        self.performance_degradation_threshold: float = kwargs.get(
            "performance_degradation_threshold", 1.5
        )  # 50% slower
        self.deployment_frequency_alert_hours: int = kwargs.get(
            "deployment_frequency_alert_hours", 168
        )  # 1 week


class BaseCICDAdapter(BaseAdapter):
    """Base class for CI/CD platform adapters."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.cicd_config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = APIRateLimiter(config.api_rate_limit)

    async def start(self) -> None:
        """Initialize the CI/CD adapter."""
        await super().start()

        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=self.cicd_config.request_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=self.cicd_config.concurrent_requests),
        )

        self.logger.info(
            "CI/CD adapter started",
            platform=self.cicd_config.platform.value,
            repositories=len(self.cicd_config.repositories),
        )

    async def stop(self) -> None:
        """Stop the CI/CD adapter."""
        if self.session:
            await self.session.close()
            self.session = None

        await super().stop()

    async def fetch_items(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch CI/CD events from the platform."""
        if self.cicd_config.historical_sync_enabled:
            # Fetch historical data first
            async for item in self.fetch_historical_data(limit):
                yield item

        # Then fetch real-time updates
        async for item in self.fetch_real_time_updates(limit):
            yield item

    @abstractmethod
    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical CI/CD data from API."""
        pass

    @abstractmethod
    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch real-time CI/CD updates."""
        pass

    @abstractmethod
    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process incoming webhook payload."""
        pass

    @abstractmethod
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        pass

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform platform-specific data to ContextItem."""
        try:
            item = await self._transform_platform_item(raw_item)

            # Add performance metrics if enabled
            if (
                hasattr(self.cicd_config, "calculate_performance_metrics")
                and self.cicd_config.calculate_performance_metrics
            ):
                # This would typically be called with a context window from the ingestion pipeline
                # For now, we just ensure the item has the structure for metrics
                if not item.metrics:
                    item.metrics = {}

                # Add artifact management metadata
                item.metrics.update(self._extract_artifact_metadata(raw_item))

            return item
        except Exception as e:
            self.logger.error(
                "Failed to transform CI/CD item",
                platform=self.cicd_config.platform.value,
                error=str(e),
                raw_item_keys=list(raw_item.keys()) if raw_item else None,
            )
            raise

    def _extract_artifact_metadata(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract artifact and build metadata."""
        metadata = {}
        data = raw_item.get("data", {})

        # Extract artifact URLs and information
        if "artifacts" in data:
            artifacts = data["artifacts"]
            if isinstance(artifacts, list):
                metadata["artifact_count"] = len(artifacts)
                metadata["artifact_urls"] = [
                    a.get("url") for a in artifacts if a.get("url")
                ]
                metadata["artifact_sizes"] = [
                    a.get("size") for a in artifacts if a.get("size")
                ]

        # Extract test results
        if "test_results" in data:
            test_data = data["test_results"]
            metadata["tests_total"] = test_data.get("total", 0)
            metadata["tests_passed"] = test_data.get("passed", 0)
            metadata["tests_failed"] = test_data.get("failed", 0)
            metadata["test_coverage"] = test_data.get("coverage")

        # Extract quality metrics
        if "quality_gate" in data:
            quality = data["quality_gate"]
            metadata["quality_gate_status"] = quality.get("status")
            metadata["code_coverage"] = quality.get("coverage")
            metadata["code_smells"] = quality.get("code_smells")
            metadata["vulnerabilities"] = quality.get("vulnerabilities")

        # Extract deployment information
        if "environment" in data or raw_item.get("type") == "deployment":
            metadata["deployment_strategy"] = data.get("deployment_strategy")
            metadata["rollback_enabled"] = data.get("rollback_enabled", False)
            metadata["blue_green"] = data.get("blue_green", False)
            metadata["canary_percentage"] = data.get("canary_percentage")

        return metadata

    @abstractmethod
    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Platform-specific item transformation."""
        pass

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Detect relationships between CI/CD items and other context."""
        relationships = []

        if self.cicd_config.enable_commit_correlation:
            relationships.extend(
                await self._detect_commit_relationships(item, context_window)
            )

        if self.cicd_config.enable_temporal_correlation:
            relationships.extend(
                await self._detect_temporal_relationships(item, context_window)
            )

        return relationships

    async def _detect_commit_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Detect relationships based on commit SHA correlation."""
        relationships = []

        # Extract commit SHA from CI/CD item
        commit_sha = None
        if item.source_data:
            commit_sha = (
                item.source_data.get("head_commit", {}).get("id")
                or item.source_data.get("sha")
                or item.source_data.get("commit", {}).get("sha")
                or item.metrics.get("commit_sha")
            )

        if not commit_sha:
            return relationships

        # Find matching git commits in context window
        for context_item in context_window:
            if (
                context_item.source_type == "git"
                and context_item.entity_type == "commit"
                and context_item.source_data
                and context_item.source_data.get("sha") == commit_sha
            ):
                relationships.append(
                    (
                        "builds_commit",
                        str(context_item.id),
                        1.0,  # High confidence for exact commit match
                    )
                )

        return relationships

    async def _detect_temporal_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Detect relationships based on temporal proximity."""
        relationships = []

        window_delta = timedelta(hours=self.cicd_config.temporal_window_hours)

        for context_item in context_window:
            time_diff = abs((item.timestamp - context_item.timestamp).total_seconds())

            # Calculate confidence based on temporal proximity
            if time_diff <= window_delta.total_seconds():
                confidence = max(0.1, 1.0 - (time_diff / window_delta.total_seconds()))

                # Different relationship types based on context
                if context_item.source_type == "chat":
                    if any(
                        keyword in (context_item.content or "").lower()
                        for keyword in ["deploy", "build", "ci", "release"]
                    ):
                        relationships.append(
                            (
                                "discussed_during_cicd",
                                str(context_item.id),
                                confidence
                                * 0.8,  # Lower confidence for temporal correlation
                            )
                        )
                elif context_item.source_type == "error":
                    # Correlate errors with failed builds/deployments
                    if item.metrics.get("status") in ["failed", "error"]:
                        relationships.append(
                            (
                                "error_during_cicd",
                                str(context_item.id),
                                confidence * 0.6,
                            )
                        )
                elif context_item.source_type == "cicd":
                    # Correlate CI/CD items with each other
                    relationships.extend(
                        await self._detect_cicd_chain_relationships(
                            item, context_item, confidence
                        )
                    )

        return relationships

    async def _detect_cicd_chain_relationships(
        self,
        current_item: ContextItem,
        context_item: ContextItem,
        base_confidence: float,
    ) -> List[Tuple[str, str, float]]:
        """Detect relationships within CI/CD chains (build -> deploy -> etc.)."""
        relationships = []

        current_type = current_item.entity_type
        context_type = context_item.entity_type

        # Build -> Job relationships
        if "build" in current_type and "job" in context_type:
            if current_item.metrics.get("build_number") == context_item.metrics.get(
                "build_number"
            ):
                relationships.append(
                    ("contains_job", str(context_item.id), base_confidence * 0.9)
                )

        # Pipeline -> Job relationships
        elif "pipeline" in current_type and "job" in context_type:
            if current_item.metrics.get("pipeline_id") == context_item.metrics.get(
                "pipeline_id"
            ):
                relationships.append(
                    ("contains_job", str(context_item.id), base_confidence * 0.9)
                )

        # Build -> Deployment relationships
        elif (
            any(t in current_type for t in ["build", "pipeline"])
            and "deployment" in context_type
        ):
            # Same commit SHA indicates deployment of this build
            current_sha = current_item.metrics.get(
                "commit_sha"
            ) or current_item.metrics.get("sha")
            context_sha = context_item.metrics.get(
                "commit_sha"
            ) or context_item.metrics.get("sha")

            if current_sha and context_sha and current_sha == context_sha:
                relationships.append(
                    ("triggers_deployment", str(context_item.id), base_confidence * 0.8)
                )

        # Environment progression (dev -> staging -> prod)
        elif "deployment" in current_type and "deployment" in context_type:
            current_env = current_item.metrics.get("environment", "").lower()
            context_env = context_item.metrics.get("environment", "").lower()

            # Define environment progression
            env_order = [
                "dev",
                "development",
                "test",
                "testing",
                "staging",
                "stage",
                "prod",
                "production",
            ]

            try:
                current_idx = next(
                    i for i, env in enumerate(env_order) if env in current_env
                )
                context_idx = next(
                    i for i, env in enumerate(env_order) if env in context_env
                )

                if context_idx == current_idx + 1:  # Next environment in sequence
                    relationships.append(
                        (
                            "promotes_to_environment",
                            str(context_item.id),
                            base_confidence * 0.7,
                        )
                    )
            except StopIteration:
                pass  # Environment names don't match known patterns

        return relationships

    async def _calculate_performance_metrics(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for CI/CD items."""
        metrics = {}

        # Calculate success rate for similar jobs/builds
        similar_items = [
            ctx
            for ctx in context_window
            if (
                ctx.source_type == "cicd"
                and ctx.entity_type == item.entity_type
                and ctx.project_id == item.project_id
            )
        ]

        if similar_items:
            successful = sum(
                1
                for ctx in similar_items
                if ctx.metrics.get("status") in ["success", "succeeded", "completed"]
            )
            total = len(similar_items)
            metrics["success_rate"] = successful / total if total > 0 else 0

            # Calculate average duration
            durations = [
                ctx.metrics.get("duration_ms", 0)
                for ctx in similar_items
                if ctx.metrics.get("duration_ms")
            ]
            if durations:
                metrics["avg_duration_ms"] = sum(durations) / len(durations)
                metrics["duration_percentile_90"] = sorted(durations)[
                    int(len(durations) * 0.9)
                ]

                # Performance comparison
                current_duration = item.metrics.get("duration_ms")
                if current_duration:
                    metrics["performance_vs_avg"] = (
                        "faster"
                        if current_duration < metrics["avg_duration_ms"]
                        else "slower"
                    )
                    metrics["performance_ratio"] = (
                        current_duration / metrics["avg_duration_ms"]
                    )

        # Calculate deployment frequency
        if "deployment" in item.entity_type:
            recent_deployments = [
                ctx
                for ctx in context_window
                if (
                    ctx.source_type == "cicd"
                    and "deployment" in ctx.entity_type
                    and ctx.project_id == item.project_id
                    and ctx.metrics.get("environment")
                    == item.metrics.get("environment")
                )
            ]

            if len(recent_deployments) > 1:
                time_diffs = []
                sorted_deployments = sorted(
                    recent_deployments, key=lambda x: x.timestamp
                )

                for i in range(1, len(sorted_deployments)):
                    diff = (
                        sorted_deployments[i].timestamp
                        - sorted_deployments[i - 1].timestamp
                    ).total_seconds()
                    time_diffs.append(diff)

                if time_diffs:
                    metrics["deployment_frequency_hours"] = (
                        sum(time_diffs) / len(time_diffs) / 3600
                    )

        return metrics


class APIRateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, requests_per_minute: int):
        self.rate_limit = requests_per_minute
        self.request_times = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire rate limit permission."""
        async with self._lock:
            now = datetime.utcnow().timestamp()

            # Remove requests older than 1 minute
            cutoff = now - 60
            self.request_times = [t for t in self.request_times if t > cutoff]

            # Check if we need to wait
            if len(self.request_times) >= self.rate_limit:
                sleep_time = self.request_times[0] + 60 - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            self.request_times.append(now)


class GitHubActionsAdapter(BaseCICDAdapter):
    """GitHub Actions integration adapter."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.api_base = "https://api.github.com"

    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical workflow runs from GitHub API."""
        if not self.cicd_config.repositories:
            return

        since = datetime.utcnow() - timedelta(
            days=self.cicd_config.historical_sync_days
        )

        for repo in self.cicd_config.repositories:
            try:
                await self.rate_limiter.acquire()

                url = f"{self.api_base}/repos/{repo}/actions/runs"
                params = {
                    "created": f">={since.isoformat()}",
                    "per_page": self.cicd_config.sync_batch_size,
                }

                async with self.session.get(
                    url, headers=self._get_auth_headers(), params=params
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                for run in data.get("workflow_runs", []):
                    yield {"type": "workflow_run", "data": run, "repository": repo}

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch GitHub workflow runs for {repo}: {e}"
                )

    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """GitHub Actions real-time updates come via webhooks."""
        # This is handled by the webhook processor
        return
        if False:  # Unreachable, but keeps the generator type
            yield {}

    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process GitHub webhook payload."""
        if event_type == "workflow_run":
            return await self._process_workflow_run(payload)
        elif event_type == "workflow_job":
            return await self._process_workflow_job(payload)
        elif event_type == "deployment":
            return await self._process_deployment(payload)
        elif event_type == "deployment_status":
            return await self._process_deployment_status(payload)
        elif event_type == "check_run":
            return await self._process_check_run(payload)

        return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature."""
        if not self.cicd_config.webhook_secret:
            return True  # Skip validation if no secret configured

        expected_signature = (
            "sha256="
            + hmac.new(
                self.cicd_config.webhook_secret.encode(), payload, hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature, expected_signature)

    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform GitHub Actions data to ContextItem."""
        item_type = raw_item.get("type")
        data = raw_item.get("data", {})

        if item_type == "workflow_run":
            return self._transform_workflow_run(data, raw_item.get("repository"))
        elif item_type == "workflow_job":
            return self._transform_workflow_job(data, raw_item.get("repository"))
        elif item_type == "deployment":
            return self._transform_deployment(data, raw_item.get("repository"))

        raise ValueError(f"Unsupported GitHub Actions item type: {item_type}")

    def _transform_workflow_run(self, run_data: dict, repository: str) -> ContextItem:
        """Transform GitHub workflow run to ContextItem."""
        created_at = datetime.fromisoformat(
            run_data["created_at"].replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            run_data["updated_at"].replace("Z", "+00:00")
        )

        # Calculate duration if completed
        duration_ms = None
        if run_data.get("conclusion"):
            duration_ms = int((updated_at - created_at).total_seconds() * 1000)

        return ContextItem(
            source_type="cicd",
            source_id=str(run_data["id"]),
            entity_type="github_workflow_run",
            title=f"Workflow: {run_data['name']}",
            content=self._extract_workflow_summary(run_data),
            timestamp=created_at,
            timestamp_end=updated_at if run_data.get("conclusion") else None,
            project_id=repository,
            file_path=run_data.get("path"),
            actor_id=run_data.get("actor", {}).get("login"),
            actor_type="human",
            metrics={
                "status": run_data["status"],
                "conclusion": run_data.get("conclusion"),
                "run_number": run_data["run_number"],
                "run_attempt": run_data["run_attempt"],
                "duration_ms": duration_ms,
                "workflow_id": run_data["workflow_id"],
                "head_branch": run_data.get("head_branch"),
                "commit_sha": run_data.get("head_sha"),
                "event": run_data.get("event"),
            },
            source_data=run_data,
        )

    def _transform_workflow_job(self, job_data: dict, repository: str) -> ContextItem:
        """Transform GitHub workflow job to ContextItem."""
        created_at = datetime.fromisoformat(
            job_data["created_at"].replace("Z", "+00:00")
        )

        completed_at = None
        if job_data.get("completed_at"):
            completed_at = datetime.fromisoformat(
                job_data["completed_at"].replace("Z", "+00:00")
            )

        duration_ms = None
        if completed_at:
            duration_ms = int((completed_at - created_at).total_seconds() * 1000)

        return ContextItem(
            source_type="cicd",
            source_id=str(job_data["id"]),
            entity_type="github_workflow_job",
            title=f"Job: {job_data['name']}",
            content=self._extract_job_summary(job_data),
            timestamp=created_at,
            timestamp_end=completed_at,
            project_id=repository,
            actor_id=job_data.get("runner_name"),
            actor_type="system",
            metrics={
                "status": job_data["status"],
                "conclusion": job_data.get("conclusion"),
                "duration_ms": duration_ms,
                "run_id": job_data["run_id"],
                "run_attempt": job_data["run_attempt"],
                "runner_name": job_data.get("runner_name"),
                "runner_group_name": job_data.get("runner_group_name"),
            },
            source_data=job_data,
        )

    def _transform_deployment(self, deploy_data: dict, repository: str) -> ContextItem:
        """Transform GitHub deployment to ContextItem."""
        created_at = datetime.fromisoformat(
            deploy_data["created_at"].replace("Z", "+00:00")
        )

        return ContextItem(
            source_type="cicd",
            source_id=str(deploy_data["id"]),
            entity_type="github_deployment",
            title=f"Deployment to {deploy_data.get('environment', 'unknown')}",
            content=f"Deployment {deploy_data['id']} to {deploy_data.get('environment')}",
            timestamp=created_at,
            project_id=repository,
            actor_id=deploy_data.get("creator", {}).get("login"),
            actor_type="human",
            metrics={
                "environment": deploy_data.get("environment"),
                "ref": deploy_data.get("ref"),
                "sha": deploy_data.get("sha"),
                "task": deploy_data.get("task"),
                "auto_merge": deploy_data.get("auto_merge"),
                "required_contexts": deploy_data.get("required_contexts", []),
                "production_environment": deploy_data.get("production_environment"),
            },
            source_data=deploy_data,
        )

    def _extract_workflow_summary(self, run_data: dict) -> str:
        """Extract workflow summary text."""
        summary_parts = [
            f"Workflow '{run_data['name']}' on {run_data.get('head_branch', 'unknown branch')}",
            f"Status: {run_data['status']}",
        ]

        if run_data.get("conclusion"):
            summary_parts.append(f"Conclusion: {run_data['conclusion']}")

        if run_data.get("head_commit", {}).get("message"):
            summary_parts.append(
                f"Commit: {run_data['head_commit']['message'][:100]}..."
            )

        return " | ".join(summary_parts)

    def _extract_job_summary(self, job_data: dict) -> str:
        """Extract job summary text."""
        summary_parts = [
            f"Job '{job_data['name']}' in workflow run {job_data['run_id']}",
            f"Status: {job_data['status']}",
        ]

        if job_data.get("conclusion"):
            summary_parts.append(f"Conclusion: {job_data['conclusion']}")

        if job_data.get("runner_name"):
            summary_parts.append(f"Runner: {job_data['runner_name']}")

        return " | ".join(summary_parts)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GitHub API."""
        return {
            "Authorization": f"token {self.cicd_config.api_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "unified-context-system/1.0",
        }

    async def _process_workflow_run(self, payload: dict) -> Optional[ContextItem]:
        """Process workflow_run webhook."""
        return self._transform_workflow_run(
            payload["workflow_run"], payload["repository"]["full_name"]
        )

    async def _process_workflow_job(self, payload: dict) -> Optional[ContextItem]:
        """Process workflow_job webhook."""
        return self._transform_workflow_job(
            payload["workflow_job"], payload["repository"]["full_name"]
        )

    async def _process_deployment(self, payload: dict) -> Optional[ContextItem]:
        """Process deployment webhook."""
        return self._transform_deployment(
            payload["deployment"], payload["repository"]["full_name"]
        )

    async def _process_deployment_status(self, payload: dict) -> Optional[ContextItem]:
        """Process deployment_status webhook."""
        # This could create a separate context item for deployment status updates
        # or update the existing deployment item
        return None

    async def _process_check_run(self, payload: dict) -> Optional[ContextItem]:
        """Process check_run webhook."""
        check_run = payload["check_run"]

        # Only process completed check runs
        if check_run["status"] != "completed":
            return None

        created_at = datetime.fromisoformat(
            check_run["started_at"].replace("Z", "+00:00")
        )
        completed_at = datetime.fromisoformat(
            check_run["completed_at"].replace("Z", "+00:00")
        )

        return ContextItem(
            source_type="cicd",
            source_id=str(check_run["id"]),
            entity_type="github_check_run",
            title=f"Check: {check_run['name']}",
            content=f"Check run '{check_run['name']}' - {check_run['conclusion']}",
            timestamp=created_at,
            timestamp_end=completed_at,
            project_id=payload["repository"]["full_name"],
            metrics={
                "status": check_run["status"],
                "conclusion": check_run["conclusion"],
                "duration_ms": int((completed_at - created_at).total_seconds() * 1000),
                "head_sha": check_run["head_sha"],
                "check_suite_id": check_run["check_suite"]["id"],
            },
            source_data=check_run,
        )


class GitLabCIAdapter(BaseCICDAdapter):
    """GitLab CI/CD integration adapter."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.api_base = config.base_url or "https://gitlab.com/api/v4"

    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical pipeline data from GitLab API."""
        if not self.cicd_config.projects:
            return

        since = datetime.utcnow() - timedelta(
            days=self.cicd_config.historical_sync_days
        )

        for project_id in self.cicd_config.projects:
            try:
                await self.rate_limiter.acquire()

                # Fetch pipelines
                url = f"{self.api_base}/projects/{project_id}/pipelines"
                params = {
                    "updated_after": since.isoformat(),
                    "per_page": self.cicd_config.sync_batch_size,
                    "sort": "desc",
                }

                async with self.session.get(
                    url, headers=self._get_auth_headers(), params=params
                ) as response:
                    response.raise_for_status()
                    pipelines = await response.json()

                for pipeline in pipelines:
                    yield {
                        "type": "pipeline",
                        "data": pipeline,
                        "project_id": project_id,
                    }

                    # Fetch jobs for each pipeline
                    await self.rate_limiter.acquire()
                    jobs_url = f"{self.api_base}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"

                    async with self.session.get(
                        jobs_url, headers=self._get_auth_headers()
                    ) as jobs_response:
                        jobs_response.raise_for_status()
                        jobs = await jobs_response.json()

                    for job in jobs:
                        yield {
                            "type": "job",
                            "data": job,
                            "project_id": project_id,
                            "pipeline_id": pipeline["id"],
                        }

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch GitLab data for project {project_id}: {e}"
                )

    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """GitLab real-time updates come via webhooks."""
        return
        if False:
            yield {}

    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process GitLab webhook payload."""
        if event_type == "Pipeline Hook":
            return await self._process_pipeline_event(payload)
        elif event_type == "Job Hook":
            return await self._process_job_event(payload)
        elif event_type == "Deployment Hook":
            return await self._process_deployment_event(payload)

        return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Validate GitLab webhook token."""
        if not self.cicd_config.webhook_secret:
            return True
        return signature == self.cicd_config.webhook_secret

    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform GitLab data to ContextItem."""
        item_type = raw_item.get("type")
        data = raw_item.get("data", {})

        if item_type == "pipeline":
            return self._transform_pipeline(data, raw_item.get("project_id"))
        elif item_type == "job":
            return self._transform_job(
                data, raw_item.get("project_id"), raw_item.get("pipeline_id")
            )
        elif item_type == "deployment":
            return self._transform_deployment_event(data, raw_item.get("project_id"))

        raise ValueError(f"Unsupported GitLab item type: {item_type}")

    def _transform_pipeline(self, pipeline_data: dict, project_id: str) -> ContextItem:
        """Transform GitLab pipeline to ContextItem."""
        created_at = datetime.fromisoformat(
            pipeline_data["created_at"].replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            pipeline_data["updated_at"].replace("Z", "+00:00")
        )

        duration_ms = None
        if pipeline_data.get("duration"):
            duration_ms = int(pipeline_data["duration"] * 1000)

        return ContextItem(
            source_type="cicd",
            source_id=str(pipeline_data["id"]),
            entity_type="gitlab_pipeline",
            title=f"Pipeline #{pipeline_data['id']} on {pipeline_data.get('ref', 'unknown')}",
            content=self._extract_pipeline_summary(pipeline_data),
            timestamp=created_at,
            timestamp_end=updated_at
            if pipeline_data.get("status") in ["success", "failed", "canceled"]
            else None,
            project_id=project_id,
            actor_id=pipeline_data.get("user", {}).get("username"),
            actor_type="human",
            metrics={
                "status": pipeline_data["status"],
                "ref": pipeline_data.get("ref"),
                "sha": pipeline_data.get("sha"),
                "duration_ms": duration_ms,
                "pipeline_id": pipeline_data["id"],
                "web_url": pipeline_data.get("web_url"),
                "source": pipeline_data.get("source"),
            },
            source_data=pipeline_data,
        )

    def _transform_job(
        self, job_data: dict, project_id: str, pipeline_id: int
    ) -> ContextItem:
        """Transform GitLab job to ContextItem."""
        created_at = datetime.fromisoformat(
            job_data["created_at"].replace("Z", "+00:00")
        )

        finished_at = None
        if job_data.get("finished_at"):
            finished_at = datetime.fromisoformat(
                job_data["finished_at"].replace("Z", "+00:00")
            )

        duration_ms = None
        if job_data.get("duration"):
            duration_ms = int(job_data["duration"] * 1000)

        return ContextItem(
            source_type="cicd",
            source_id=str(job_data["id"]),
            entity_type="gitlab_job",
            title=f"Job: {job_data['name']}",
            content=f"GitLab job '{job_data['name']}' in pipeline {pipeline_id} - {job_data['status']}",
            timestamp=created_at,
            timestamp_end=finished_at,
            project_id=project_id,
            actor_id=job_data.get("user", {}).get("username"),
            actor_type="human",
            metrics={
                "status": job_data["status"],
                "stage": job_data.get("stage"),
                "duration_ms": duration_ms,
                "pipeline_id": pipeline_id,
                "job_id": job_data["id"],
                "web_url": job_data.get("web_url"),
                "runner": job_data.get("runner", {}),
                "commit_sha": job_data.get("commit", {}).get("id"),
            },
            source_data=job_data,
        )

    def _extract_pipeline_summary(self, pipeline_data: dict) -> str:
        """Extract pipeline summary text."""
        summary_parts = [
            f"Pipeline #{pipeline_data['id']} on {pipeline_data.get('ref', 'unknown')}",
            f"Status: {pipeline_data['status']}",
        ]

        if pipeline_data.get("duration"):
            summary_parts.append(f"Duration: {pipeline_data['duration']}s")

        if pipeline_data.get("user", {}).get("name"):
            summary_parts.append(f"User: {pipeline_data['user']['name']}")

        return " | ".join(summary_parts)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for GitLab API."""
        return {
            "Authorization": f"Bearer {self.cicd_config.api_token}",
            "Content-Type": "application/json",
        }

    async def _process_pipeline_event(self, payload: dict) -> Optional[ContextItem]:
        """Process GitLab pipeline webhook."""
        pipeline_attrs = payload.get("object_attributes", {})
        project = payload.get("project", {})

        return self._transform_pipeline(pipeline_attrs, str(project.get("id")))

    async def _process_job_event(self, payload: dict) -> Optional[ContextItem]:
        """Process GitLab job webhook."""
        job_attrs = payload.get("object_attributes", {})
        project = payload.get("project", {})
        pipeline_id = job_attrs.get("pipeline_id")

        return self._transform_job(job_attrs, str(project.get("id")), pipeline_id)

    async def _process_deployment_event(self, payload: dict) -> Optional[ContextItem]:
        """Process GitLab deployment webhook."""
        deployment = payload.get("deployment", {})
        project = payload.get("project", {})

        created_at = datetime.fromisoformat(
            deployment["created_at"].replace("Z", "+00:00")
        )

        return ContextItem(
            source_type="cicd",
            source_id=str(deployment["id"]),
            entity_type="gitlab_deployment",
            title=f"Deployment to {deployment.get('environment', 'unknown')}",
            content=f"GitLab deployment {deployment['id']} to {deployment.get('environment')}",
            timestamp=created_at,
            project_id=str(project.get("id")),
            metrics={
                "environment": deployment.get("environment"),
                "status": deployment.get("status"),
                "ref": deployment.get("ref"),
                "sha": deployment.get("sha"),
                "deployment_id": deployment["id"],
            },
            source_data=deployment,
        )


class JenkinsAdapter(BaseCICDAdapter):
    """Jenkins CI/CD integration adapter."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.api_base = config.base_url or "http://localhost:8080"

    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical build data from Jenkins API."""
        if not self.cicd_config.projects:  # In Jenkins context, these are job names
            return

        for job_name in self.cicd_config.projects:
            try:
                await self.rate_limiter.acquire()

                # Get job builds
                url = f"{self.api_base}/job/{job_name}/api/json"
                params = {
                    "tree": "builds[number,timestamp,result,duration,url,changeSets[*]]"
                }

                async with self.session.get(
                    url, headers=self._get_auth_headers(), params=params
                ) as response:
                    response.raise_for_status()
                    job_data = await response.json()

                # Get recent builds within sync period
                since_timestamp = (
                    datetime.utcnow()
                    - timedelta(days=self.cicd_config.historical_sync_days)
                ).timestamp() * 1000

                for build in job_data.get("builds", []):
                    if build.get("timestamp", 0) >= since_timestamp:
                        yield {"type": "build", "data": build, "job_name": job_name}

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch Jenkins data for job {job_name}: {e}"
                )

    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Jenkins real-time updates come via webhooks."""
        return
        if False:
            yield {}

    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process Jenkins webhook payload."""
        if event_type in ["build_started", "build_completed"]:
            return await self._process_build_event(payload)
        elif event_type == "deployment_completed":
            return await self._process_deployment_event(payload)

        return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Jenkins typically doesn't use webhook signatures."""
        return True  # Jenkins usually relies on network security

    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform Jenkins data to ContextItem."""
        item_type = raw_item.get("type")
        data = raw_item.get("data", {})

        if item_type == "build":
            return self._transform_build(data, raw_item.get("job_name"))
        elif item_type == "deployment":
            return self._transform_deployment_event(data, raw_item.get("job_name"))

        raise ValueError(f"Unsupported Jenkins item type: {item_type}")

    def _transform_build(self, build_data: dict, job_name: str) -> ContextItem:
        """Transform Jenkins build to ContextItem."""
        timestamp = datetime.fromtimestamp(build_data["timestamp"] / 1000)

        timestamp_end = None
        duration_ms = build_data.get("duration")
        if duration_ms and duration_ms > 0:
            timestamp_end = timestamp + timedelta(milliseconds=duration_ms)

        # Extract commit information
        commit_sha = None
        changeset = build_data.get("changeSets", [])
        if changeset and len(changeset) > 0:
            items = changeset[0].get("items", [])
            if items and len(items) > 0:
                commit_sha = items[0].get("commitId")

        return ContextItem(
            source_type="cicd",
            source_id=f"{job_name}#{build_data['number']}",
            entity_type="jenkins_build",
            title=f"Build {job_name} #{build_data['number']}",
            content=f"Jenkins build {job_name} #{build_data['number']} - {build_data.get('result', 'RUNNING')}",
            timestamp=timestamp,
            timestamp_end=timestamp_end,
            project_id=job_name,
            actor_type="system",
            metrics={
                "status": build_data.get("result", "RUNNING"),
                "build_number": build_data["number"],
                "duration_ms": duration_ms,
                "job_name": job_name,
                "build_url": build_data.get("url"),
                "commit_sha": commit_sha,
            },
            source_data=build_data,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Jenkins API."""
        if self.cicd_config.api_token:
            # Jenkins uses basic auth with API token
            import base64

            # Assume format is username:token
            auth_string = base64.b64encode(self.cicd_config.api_token.encode()).decode()
            return {"Authorization": f"Basic {auth_string}"}
        return {}

    async def _process_build_event(self, payload: dict) -> Optional[ContextItem]:
        """Process Jenkins build webhook."""
        # Extract build info from webhook payload
        build_data = {
            "number": payload.get("build_number", payload.get("number", 0)),
            "timestamp": payload.get("timestamp", datetime.utcnow().timestamp() * 1000),
            "result": payload.get("build_status", payload.get("result", "UNKNOWN")),
            "duration": payload.get("duration", 0),
            "url": payload.get("build_url", payload.get("url")),
        }

        job_name = payload.get("job_name", payload.get("name", "unknown"))
        return self._transform_build(build_data, job_name)

    async def _process_deployment_event(self, payload: dict) -> Optional[ContextItem]:
        """Process Jenkins deployment webhook."""
        timestamp = datetime.utcnow()

        return ContextItem(
            source_type="cicd",
            source_id=f"deploy-{payload.get('deployment_id', payload.get('build_number', 'unknown'))}",
            entity_type="jenkins_deployment",
            title=f"Deployment to {payload.get('environment', 'unknown')}",
            content=f"Jenkins deployment to {payload.get('environment', 'unknown')}",
            timestamp=timestamp,
            project_id=payload.get("job_name", "unknown"),
            metrics={
                "environment": payload.get("environment"),
                "status": payload.get("status"),
                "deployment_id": payload.get("deployment_id"),
                "build_number": payload.get("build_number"),
            },
            source_data=payload,
        )


class AzureDevOpsAdapter(BaseCICDAdapter):
    """Azure DevOps CI/CD integration adapter."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.api_base = config.base_url or "https://dev.azure.com"

    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical pipeline data from Azure DevOps API."""
        if not self.cicd_config.projects:
            return

        since = datetime.utcnow() - timedelta(
            days=self.cicd_config.historical_sync_days
        )

        for project in self.cicd_config.projects:
            try:
                await self.rate_limiter.acquire()

                # Format: organization/project
                org_project = project.split("/")
                if len(org_project) != 2:
                    continue

                organization, project_name = org_project

                # Fetch builds
                url = (
                    f"{self.api_base}/{organization}/{project_name}/_apis/build/builds"
                )
                params = {
                    "api-version": "7.0",
                    "minTime": since.isoformat(),
                    "$top": self.cicd_config.sync_batch_size,
                }

                async with self.session.get(
                    url, headers=self._get_auth_headers(), params=params
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                for build in data.get("value", []):
                    yield {"type": "build", "data": build, "project": project}

                # Fetch releases
                release_url = f"{self.api_base}/{organization}/{project_name}/_apis/release/deployments"
                async with self.session.get(
                    release_url,
                    headers=self._get_auth_headers(),
                    params={"api-version": "7.0"},
                ) as release_response:
                    release_response.raise_for_status()
                    release_data = await release_response.json()

                for deployment in release_data.get("value", []):
                    yield {"type": "deployment", "data": deployment, "project": project}

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch Azure DevOps data for project {project}: {e}"
                )

    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Azure DevOps real-time updates come via webhooks."""
        return
        if False:
            yield {}

    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process Azure DevOps webhook payload."""
        if event_type == "build.complete":
            return await self._process_build_complete(payload)
        elif event_type == "ms.vss-release.deployment-completed-event":
            return await self._process_deployment_complete(payload)

        return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Azure DevOps can use basic auth or service hooks."""
        return True  # Simplified for now

    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform Azure DevOps data to ContextItem."""
        item_type = raw_item.get("type")
        data = raw_item.get("data", {})

        if item_type == "build":
            return self._transform_build(data, raw_item.get("project"))
        elif item_type == "deployment":
            return self._transform_deployment(data, raw_item.get("project"))

        raise ValueError(f"Unsupported Azure DevOps item type: {item_type}")

    def _transform_build(self, build_data: dict, project: str) -> ContextItem:
        """Transform Azure DevOps build to ContextItem."""
        start_time = datetime.fromisoformat(
            build_data["startTime"].replace("Z", "+00:00")
        )

        finish_time = None
        if build_data.get("finishTime"):
            finish_time = datetime.fromisoformat(
                build_data["finishTime"].replace("Z", "+00:00")
            )

        duration_ms = None
        if finish_time:
            duration_ms = int((finish_time - start_time).total_seconds() * 1000)

        return ContextItem(
            source_type="cicd",
            source_id=str(build_data["id"]),
            entity_type="azure_build",
            title=f"Build {build_data.get('buildNumber', build_data['id'])}",
            content=f"Azure DevOps build {build_data.get('buildNumber', build_data['id'])} - {build_data['status']}",
            timestamp=start_time,
            timestamp_end=finish_time,
            project_id=project,
            actor_id=build_data.get("requestedFor", {}).get("uniqueName"),
            actor_type="human",
            metrics={
                "status": build_data["status"],
                "result": build_data.get("result"),
                "build_number": build_data.get("buildNumber"),
                "duration_ms": duration_ms,
                "definition_name": build_data.get("definition", {}).get("name"),
                "source_branch": build_data.get("sourceBranch"),
                "source_version": build_data.get("sourceVersion"),
            },
            source_data=build_data,
        )

    def _transform_deployment(self, deployment_data: dict, project: str) -> ContextItem:
        """Transform Azure DevOps deployment to ContextItem."""
        started_on = datetime.fromisoformat(
            deployment_data["startedOn"].replace("Z", "+00:00")
        )

        completed_on = None
        if deployment_data.get("completedOn"):
            completed_on = datetime.fromisoformat(
                deployment_data["completedOn"].replace("Z", "+00:00")
            )

        return ContextItem(
            source_type="cicd",
            source_id=str(deployment_data["id"]),
            entity_type="azure_deployment",
            title=f"Deployment to {deployment_data.get('releaseEnvironment', {}).get('name', 'unknown')}",
            content=f"Azure DevOps deployment {deployment_data['id']}",
            timestamp=started_on,
            timestamp_end=completed_on,
            project_id=project,
            metrics={
                "status": deployment_data["deploymentStatus"],
                "environment": deployment_data.get("releaseEnvironment", {}).get(
                    "name"
                ),
                "release_name": deployment_data.get("release", {}).get("name"),
                "deployment_id": deployment_data["id"],
            },
            source_data=deployment_data,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Azure DevOps API."""
        if self.cicd_config.api_token:
            import base64

            # Azure DevOps uses PAT with basic auth
            token = base64.b64encode(f":{self.cicd_config.api_token}".encode()).decode()
            return {"Authorization": f"Basic {token}"}
        return {}

    async def _process_build_complete(self, payload: dict) -> Optional[ContextItem]:
        """Process Azure DevOps build complete webhook."""
        resource = payload.get("resource", {})
        project_info = payload.get("resourceContainers", {}).get("project", {})
        project = f"{payload.get('resourceContainers', {}).get('account', {}).get('id', 'unknown')}/{project_info.get('id', 'unknown')}"

        return self._transform_build(resource, project)

    async def _process_deployment_complete(
        self, payload: dict
    ) -> Optional[ContextItem]:
        """Process Azure DevOps deployment complete webhook."""
        resource = payload.get("resource", {})
        project_info = payload.get("resourceContainers", {}).get("project", {})
        project = f"{payload.get('resourceContainers', {}).get('account', {}).get('id', 'unknown')}/{project_info.get('id', 'unknown')}"

        return self._transform_deployment(resource, project)


class CircleCIAdapter(BaseCICDAdapter):
    """CircleCI integration adapter."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.api_base = "https://circleci.com/api/v2"

    async def fetch_historical_data(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch historical pipeline data from CircleCI API."""
        if not self.cicd_config.projects:  # Format: github/username/project
            return

        for project_slug in self.cicd_config.projects:
            try:
                await self.rate_limiter.acquire()

                url = f"{self.api_base}/project/{project_slug}/pipeline"

                async with self.session.get(
                    url, headers=self._get_auth_headers()
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                for pipeline in data.get("items", []):
                    yield {
                        "type": "pipeline",
                        "data": pipeline,
                        "project_slug": project_slug,
                    }

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch CircleCI data for project {project_slug}: {e}"
                )

    async def fetch_real_time_updates(
        self, limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """CircleCI real-time updates come via webhooks."""
        return
        if False:
            yield {}

    async def process_webhook(
        self, event_type: str, payload: dict
    ) -> Optional[ContextItem]:
        """Process CircleCI webhook payload."""
        if event_type == "workflow-completed":
            return await self._process_workflow_completed(payload)
        elif event_type == "job-completed":
            return await self._process_job_completed(payload)

        return None

    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """CircleCI webhook signature validation."""
        if not self.cicd_config.webhook_secret:
            return True

        import hashlib
        import hmac

        expected_signature = hmac.new(
            self.cicd_config.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def _transform_platform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform CircleCI data to ContextItem."""
        item_type = raw_item.get("type")
        data = raw_item.get("data", {})

        if item_type == "pipeline":
            return self._transform_pipeline(data, raw_item.get("project_slug"))
        elif item_type == "workflow":
            return self._transform_workflow(data, raw_item.get("project_slug"))
        elif item_type == "job":
            return self._transform_job(data, raw_item.get("project_slug"))

        raise ValueError(f"Unsupported CircleCI item type: {item_type}")

    def _transform_pipeline(
        self, pipeline_data: dict, project_slug: str
    ) -> ContextItem:
        """Transform CircleCI pipeline to ContextItem."""
        created_at = datetime.fromisoformat(
            pipeline_data["created_at"].replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            pipeline_data["updated_at"].replace("Z", "+00:00")
        )

        return ContextItem(
            source_type="cicd",
            source_id=str(pipeline_data["id"]),
            entity_type="circleci_pipeline",
            title=f"Pipeline {pipeline_data['number']}",
            content=f"CircleCI pipeline {pipeline_data['number']} - {pipeline_data['state']}",
            timestamp=created_at,
            timestamp_end=updated_at
            if pipeline_data["state"] in ["success", "failed", "error", "canceled"]
            else None,
            project_id=project_slug,
            metrics={
                "status": pipeline_data["state"],
                "pipeline_number": pipeline_data["number"],
                "vcs_revision": pipeline_data.get("vcs", {}).get("revision"),
                "vcs_branch": pipeline_data.get("vcs", {}).get("branch"),
            },
            source_data=pipeline_data,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for CircleCI API."""
        return {
            "Circle-Token": self.cicd_config.api_token,
            "Accept": "application/json",
        }

    async def _process_workflow_completed(self, payload: dict) -> Optional[ContextItem]:
        """Process CircleCI workflow completed webhook."""
        workflow = payload.get("workflow", {})
        project = payload.get("project", {})

        created_at = datetime.fromisoformat(
            workflow["created_at"].replace("Z", "+00:00")
        )
        stopped_at = datetime.fromisoformat(
            workflow["stopped_at"].replace("Z", "+00:00")
        )

        return ContextItem(
            source_type="cicd",
            source_id=workflow["id"],
            entity_type="circleci_workflow",
            title=f"Workflow: {workflow['name']}",
            content=f"CircleCI workflow '{workflow['name']}' - {workflow['status']}",
            timestamp=created_at,
            timestamp_end=stopped_at,
            project_id=project.get("slug"),
            metrics={
                "status": workflow["status"],
                "workflow_name": workflow["name"],
                "pipeline_id": payload.get("pipeline", {}).get("id"),
            },
            source_data=workflow,
        )

    async def _process_job_completed(self, payload: dict) -> Optional[ContextItem]:
        """Process CircleCI job completed webhook."""
        job = payload.get("job", {})
        project = payload.get("project", {})

        started_at = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
        stopped_at = datetime.fromisoformat(job["stopped_at"].replace("Z", "+00:00"))

        return ContextItem(
            source_type="cicd",
            source_id=str(job["job_number"]),
            entity_type="circleci_job",
            title=f"Job: {job['name']}",
            content=f"CircleCI job '{job['name']}' - {job['status']}",
            timestamp=started_at,
            timestamp_end=stopped_at,
            project_id=project.get("slug"),
            metrics={
                "status": job["status"],
                "job_name": job["name"],
                "job_number": job["job_number"],
                "duration_ms": int((stopped_at - started_at).total_seconds() * 1000),
            },
            source_data=job,
        )


# Factory function for creating platform adapters
def create_cicd_adapter(
    platform: CICDPlatform, config: CICDAdapterConfig
) -> BaseCICDAdapter:
    """Factory function to create appropriate CI/CD adapter."""
    if platform == CICDPlatform.GITHUB_ACTIONS:
        return GitHubActionsAdapter(config)
    elif platform == CICDPlatform.GITLAB_CI:
        return GitLabCIAdapter(config)
    elif platform == CICDPlatform.JENKINS:
        return JenkinsAdapter(config)
    elif platform == CICDPlatform.AZURE_DEVOPS:
        return AzureDevOpsAdapter(config)
    elif platform == CICDPlatform.CIRCLECI:
        return CircleCIAdapter(config)
    else:
        raise ValueError(f"Unsupported CI/CD platform: {platform}")
