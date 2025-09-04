"""Advanced monitoring and quality metrics for the deduplication system.

This module provides comprehensive monitoring, quality assessment, and performance
tracking for the deduplication system, including real-time metrics, quality
scoring, and automated alerts.
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import structlog

from .deduplication_system import DeduplicationResult, DuplicateGroup

logger = structlog.get_logger(__name__)


@dataclass
class DeduplicationMetrics:
    """Comprehensive deduplication metrics."""

    # Processing metrics
    total_items_processed: int = 0
    processing_time_seconds: float = 0.0
    items_per_second: float = 0.0

    # Duplicate detection metrics
    exact_duplicates_found: int = 0
    semantic_duplicates_found: int = 0
    temporal_clusters_created: int = 0

    # Quality metrics
    precision_score: float = 0.0
    recall_score: float = 0.0
    f1_score: float = 0.0
    quality_score: float = 0.0

    # Merge strategy effectiveness
    auto_merge_success_rate: float = 0.0
    manual_review_required: int = 0
    merge_conflicts: int = 0

    # System health
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0
    error_count: int = 0

    # Data quality indicators
    content_hash_collision_rate: float = 0.0
    embedding_quality_score: float = 0.0
    temporal_clustering_accuracy: float = 0.0


@dataclass
class QualityAssessment:
    """Quality assessment for deduplication results."""

    overall_score: float = 0.0
    accuracy_score: float = 0.0
    efficiency_score: float = 0.0
    reliability_score: float = 0.0

    # Detailed quality indicators
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    content_integrity_score: float = 0.0
    metadata_preservation_score: float = 0.0

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    warning_flags: List[str] = field(default_factory=list)


@dataclass
class DeduplicationAlert:
    """Alert for deduplication system issues."""

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "info"  # info, warning, error, critical
    category: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False


class QualityAnalyzer:
    """Analyzes quality of deduplication results."""

    def __init__(self):
        self.logger = logger.bind(component="quality_analyzer")

    async def assess_quality(
        self, result: DeduplicationResult, ground_truth: Optional[Dict[str, Any]] = None
    ) -> QualityAssessment:
        """Comprehensive quality assessment of deduplication results."""
        assessment = QualityAssessment()

        try:
            # Calculate accuracy metrics
            assessment.accuracy_score = self._calculate_accuracy(result, ground_truth)

            # Calculate efficiency metrics
            assessment.efficiency_score = self._calculate_efficiency(result)

            # Calculate reliability metrics
            assessment.reliability_score = self._calculate_reliability(result)

            # Calculate overall score
            assessment.overall_score = (
                assessment.accuracy_score * 0.4
                + assessment.efficiency_score * 0.3
                + assessment.reliability_score * 0.3
            )

            # Generate recommendations
            assessment.recommendations = self._generate_recommendations(
                result, assessment
            )

            # Check for warning conditions
            assessment.warning_flags = self._check_warning_conditions(
                result, assessment
            )

            self.logger.info(
                "Quality assessment completed",
                overall_score=assessment.overall_score,
                accuracy_score=assessment.accuracy_score,
                efficiency_score=assessment.efficiency_score,
            )

            return assessment

        except Exception as e:
            self.logger.error("Quality assessment failed", error=str(e))
            raise

    def _calculate_accuracy(
        self, result: DeduplicationResult, ground_truth: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate accuracy of duplicate detection."""
        if not ground_truth:
            # Fallback heuristics based on confidence scores
            high_confidence_groups = [
                g for g in result.duplicate_groups if g.confidence >= 0.9
            ]
            return len(high_confidence_groups) / max(len(result.duplicate_groups), 1)

        # Use ground truth for precise calculation
        true_positives = ground_truth.get("true_positives", 0)
        false_positives = ground_truth.get("false_positives", 0)
        false_negatives = ground_truth.get("false_negatives", 0)

        precision = true_positives / max(true_positives + false_positives, 1)
        recall = true_positives / max(true_positives + false_negatives, 1)

        return (precision + recall) / 2

    def _calculate_efficiency(self, result: DeduplicationResult) -> float:
        """Calculate processing efficiency."""
        if result.total_items == 0:
            return 1.0

        # Items processed per second (target: 100+ items/second)
        items_per_second = result.total_items / max(result.processing_time_seconds, 0.1)
        throughput_score = min(1.0, items_per_second / 100.0)

        # Duplicate detection rate
        total_duplicates = result.exact_duplicates + result.semantic_duplicates
        detection_rate = total_duplicates / result.total_items

        return (throughput_score * 0.6) + (detection_rate * 0.4)

    def _calculate_reliability(self, result: DeduplicationResult) -> float:
        """Calculate system reliability."""
        # Confidence distribution
        confidence_scores = [group.confidence for group in result.duplicate_groups]
        avg_confidence = sum(confidence_scores) / max(len(confidence_scores), 1)

        # Merge success rate
        successful_merges = result.merged_items
        total_groups = len(result.duplicate_groups)
        merge_rate = successful_merges / max(total_groups, 1)

        return (avg_confidence * 0.5) + (merge_rate * 0.5)

    def _generate_recommendations(
        self, result: DeduplicationResult, assessment: QualityAssessment
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if assessment.accuracy_score < 0.8:
            recommendations.append(
                "Consider adjusting similarity thresholds to improve accuracy"
            )

        if assessment.efficiency_score < 0.7:
            recommendations.append(
                "Optimize batch processing or consider parallel execution"
            )

        if result.processing_time_seconds > 300:  # 5 minutes
            recommendations.append(
                "Processing time is high; consider implementing incremental deduplication"
            )

        manual_review_rate = (len(result.duplicate_groups) - result.merged_items) / max(
            len(result.duplicate_groups), 1
        )
        if manual_review_rate > 0.3:
            recommendations.append(
                "High manual review rate; consider refining automatic merge criteria"
            )

        return recommendations

    def _check_warning_conditions(
        self, result: DeduplicationResult, assessment: QualityAssessment
    ) -> List[str]:
        """Check for warning conditions."""
        warnings = []

        if assessment.overall_score < 0.6:
            warnings.append("Overall quality score is below acceptable threshold")

        if result.processing_time_seconds > 600:  # 10 minutes
            warnings.append("Processing time exceeds recommended limits")

        if len(result.duplicate_groups) == 0 and result.total_items > 100:
            warnings.append(
                "No duplicates found in large dataset - verify algorithm sensitivity"
            )

        exact_duplicate_rate = result.exact_duplicates / max(result.total_items, 1)
        if exact_duplicate_rate > 0.5:
            warnings.append("Unusually high exact duplicate rate - check data source")

        return warnings


class PerformanceMonitor:
    """Real-time performance monitoring for deduplication operations."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = deque(maxlen=window_size)
        self.alerts = deque(maxlen=1000)
        self.logger = logger.bind(component="performance_monitor")

    def record_operation(self, result: DeduplicationResult) -> None:
        """Record metrics from deduplication operation."""
        metrics = DeduplicationMetrics(
            total_items_processed=result.total_items,
            processing_time_seconds=result.processing_time_seconds,
            items_per_second=result.total_items
            / max(result.processing_time_seconds, 0.1),
            exact_duplicates_found=result.exact_duplicates,
            semantic_duplicates_found=result.semantic_duplicates,
            temporal_clusters_created=result.temporal_clusters,
            quality_score=result.quality_score,
        )

        self.metrics_history.append(metrics)
        self._check_performance_thresholds(metrics)

    def _check_performance_thresholds(self, metrics: DeduplicationMetrics) -> None:
        """Check performance against thresholds and generate alerts."""
        # Processing speed alert
        if metrics.items_per_second < 10:
            self._create_alert(
                severity="warning",
                category="performance",
                message=f"Low processing speed: {metrics.items_per_second:.2f} items/second",
                details={"threshold": 10, "actual": metrics.items_per_second},
            )

        # Processing time alert
        if metrics.processing_time_seconds > 300:
            self._create_alert(
                severity="warning",
                category="performance",
                message=f"Long processing time: {metrics.processing_time_seconds:.2f} seconds",
                details={"threshold": 300, "actual": metrics.processing_time_seconds},
            )

        # Quality alert
        if metrics.quality_score < 0.7:
            self._create_alert(
                severity="warning",
                category="quality",
                message=f"Low quality score: {metrics.quality_score:.2f}",
                details={"threshold": 0.7, "actual": metrics.quality_score},
            )

    def _create_alert(
        self, severity: str, category: str, message: str, details: Dict[str, Any]
    ) -> None:
        """Create and log alert."""
        alert = DeduplicationAlert(
            severity=severity, category=category, message=message, details=details
        )

        self.alerts.append(alert)

        self.logger.warning(
            "Deduplication alert",
            alert_id=alert.id,
            severity=severity,
            category=category,
            message=message,
            details=details,
        )

    def get_current_metrics(self) -> Optional[DeduplicationMetrics]:
        """Get most recent metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(
        self, window: Optional[int] = None
    ) -> Optional[DeduplicationMetrics]:
        """Get averaged metrics over specified window."""
        if not self.metrics_history:
            return None

        window_size = min(window or self.window_size, len(self.metrics_history))
        recent_metrics = list(self.metrics_history)[-window_size:]

        # Calculate averages
        avg_metrics = DeduplicationMetrics(
            total_items_processed=sum(m.total_items_processed for m in recent_metrics)
            // window_size,
            processing_time_seconds=sum(
                m.processing_time_seconds for m in recent_metrics
            )
            / window_size,
            items_per_second=sum(m.items_per_second for m in recent_metrics)
            / window_size,
            exact_duplicates_found=sum(m.exact_duplicates_found for m in recent_metrics)
            // window_size,
            semantic_duplicates_found=sum(
                m.semantic_duplicates_found for m in recent_metrics
            )
            // window_size,
            quality_score=sum(m.quality_score for m in recent_metrics) / window_size,
        )

        return avg_metrics

    def get_active_alerts(self) -> List[DeduplicationAlert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self.alerts if not alert.resolved]


class DeduplicationDashboard:
    """Dashboard for monitoring deduplication system health and performance."""

    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.quality_analyzer = QualityAnalyzer()
        self.logger = logger.bind(component="dedup_dashboard")

    async def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        try:
            current_metrics = self.performance_monitor.get_current_metrics()
            average_metrics = self.performance_monitor.get_average_metrics()
            active_alerts = self.performance_monitor.get_active_alerts()

            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_status": "healthy" if not active_alerts else "warning",
                "current_metrics": current_metrics.__dict__
                if current_metrics
                else None,
                "average_metrics": average_metrics.__dict__
                if average_metrics
                else None,
                "active_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity,
                        "category": alert.category,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in active_alerts
                ],
                "alert_summary": self._summarize_alerts(active_alerts),
            }

            return report

        except Exception as e:
            self.logger.error("Failed to generate status report", error=str(e))
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system_status": "error",
                "error": str(e),
            }

    def _summarize_alerts(self, alerts: List[DeduplicationAlert]) -> Dict[str, int]:
        """Summarize alerts by severity and category."""
        summary = defaultdict(int)

        for alert in alerts:
            summary[f"severity_{alert.severity}"] += 1
            summary[f"category_{alert.category}"] += 1

        return dict(summary)


# Factory functions for common monitoring setups
def create_production_monitor() -> PerformanceMonitor:
    """Create performance monitor with production settings."""
    return PerformanceMonitor(window_size=500)


def create_development_monitor() -> PerformanceMonitor:
    """Create performance monitor with development settings."""
    return PerformanceMonitor(window_size=50)


def create_dashboard() -> DeduplicationDashboard:
    """Create comprehensive monitoring dashboard."""
    return DeduplicationDashboard()
