"""CI/CD Pipeline Integration Adapter - Unified interface for multiple CI/CD platforms.

Enhanced with advanced correlation, ML-based failure classification, real-time performance 
analytics, cross-platform intelligence, and comprehensive deployment tracking.
"""

import asyncio
import hashlib
import hmac
import json
import re
from abc import abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import aiohttp
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ...models.common import ContextItem, ContextRelationship
from ..base_adapter import AdapterConfig, BaseAdapter

logger = structlog.get_logger(__name__)


# Enhanced Data Structures for Advanced CI/CD Intelligence

@dataclass
class BuildConstellation:
    """Represents a constellation of related builds across platforms."""
    primary_build_id: str
    related_builds: List[Dict[str, Any]] = field(default_factory=list)
    commit_sha: Optional[str] = None
    branch_name: Optional[str] = None
    correlation_strength: float = 0.0
    lifecycle_stage: str = "unknown"
    completion_status: str = "pending"
    total_builds: int = 0
    successful_builds: int = 0
    failed_builds: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FailureClassification:
    """ML-based failure classification result."""
    primary_category: str
    confidence: float
    subcategory: Optional[str] = None
    root_cause_indicators: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    similar_failures: List[Dict[str, Any]] = field(default_factory=list)
    classification_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceProfile:
    """Performance profile for builds/deployments."""
    avg_duration_ms: float
    p90_duration_ms: float
    p95_duration_ms: float
    success_rate: float
    trend_direction: str  # "improving", "degrading", "stable"
    bottleneck_stages: List[str] = field(default_factory=list)
    resource_efficiency: float = 0.0
    performance_score: float = 0.0

@dataclass
class SecurityAnalysis:
    """Security analysis for CI/CD events."""
    risk_score: float
    vulnerability_count: int = 0
    compliance_violations: List[str] = field(default_factory=list)
    security_gates_passed: bool = True
    requires_approval: bool = False
    security_recommendations: List[str] = field(default_factory=list)
    scan_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentHealth:
    """Deployment health tracking."""
    health_score: float
    error_rate_change: float = 0.0
    performance_impact: float = 0.0
    rollback_indicators: List[str] = field(default_factory=list)
    canary_metrics: Dict[str, float] = field(default_factory=dict)
    environment_status: str = "healthy"
    monitoring_alerts: List[Dict[str, Any]] = field(default_factory=list)


class CICDPlatform(Enum):
    """Supported CI/CD platforms."""

    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_DEVOPS = "azure_devops"
    CIRCLECI = "circleci"


class CICDEventType(Enum):
    """CI/CD event types with enhanced coverage."""

    # Core Build Events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    BUILD_STARTED = "build_started"
    BUILD_COMPLETED = "build_completed"
    
    # Deployment Events
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_HEALTH_CHECK = "deployment_health_check"
    DEPLOYMENT_ROLLBACK = "deployment_rollback"
    DEPLOYMENT_PROMOTION = "deployment_promotion"
    
    # Release Events
    RELEASE_CREATED = "release_created"
    RELEASE_PUBLISHED = "release_published"
    RELEASE_DELETED = "release_deleted"
    
    # Quality Gates & Security
    CHECK_RUN_COMPLETED = "check_run_completed"
    SECURITY_SCAN_COMPLETED = "security_scan_completed"
    QUALITY_GATE_PASSED = "quality_gate_passed"
    QUALITY_GATE_FAILED = "quality_gate_failed"
    COMPLIANCE_CHECK = "compliance_check"
    
    # Advanced Events
    WORKFLOW_DISPATCH = "workflow_dispatch"
    SCHEDULE_TRIGGER = "schedule_trigger"
    MANUAL_APPROVAL = "manual_approval"
    ENVIRONMENT_PROTECTION_RULE = "environment_protection_rule"
    ARTIFACT_PUBLISHED = "artifact_published"
    
    # Monitoring & Analytics
    PERFORMANCE_ALERT = "performance_alert"
    FAILURE_PATTERN_DETECTED = "failure_pattern_detected"
    BUILD_CONSTELLATION_UPDATE = "build_constellation_update"


class FailureCategory(Enum):
    """ML-based failure classification categories."""
    
    CODE_QUALITY = "code_quality"          # Lint, type errors, code smells
    TEST_FAILURES = "test_failures"        # Unit, integration, e2e test failures
    DEPENDENCY_ISSUES = "dependency_issues" # Library conflicts, version mismatches
    INFRASTRUCTURE = "infrastructure"       # Resource, network, timeout issues
    SECURITY_VIOLATIONS = "security_violations" # Security policy failures
    CONFIGURATION = "configuration"        # Config, environment issues
    PERFORMANCE = "performance"            # Memory, CPU, timeout issues
    EXTERNAL_SERVICES = "external_services" # Third-party API issues
    DEPLOYMENT_ISSUES = "deployment_issues" # Deployment-specific problems
    UNKNOWN = "unknown"                    # Unclassified failures


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

        # Advanced Intelligence Features
        self.enable_ml_failure_classification: bool = kwargs.get(
            "enable_ml_failure_classification", True
        )
        self.enable_performance_profiling: bool = kwargs.get(
            "enable_performance_profiling", True
        )
        self.enable_security_analysis: bool = kwargs.get(
            "enable_security_analysis", True
        )
        self.enable_deployment_health_monitoring: bool = kwargs.get(
            "enable_deployment_health_monitoring", True
        )
        self.enable_cross_platform_correlation: bool = kwargs.get(
            "enable_cross_platform_correlation", True
        )
        self.enable_build_constellation_tracking: bool = kwargs.get(
            "enable_build_constellation_tracking", True
        )

        # ML Model Configuration
        self.failure_classification_model_path: Optional[str] = kwargs.get(
            "failure_classification_model_path"
        )
        self.failure_classification_confidence_threshold: float = kwargs.get(
            "failure_classification_confidence_threshold", 0.7
        )

        # Performance Analytics Configuration
        self.performance_baseline_days: int = kwargs.get("performance_baseline_days", 30)
        self.performance_alert_threshold: float = kwargs.get(
            "performance_alert_threshold", 2.0
        )  # 2x slower than baseline
        self.resource_efficiency_threshold: float = kwargs.get(
            "resource_efficiency_threshold", 0.6
        )  # 60% efficiency minimum

        # Security Integration
        self.security_scan_integrations: List[str] = kwargs.get(
            "security_scan_integrations", ["snyk", "sonarqube", "veracode", "checkmarx"]
        )
        self.compliance_frameworks: List[str] = kwargs.get(
            "compliance_frameworks", ["sox", "pci", "hipaa", "gdpr"]
        )
        self.security_risk_threshold: float = kwargs.get("security_risk_threshold", 0.7)

        # Deployment Health Monitoring
        self.health_check_endpoints: List[str] = kwargs.get("health_check_endpoints", [])
        self.canary_monitoring_duration_minutes: int = kwargs.get(
            "canary_monitoring_duration_minutes", 30
        )
        self.rollback_trigger_error_rate: float = kwargs.get(
            "rollback_trigger_error_rate", 0.05
        )  # 5% error rate

        # Cross-Platform Intelligence
        self.constellation_correlation_window_hours: int = kwargs.get(
            "constellation_correlation_window_hours", 2
        )
        self.constellation_minimum_correlation_score: float = kwargs.get(
            "constellation_minimum_correlation_score", 0.6
        )

        # Advanced Analytics
        self.enable_pattern_detection: bool = kwargs.get("enable_pattern_detection", True)
        self.pattern_detection_window_days: int = kwargs.get(
            "pattern_detection_window_days", 14
        )
        self.enable_predictive_analytics: bool = kwargs.get(
            "enable_predictive_analytics", True
        )
        
        # Real-time Processing
        self.enable_real_time_alerts: bool = kwargs.get("enable_real_time_alerts", True)
        self.webhook_processing_timeout_ms: int = kwargs.get(
            "webhook_processing_timeout_ms", 5000
        )
        self.enable_streaming_analytics: bool = kwargs.get(
            "enable_streaming_analytics", False
        )


class BaseCICDAdapter(BaseAdapter):
    """Base class for CI/CD platform adapters."""

    def __init__(self, config: CICDAdapterConfig):
        super().__init__(config)
        self.cicd_config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = APIRateLimiter(config.api_rate_limit)
        
        # Advanced Intelligence Components
        self.failure_classifier: Optional['FailureClassifier'] = None
        self.performance_analyzer: Optional['PerformanceAnalyzer'] = None
        self.security_analyzer: Optional['SecurityAnalyzer'] = None
        self.deployment_health_monitor: Optional['DeploymentHealthMonitor'] = None
        self.build_constellation_manager: Optional['BuildConstellationManager'] = None
        
        # Caching and State Management
        self.performance_baselines: Dict[str, PerformanceProfile] = {}
        self.active_constellations: Dict[str, BuildConstellation] = {}
        self.failure_patterns_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.security_scan_cache: Dict[str, SecurityAnalysis] = {}
        
        # Real-time Analytics State
        self.real_time_metrics: Dict[str, Any] = {
            "webhook_processing_times": [],
            "correlation_detection_rate": 0.0,
            "active_builds_count": 0,
            "failure_rate_last_hour": 0.0,
            "average_build_duration": 0.0
        }

    async def start(self) -> None:
        """Initialize the CI/CD adapter with advanced intelligence components."""
        await super().start()

        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=self.cicd_config.request_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=self.cicd_config.concurrent_requests),
        )

        # Initialize Advanced Intelligence Components
        await self._initialize_intelligence_components()

        self.logger.info(
            "Enhanced CI/CD adapter started",
            platform=self.cicd_config.platform.value,
            repositories=len(self.cicd_config.repositories),
            ml_classification=self.cicd_config.enable_ml_failure_classification,
            performance_profiling=self.cicd_config.enable_performance_profiling,
            security_analysis=self.cicd_config.enable_security_analysis,
            deployment_health=self.cicd_config.enable_deployment_health_monitoring,
        )

    async def _initialize_intelligence_components(self) -> None:
        """Initialize advanced intelligence components."""
        try:
            # Initialize ML Failure Classification
            if self.cicd_config.enable_ml_failure_classification:
                self.failure_classifier = FailureClassifier(
                    model_path=self.cicd_config.failure_classification_model_path,
                    confidence_threshold=self.cicd_config.failure_classification_confidence_threshold
                )
                await self.failure_classifier.initialize()

            # Initialize Performance Analytics
            if self.cicd_config.enable_performance_profiling:
                self.performance_analyzer = PerformanceAnalyzer(
                    baseline_days=self.cicd_config.performance_baseline_days,
                    alert_threshold=self.cicd_config.performance_alert_threshold
                )
                await self.performance_analyzer.initialize()

            # Initialize Security Analysis
            if self.cicd_config.enable_security_analysis:
                self.security_analyzer = SecurityAnalyzer(
                    scan_integrations=self.cicd_config.security_scan_integrations,
                    compliance_frameworks=self.cicd_config.compliance_frameworks,
                    risk_threshold=self.cicd_config.security_risk_threshold
                )
                await self.security_analyzer.initialize()

            # Initialize Deployment Health Monitoring
            if self.cicd_config.enable_deployment_health_monitoring:
                self.deployment_health_monitor = DeploymentHealthMonitor(
                    health_endpoints=self.cicd_config.health_check_endpoints,
                    canary_duration=self.cicd_config.canary_monitoring_duration_minutes,
                    rollback_threshold=self.cicd_config.rollback_trigger_error_rate
                )
                await self.deployment_health_monitor.initialize()

            # Initialize Build Constellation Manager
            if self.cicd_config.enable_build_constellation_tracking:
                self.build_constellation_manager = BuildConstellationManager(
                    correlation_window=self.cicd_config.constellation_correlation_window_hours,
                    minimum_correlation=self.cicd_config.constellation_minimum_correlation_score
                )
                await self.build_constellation_manager.initialize()

            self.logger.info("Advanced intelligence components initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize intelligence components", error=str(e))
            # Continue without advanced features rather than fail completely
            self._disable_advanced_features()

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
        """Transform platform-specific data to ContextItem with advanced intelligence."""
        start_time = datetime.utcnow()
        
        try:
            # Basic platform transformation
            item = await self._transform_platform_item(raw_item)
            
            # Initialize metrics if not present
            if not item.metrics:
                item.metrics = {}

            # Add artifact management metadata
            item.metrics.update(self._extract_artifact_metadata(raw_item))

            # Apply Advanced Intelligence Analysis
            await self._apply_advanced_analysis(item, raw_item)
            
            # Update real-time metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_real_time_metrics(processing_time, item)

            return item
            
        except Exception as e:
            self.logger.error(
                "Failed to transform CI/CD item",
                platform=self.cicd_config.platform.value,
                error=str(e),
                raw_item_keys=list(raw_item.keys()) if raw_item else None,
            )
            raise

    async def _apply_advanced_analysis(self, item: ContextItem, raw_item: Dict[str, Any]) -> None:
        """Apply advanced intelligence analysis to the context item."""
        try:
            # ML-based Failure Classification
            if self.failure_classifier and self._is_failure_event(item):
                failure_classification = await self.failure_classifier.classify_failure(item, raw_item)
                if failure_classification:
                    item.metrics["failure_classification"] = asdict(failure_classification)

            # Performance Profiling
            if self.performance_analyzer:
                performance_profile = await self.performance_analyzer.analyze_performance(item, raw_item)
                if performance_profile:
                    item.metrics["performance_profile"] = asdict(performance_profile)

            # Security Analysis
            if self.security_analyzer and self._has_security_context(item):
                security_analysis = await self.security_analyzer.analyze_security(item, raw_item)
                if security_analysis:
                    item.metrics["security_analysis"] = asdict(security_analysis)

            # Deployment Health Monitoring
            if self.deployment_health_monitor and self._is_deployment_event(item):
                health_analysis = await self.deployment_health_monitor.analyze_health(item, raw_item)
                if health_analysis:
                    item.metrics["deployment_health"] = asdict(health_analysis)

            # Build Constellation Tracking
            if self.build_constellation_manager:
                constellation_info = await self.build_constellation_manager.track_build(item, raw_item)
                if constellation_info:
                    item.metrics["build_constellation"] = constellation_info

            # Add intelligence metadata
            item.metrics["intelligence_applied"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "features": self._get_enabled_features(),
                "processing_version": "v2.0.0"
            }

        except Exception as e:
            self.logger.warning(
                "Advanced analysis failed for item",
                item_id=getattr(item, 'source_id', 'unknown'),
                error=str(e)
            )
            # Don't fail the entire transformation if advanced analysis fails

    def _is_failure_event(self, item: ContextItem) -> bool:
        """Check if the item represents a failure event."""
        if not item.metrics:
            return False
            
        status = item.metrics.get("status", "").lower()
        conclusion = item.metrics.get("conclusion", "").lower()
        
        return any(status_indicator in [status, conclusion] 
                  for status_indicator in ["failed", "failure", "error", "cancelled", "timeout"])

    def _has_security_context(self, item: ContextItem) -> bool:
        """Check if the item has security-relevant context."""
        if not item.content and not item.metrics:
            return False
            
        security_keywords = [
            "security", "vulnerability", "scan", "audit", "compliance",
            "sonar", "snyk", "veracode", "checkmarx", "cve"
        ]
        
        content_str = (item.content or "").lower()
        title_str = (item.title or "").lower()
        
        return any(keyword in content_str or keyword in title_str 
                  for keyword in security_keywords)

    def _is_deployment_event(self, item: ContextItem) -> bool:
        """Check if the item represents a deployment event."""
        if not item.entity_type:
            return False
            
        return "deployment" in item.entity_type.lower()

    def _get_enabled_features(self) -> List[str]:
        """Get list of enabled advanced features."""
        features = []
        if self.failure_classifier:
            features.append("ml_failure_classification")
        if self.performance_analyzer:
            features.append("performance_profiling")
        if self.security_analyzer:
            features.append("security_analysis")
        if self.deployment_health_monitor:
            features.append("deployment_health_monitoring")
        if self.build_constellation_manager:
            features.append("build_constellation_tracking")
        return features

    def _update_real_time_metrics(self, processing_time: float, item: ContextItem) -> None:
        """Update real-time processing metrics."""
        # Track webhook processing times
        self.real_time_metrics["webhook_processing_times"].append(processing_time)
        
        # Keep only last 100 processing times
        if len(self.real_time_metrics["webhook_processing_times"]) > 100:
            self.real_time_metrics["webhook_processing_times"] = \
                self.real_time_metrics["webhook_processing_times"][-100:]
        
        # Update average processing time
        if self.real_time_metrics["webhook_processing_times"]:
            self.real_time_metrics["average_processing_time"] = \
                sum(self.real_time_metrics["webhook_processing_times"]) / \
                len(self.real_time_metrics["webhook_processing_times"])

    def _disable_advanced_features(self) -> None:
        """Disable advanced features if initialization fails."""
        self.failure_classifier = None
        self.performance_analyzer = None
        self.security_analyzer = None
        self.deployment_health_monitor = None
        self.build_constellation_manager = None
        self.logger.warning("Advanced features disabled due to initialization failure")

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


# Advanced Intelligence Components

class FailureClassifier:
    """ML-based failure classification system."""
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.7):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.failure_patterns = self._load_failure_patterns()
        
    async def initialize(self) -> None:
        """Initialize the failure classifier."""
        try:
            if self.model_path and Path(self.model_path).exists():
                # Load ML model (placeholder for actual ML model loading)
                self.model = await self._load_ml_model()
            else:
                # Use rule-based classification
                logger.info("Using rule-based failure classification")
        except Exception as e:
            logger.warning(f"Failed to initialize ML model, using rules: {e}")
    
    async def classify_failure(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[FailureClassification]:
        """Classify a failure event using ML or rule-based approach."""
        try:
            if self.model:
                return await self._classify_with_ml(item, raw_item)
            else:
                return await self._classify_with_rules(item, raw_item)
        except Exception as e:
            logger.warning(f"Failure classification failed: {e}")
            return None
    
    async def _classify_with_ml(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[FailureClassification]:
        """Classify failure using ML model."""
        # Extract features for ML model
        features = self._extract_failure_features(item, raw_item)
        
        # Get prediction (placeholder for actual ML prediction)
        prediction = await self._predict_failure_category(features)
        
        if prediction["confidence"] >= self.confidence_threshold:
            return FailureClassification(
                primary_category=prediction["category"],
                confidence=prediction["confidence"],
                subcategory=prediction.get("subcategory"),
                root_cause_indicators=prediction.get("indicators", []),
                suggested_fixes=self._get_suggested_fixes(prediction["category"]),
                classification_metadata={"method": "ml", "features_used": list(features.keys())}
            )
        
        return None
    
    async def _classify_with_rules(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[FailureClassification]:
        """Classify failure using rule-based approach."""
        log_content = self._extract_logs(item, raw_item)
        
        for pattern in self.failure_patterns:
            if self._matches_pattern(log_content, pattern):
                return FailureClassification(
                    primary_category=pattern["category"],
                    confidence=pattern["confidence"],
                    subcategory=pattern.get("subcategory"),
                    root_cause_indicators=pattern.get("indicators", []),
                    suggested_fixes=pattern.get("fixes", []),
                    classification_metadata={"method": "rules", "pattern_matched": pattern["name"]}
                )
        
        return FailureClassification(
            primary_category=FailureCategory.UNKNOWN.value,
            confidence=0.5,
            classification_metadata={"method": "rules", "pattern_matched": "none"}
        )
    
    def _load_failure_patterns(self) -> List[Dict[str, Any]]:
        """Load predefined failure patterns."""
        return [
            {
                "name": "compilation_error",
                "category": FailureCategory.CODE_QUALITY.value,
                "patterns": [r"compilation failed", r"syntax error", r"cannot find symbol"],
                "confidence": 0.9,
                "indicators": ["compilation", "syntax"],
                "fixes": ["Check code syntax", "Verify imports and dependencies"]
            },
            {
                "name": "test_failure",
                "category": FailureCategory.TEST_FAILURES.value,
                "patterns": [r"test.*failed", r"assertion.*failed", r"\d+ tests? failed"],
                "confidence": 0.95,
                "indicators": ["test", "assertion"],
                "fixes": ["Review failing tests", "Check test data and expectations"]
            },
            {
                "name": "dependency_conflict",
                "category": FailureCategory.DEPENDENCY_ISSUES.value,
                "patterns": [r"dependency conflict", r"version.*incompatible", r"could not resolve"],
                "confidence": 0.85,
                "indicators": ["dependency", "version", "conflict"],
                "fixes": ["Update dependency versions", "Resolve version conflicts"]
            },
            {
                "name": "timeout",
                "category": FailureCategory.INFRASTRUCTURE.value,
                "patterns": [r"timeout", r"timed out", r"connection.*timeout"],
                "confidence": 0.8,
                "indicators": ["timeout", "connection"],
                "fixes": ["Increase timeout values", "Check network connectivity"]
            },
            {
                "name": "security_scan_failure",
                "category": FailureCategory.SECURITY_VIOLATIONS.value,
                "patterns": [r"security.*violation", r"vulnerability.*found", r"security.*scan.*failed"],
                "confidence": 0.9,
                "indicators": ["security", "vulnerability"],
                "fixes": ["Address security vulnerabilities", "Update vulnerable dependencies"]
            }
        ]
    
    def _extract_failure_features(self, item: ContextItem, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for ML classification."""
        return {
            "duration_ms": item.metrics.get("duration_ms", 0),
            "exit_code": item.metrics.get("exit_code", 0),
            "log_length": len(self._extract_logs(item, raw_item)),
            "error_keywords_count": self._count_error_keywords(item, raw_item),
            "platform": item.metrics.get("platform", "unknown"),
            "job_type": item.entity_type or "unknown"
        }
    
    def _extract_logs(self, item: ContextItem, raw_item: Dict[str, Any]) -> str:
        """Extract log content from the item."""
        logs = []
        
        # From content
        if item.content:
            logs.append(item.content)
        
        # From raw data
        if isinstance(raw_item.get("data"), dict):
            data = raw_item["data"]
            if "logs" in data:
                logs.append(str(data["logs"]))
            if "error_message" in data:
                logs.append(str(data["error_message"]))
        
        return "\n".join(logs).lower()
    
    def _matches_pattern(self, text: str, pattern: Dict[str, Any]) -> bool:
        """Check if text matches any of the failure patterns."""
        for regex_pattern in pattern["patterns"]:
            if re.search(regex_pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _count_error_keywords(self, item: ContextItem, raw_item: Dict[str, Any]) -> int:
        """Count error-related keywords in the content."""
        error_keywords = [
            "error", "failed", "failure", "exception", "timeout",
            "denied", "forbidden", "unauthorized", "conflict"
        ]
        
        text = self._extract_logs(item, raw_item)
        return sum(1 for keyword in error_keywords if keyword in text)
    
    def _get_suggested_fixes(self, category: str) -> List[str]:
        """Get suggested fixes for a failure category."""
        fixes_map = {
            FailureCategory.CODE_QUALITY.value: [
                "Run code linters and fix syntax errors",
                "Check code formatting and style",
                "Review type annotations and imports"
            ],
            FailureCategory.TEST_FAILURES.value: [
                "Review failing test cases",
                "Check test data and mock configurations",
                "Update test expectations if code behavior changed"
            ],
            FailureCategory.DEPENDENCY_ISSUES.value: [
                "Update dependency versions",
                "Resolve version conflicts",
                "Check package registry availability"
            ],
            FailureCategory.INFRASTRUCTURE.value: [
                "Check resource availability",
                "Verify network connectivity",
                "Increase timeout values"
            ],
            FailureCategory.SECURITY_VIOLATIONS.value: [
                "Address identified vulnerabilities",
                "Update security configurations",
                "Review security scan results"
            ]
        }
        
        return fixes_map.get(category, ["Review logs and error messages"])
    
    async def _load_ml_model(self):
        """Load ML model (placeholder for actual implementation)."""
        # This would load an actual ML model like scikit-learn, TensorFlow, etc.
        return None
    
    async def _predict_failure_category(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict failure category using ML model."""
        # Placeholder for actual ML prediction
        return {
            "category": FailureCategory.UNKNOWN.value,
            "confidence": 0.5,
            "subcategory": None,
            "indicators": []
        }


class PerformanceAnalyzer:
    """Advanced performance analytics for CI/CD pipelines."""
    
    def __init__(self, baseline_days: int = 30, alert_threshold: float = 2.0):
        self.baseline_days = baseline_days
        self.alert_threshold = alert_threshold
        self.baselines: Dict[str, PerformanceProfile] = {}
        
    async def initialize(self) -> None:
        """Initialize performance analyzer."""
        # Load historical baselines if available
        await self._load_performance_baselines()
        
    async def analyze_performance(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[PerformanceProfile]:
        """Analyze performance metrics for a CI/CD event."""
        try:
            if not item.metrics or not item.metrics.get("duration_ms"):
                return None
            
            current_duration = item.metrics["duration_ms"]
            job_key = self._get_job_key(item)
            
            # Get or create baseline
            baseline = self.baselines.get(job_key)
            if not baseline:
                baseline = await self._create_baseline(job_key, item)
                self.baselines[job_key] = baseline
            
            # Calculate performance metrics
            performance_ratio = current_duration / baseline.avg_duration_ms if baseline.avg_duration_ms > 0 else 1.0
            
            # Determine trend
            trend_direction = self._determine_trend(performance_ratio)
            
            # Calculate performance score (0-100, higher is better)
            performance_score = min(100, max(0, 100 - (performance_ratio - 1) * 50))
            
            return PerformanceProfile(
                avg_duration_ms=baseline.avg_duration_ms,
                p90_duration_ms=baseline.p90_duration_ms,
                p95_duration_ms=baseline.p95_duration_ms,
                success_rate=baseline.success_rate,
                trend_direction=trend_direction,
                bottleneck_stages=self._identify_bottlenecks(item, raw_item),
                resource_efficiency=self._calculate_resource_efficiency(item, raw_item),
                performance_score=performance_score
            )
            
        except Exception as e:
            logger.warning(f"Performance analysis failed: {e}")
            return None
    
    def _get_job_key(self, item: ContextItem) -> str:
        """Generate a key for job performance tracking."""
        platform = item.metrics.get("platform", "unknown")
        job_name = item.metrics.get("job_name") or item.metrics.get("workflow_name") or item.entity_type
        project = item.project_id or "unknown"
        return f"{platform}:{project}:{job_name}"
    
    async def _create_baseline(self, job_key: str, item: ContextItem) -> PerformanceProfile:
        """Create performance baseline for a job."""
        # This would typically query historical data
        return PerformanceProfile(
            avg_duration_ms=item.metrics.get("duration_ms", 0),
            p90_duration_ms=item.metrics.get("duration_ms", 0) * 1.5,
            p95_duration_ms=item.metrics.get("duration_ms", 0) * 2.0,
            success_rate=1.0,
            trend_direction="stable"
        )
    
    def _determine_trend(self, performance_ratio: float) -> str:
        """Determine performance trend based on ratio."""
        if performance_ratio < 0.9:
            return "improving"
        elif performance_ratio > 1.1:
            return "degrading"
        else:
            return "stable"
    
    def _identify_bottlenecks(self, item: ContextItem, raw_item: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Check for common bottleneck indicators
        if item.metrics.get("duration_ms", 0) > 900000:  # 15 minutes
            bottlenecks.append("long_running_job")
        
        # Check for specific stage information
        if "stages" in item.metrics:
            stages = item.metrics["stages"]
            if isinstance(stages, list):
                for stage in stages:
                    if isinstance(stage, dict) and stage.get("duration_ms", 0) > 300000:  # 5 minutes
                        bottlenecks.append(f"slow_stage_{stage.get('name', 'unknown')}")
        
        return bottlenecks
    
    def _calculate_resource_efficiency(self, item: ContextItem, raw_item: Dict[str, Any]) -> float:
        """Calculate resource utilization efficiency."""
        # Placeholder for resource efficiency calculation
        # This would typically analyze CPU, memory, and I/O usage
        return 0.75  # Default 75% efficiency
    
    async def _load_performance_baselines(self) -> None:
        """Load performance baselines from storage."""
        # This would load from database or cache
        pass


class SecurityAnalyzer:
    """Security analysis for CI/CD events."""
    
    def __init__(self, scan_integrations: List[str], compliance_frameworks: List[str], risk_threshold: float = 0.7):
        self.scan_integrations = scan_integrations
        self.compliance_frameworks = compliance_frameworks
        self.risk_threshold = risk_threshold
        
    async def initialize(self) -> None:
        """Initialize security analyzer."""
        pass
    
    async def analyze_security(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[SecurityAnalysis]:
        """Analyze security aspects of a CI/CD event."""
        try:
            # Extract security scan results
            scan_results = self._extract_security_scans(item, raw_item)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(scan_results, item)
            
            # Check compliance violations
            violations = self._check_compliance_violations(item, raw_item)
            
            # Generate recommendations
            recommendations = self._generate_security_recommendations(scan_results, violations)
            
            return SecurityAnalysis(
                risk_score=risk_score,
                vulnerability_count=scan_results.get("vulnerability_count", 0),
                compliance_violations=violations,
                security_gates_passed=risk_score < self.risk_threshold,
                requires_approval=risk_score >= self.risk_threshold,
                security_recommendations=recommendations,
                scan_results=scan_results
            )
            
        except Exception as e:
            logger.warning(f"Security analysis failed: {e}")
            return None
    
    def _extract_security_scans(self, item: ContextItem, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract security scan results from the event."""
        # Placeholder for extracting security scan results
        return {
            "vulnerability_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "scan_tools": []
        }
    
    def _calculate_risk_score(self, scan_results: Dict[str, Any], item: ContextItem) -> float:
        """Calculate overall security risk score."""
        base_score = 0.0
        
        # Weight vulnerabilities by severity
        critical = scan_results.get("critical_count", 0)
        high = scan_results.get("high_count", 0)
        medium = scan_results.get("medium_count", 0)
        low = scan_results.get("low_count", 0)
        
        weighted_score = (critical * 1.0) + (high * 0.7) + (medium * 0.4) + (low * 0.1)
        
        # Normalize to 0-1 scale
        max_expected_vulnerabilities = 20
        normalized_score = min(1.0, weighted_score / max_expected_vulnerabilities)
        
        return normalized_score
    
    def _check_compliance_violations(self, item: ContextItem, raw_item: Dict[str, Any]) -> List[str]:
        """Check for compliance framework violations."""
        violations = []
        
        # Check for common compliance issues
        if not item.metrics.get("security_scan_passed", True):
            violations.append("security_scan_failed")
        
        if item.metrics.get("secrets_exposed", False):
            violations.append("secrets_exposure")
        
        return violations
    
    def _generate_security_recommendations(self, scan_results: Dict[str, Any], violations: List[str]) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        if scan_results.get("critical_count", 0) > 0:
            recommendations.append("Address critical vulnerabilities immediately")
        
        if scan_results.get("high_count", 0) > 0:
            recommendations.append("Review and fix high-severity vulnerabilities")
        
        if "secrets_exposure" in violations:
            recommendations.append("Remove exposed secrets and rotate credentials")
        
        return recommendations


class DeploymentHealthMonitor:
    """Monitor deployment health and performance."""
    
    def __init__(self, health_endpoints: List[str], canary_duration: int, rollback_threshold: float):
        self.health_endpoints = health_endpoints
        self.canary_duration = canary_duration
        self.rollback_threshold = rollback_threshold
        
    async def initialize(self) -> None:
        """Initialize deployment health monitor."""
        pass
    
    async def analyze_health(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[DeploymentHealth]:
        """Analyze deployment health metrics."""
        try:
            # Calculate health score
            health_score = await self._calculate_health_score(item, raw_item)
            
            # Analyze error rate changes
            error_rate_change = await self._analyze_error_rate_change(item)
            
            # Check for rollback indicators
            rollback_indicators = self._check_rollback_indicators(item, error_rate_change)
            
            # Get canary metrics if applicable
            canary_metrics = await self._get_canary_metrics(item)
            
            return DeploymentHealth(
                health_score=health_score,
                error_rate_change=error_rate_change,
                performance_impact=0.0,  # Placeholder
                rollback_indicators=rollback_indicators,
                canary_metrics=canary_metrics,
                environment_status="healthy" if health_score > 0.8 else "degraded",
                monitoring_alerts=[]
            )
            
        except Exception as e:
            logger.warning(f"Deployment health analysis failed: {e}")
            return None
    
    async def _calculate_health_score(self, item: ContextItem, raw_item: Dict[str, Any]) -> float:
        """Calculate overall deployment health score."""
        # Placeholder for health score calculation
        if item.metrics.get("status") == "success":
            return 0.95
        elif item.metrics.get("status") == "failed":
            return 0.2
        else:
            return 0.7
    
    async def _analyze_error_rate_change(self, item: ContextItem) -> float:
        """Analyze error rate changes post-deployment."""
        # Placeholder for error rate analysis
        return 0.0
    
    def _check_rollback_indicators(self, item: ContextItem, error_rate_change: float) -> List[str]:
        """Check for indicators that suggest a rollback might be needed."""
        indicators = []
        
        if error_rate_change > self.rollback_threshold:
            indicators.append("error_rate_spike")
        
        if item.metrics.get("deployment_status") == "failed":
            indicators.append("deployment_failure")
        
        return indicators
    
    async def _get_canary_metrics(self, item: ContextItem) -> Dict[str, float]:
        """Get canary deployment metrics."""
        # Placeholder for canary metrics
        return {
            "success_rate": 0.95,
            "error_rate": 0.02,
            "response_time_p95": 150.0
        }


class BuildConstellationManager:
    """Manage build constellations across platforms."""
    
    def __init__(self, correlation_window: int, minimum_correlation: float):
        self.correlation_window = correlation_window
        self.minimum_correlation = minimum_correlation
        self.active_constellations: Dict[str, BuildConstellation] = {}
        
    async def initialize(self) -> None:
        """Initialize build constellation manager."""
        pass
    
    async def track_build(self, item: ContextItem, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Track build as part of constellation."""
        try:
            # Extract correlation identifiers
            commit_sha = self._extract_commit_sha(item)
            if not commit_sha:
                return None
            
            # Find or create constellation
            constellation = await self._find_or_create_constellation(commit_sha, item)
            
            # Add build to constellation
            build_info = self._create_build_info(item, raw_item)
            constellation.related_builds.append(build_info)
            
            # Update constellation status
            await self._update_constellation_status(constellation)
            
            return {
                "constellation_id": constellation.primary_build_id,
                "correlation_strength": constellation.correlation_strength,
                "total_builds": constellation.total_builds,
                "completion_status": constellation.completion_status
            }
            
        except Exception as e:
            logger.warning(f"Build constellation tracking failed: {e}")
            return None
    
    def _extract_commit_sha(self, item: ContextItem) -> Optional[str]:
        """Extract commit SHA from the item."""
        if not item.metrics:
            return None
        
        return (item.metrics.get("commit_sha") or 
                item.metrics.get("sha") or 
                item.metrics.get("head_sha"))
    
    async def _find_or_create_constellation(self, commit_sha: str, item: ContextItem) -> BuildConstellation:
        """Find existing constellation or create new one."""
        # Look for existing constellation with same commit SHA
        for constellation in self.active_constellations.values():
            if constellation.commit_sha == commit_sha:
                return constellation
        
        # Create new constellation
        constellation = BuildConstellation(
            primary_build_id=item.source_id or "unknown",
            commit_sha=commit_sha,
            branch_name=item.metrics.get("branch_name") if item.metrics else None
        )
        
        self.active_constellations[constellation.primary_build_id] = constellation
        return constellation
    
    def _create_build_info(self, item: ContextItem, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """Create build information for constellation tracking."""
        return {
            "build_id": item.source_id,
            "platform": raw_item.get("type", "unknown"),
            "status": item.metrics.get("status") if item.metrics else None,
            "duration_ms": item.metrics.get("duration_ms") if item.metrics else None,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None
        }
    
    async def _update_constellation_status(self, constellation: BuildConstellation) -> None:
        """Update constellation status based on all builds."""
        constellation.total_builds = len(constellation.related_builds)
        constellation.successful_builds = sum(1 for build in constellation.related_builds 
                                            if build.get("status") == "success")
        constellation.failed_builds = sum(1 for build in constellation.related_builds 
                                        if build.get("status") in ["failed", "error"])
        
        # Determine completion status
        if constellation.failed_builds > 0:
            constellation.completion_status = "failed"
        elif constellation.successful_builds == constellation.total_builds:
            constellation.completion_status = "completed"
        else:
            constellation.completion_status = "in_progress"
        
        constellation.updated_at = datetime.utcnow()


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
