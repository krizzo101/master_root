"""Advanced performance monitoring system for chat import optimization."""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import psutil
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance snapshot."""

    timestamp: datetime
    items_processed: int
    items_per_second: float
    memory_usage_mb: float
    cpu_utilization_pct: float
    database_connections_active: int
    database_connections_idle: int
    cache_hit_rate_pct: float
    error_rate_pct: float
    queue_size: int
    embedding_generation_rate: float
    batch_processing_efficiency: float


@dataclass
class ThroughputMetrics:
    """Throughput-related performance metrics."""

    current_items_per_second: float
    peak_items_per_second: float
    average_items_per_second: float
    total_items_processed: int
    processing_start_time: datetime
    elapsed_time_seconds: float
    projected_completion_time: Optional[datetime]
    efficiency_rating: str  # excellent, good, fair, poor


@dataclass
class ResourceUtilization:
    """System resource utilization metrics."""

    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    database_connections: int
    max_database_connections: int
    connection_pool_efficiency: float


@dataclass
class QualityMetrics:
    """Data quality and processing accuracy metrics."""

    total_items: int
    successful_items: int
    failed_items: int
    success_rate_pct: float
    embedding_success_rate_pct: float
    entity_extraction_success_rate_pct: float
    relationship_detection_success_rate_pct: float
    cache_hit_rate_pct: float
    data_integrity_score: float


class RealTimeMetricsCollector:
    """Real-time metrics collection and analysis system."""

    def __init__(self, collection_interval: float = 5.0, history_size: int = 1000):
        """Initialize metrics collector."""
        self.collection_interval = collection_interval
        self.history_size = history_size

        # Metric storage
        self.performance_history = deque(maxlen=history_size)
        self.throughput_history = deque(maxlen=history_size)
        self.resource_history = deque(maxlen=history_size)
        self.quality_history = deque(maxlen=history_size)

        # Processing state
        self.start_time = datetime.utcnow()
        self.total_items_processed = 0
        self.total_items_failed = 0
        self.peak_throughput = 0.0

        # Component references for metrics collection
        self.database_pool = None
        self.cache_manager = None
        self.batch_processor = None

        # Collection task
        self.collection_task = None
        self.is_collecting = False

    def register_components(
        self,
        database_pool: Any = None,
        cache_manager: Any = None,
        batch_processor: Any = None,
    ):
        """Register system components for metrics collection."""
        self.database_pool = database_pool
        self.cache_manager = cache_manager
        self.batch_processor = batch_processor

    async def start_collection(self):
        """Start real-time metrics collection."""
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info(
            "Performance metrics collection started", interval=self.collection_interval
        )

    async def stop_collection(self):
        """Stop metrics collection."""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance metrics collection stopped")

    async def _collection_loop(self):
        """Main metrics collection loop."""
        while self.is_collecting:
            try:
                await self._collect_current_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metrics collection failed", error=str(e))
                await asyncio.sleep(self.collection_interval)

    async def _collect_current_metrics(self):
        """Collect current system metrics."""
        timestamp = datetime.utcnow()

        # Collect performance snapshot
        performance_snapshot = await self._collect_performance_snapshot(timestamp)
        self.performance_history.append(performance_snapshot)

        # Collect throughput metrics
        throughput_metrics = self._calculate_throughput_metrics()
        self.throughput_history.append(throughput_metrics)

        # Collect resource utilization
        resource_metrics = self._collect_resource_utilization()
        self.resource_history.append(resource_metrics)

        # Collect quality metrics
        quality_metrics = self._calculate_quality_metrics()
        self.quality_history.append(quality_metrics)

    async def _collect_performance_snapshot(
        self, timestamp: datetime
    ) -> PerformanceSnapshot:
        """Collect a comprehensive performance snapshot."""

        # Calculate current throughput
        recent_snapshots = list(self.performance_history)[-10:]  # Last 10 snapshots
        if len(recent_snapshots) >= 2:
            time_diff = (timestamp - recent_snapshots[0].timestamp).total_seconds()
            items_diff = (
                self.total_items_processed - recent_snapshots[0].items_processed
            )
            current_throughput = items_diff / max(0.1, time_diff)
        else:
            current_throughput = 0.0

        # System resources
        memory_info = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()

        # Database connection info
        db_active, db_idle = 0, 0
        if self.database_pool:
            try:
                if hasattr(self.database_pool, "pool") and self.database_pool.pool:
                    db_active = (
                        self.database_pool.pool.get_size()
                        - self.database_pool.pool.get_idle_size()
                    )
                    db_idle = self.database_pool.pool.get_idle_size()
            except:
                pass

        # Cache performance
        cache_hit_rate = 0.0
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_comprehensive_stats()
                embedding_cache = cache_stats.get("embedding_cache", {})
                cache_hit_rate = embedding_cache.get("memory_hit_rate_pct", 0.0)
            except:
                pass

        # Error rate
        error_rate = (
            self.total_items_failed
            / max(1, self.total_items_processed + self.total_items_failed)
        ) * 100

        # Batch processing efficiency
        batch_efficiency = 0.0
        if self.batch_processor:
            try:
                batch_stats = self.batch_processor.get_comprehensive_stats()
                batch_efficiency = 100 - batch_stats.get("error_rate_pct", 0.0)
            except:
                pass

        return PerformanceSnapshot(
            timestamp=timestamp,
            items_processed=self.total_items_processed,
            items_per_second=current_throughput,
            memory_usage_mb=memory_info.used / 1024 / 1024,
            cpu_utilization_pct=cpu_percent,
            database_connections_active=db_active,
            database_connections_idle=db_idle,
            cache_hit_rate_pct=cache_hit_rate,
            error_rate_pct=error_rate,
            queue_size=0,  # Would need to be passed from processing system
            embedding_generation_rate=0.0,  # Would calculate from embedding processor
            batch_processing_efficiency=batch_efficiency,
        )

    def _calculate_throughput_metrics(self) -> ThroughputMetrics:
        """Calculate comprehensive throughput metrics."""
        now = datetime.utcnow()
        elapsed_seconds = (now - self.start_time).total_seconds()

        # Current and average throughput
        if elapsed_seconds > 0:
            average_throughput = self.total_items_processed / elapsed_seconds
        else:
            average_throughput = 0.0

        # Peak throughput from history
        recent_snapshots = list(self.performance_history)[-20:]
        if recent_snapshots:
            current_throughput = recent_snapshots[-1].items_per_second
            peak_throughput = max(
                snapshot.items_per_second for snapshot in recent_snapshots
            )
            self.peak_throughput = max(self.peak_throughput, peak_throughput)
        else:
            current_throughput = 0.0
            peak_throughput = 0.0

        # Projected completion (if we have a target)
        projected_completion = None  # Would need target items count

        # Efficiency rating
        if average_throughput >= self.peak_throughput * 0.8:
            efficiency = "excellent"
        elif average_throughput >= self.peak_throughput * 0.6:
            efficiency = "good"
        elif average_throughput >= self.peak_throughput * 0.4:
            efficiency = "fair"
        else:
            efficiency = "poor"

        return ThroughputMetrics(
            current_items_per_second=current_throughput,
            peak_items_per_second=self.peak_throughput,
            average_items_per_second=average_throughput,
            total_items_processed=self.total_items_processed,
            processing_start_time=self.start_time,
            elapsed_time_seconds=elapsed_seconds,
            projected_completion_time=projected_completion,
            efficiency_rating=efficiency,
        )

    def _collect_resource_utilization(self) -> ResourceUtilization:
        """Collect current resource utilization metrics."""
        # System resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / 1024 / 1024 if disk_io else 0
        disk_write_mb = disk_io.write_bytes / 1024 / 1024 if disk_io else 0

        # Network I/O
        network_io = psutil.net_io_counters()
        network_sent_mb = network_io.bytes_sent / 1024 / 1024 if network_io else 0
        network_recv_mb = network_io.bytes_recv / 1024 / 1024 if network_io else 0

        # Database connections
        db_connections = 0
        max_db_connections = 0
        connection_efficiency = 0.0

        if (
            self.database_pool
            and hasattr(self.database_pool, "pool")
            and self.database_pool.pool
        ):
            try:
                db_connections = self.database_pool.pool.get_size()
                max_db_connections = self.database_pool.max_connections
                active_connections = (
                    db_connections - self.database_pool.pool.get_idle_size()
                )
                connection_efficiency = (
                    active_connections / max(1, db_connections)
                ) * 100
            except:
                pass

        return ResourceUtilization(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_io_sent_mb=network_sent_mb,
            network_io_recv_mb=network_recv_mb,
            database_connections=db_connections,
            max_database_connections=max_db_connections,
            connection_pool_efficiency=connection_efficiency,
        )

    def _calculate_quality_metrics(self) -> QualityMetrics:
        """Calculate data quality and processing accuracy metrics."""
        total_items = self.total_items_processed + self.total_items_failed
        success_rate = (self.total_items_processed / max(1, total_items)) * 100

        # Component-specific success rates (would be calculated from actual components)
        embedding_success_rate = 95.0  # Placeholder
        entity_success_rate = 98.0  # Placeholder
        relationship_success_rate = 92.0  # Placeholder

        # Cache performance
        cache_hit_rate = 0.0
        if self.cache_manager:
            try:
                stats = self.cache_manager.get_comprehensive_stats()
                embedding_cache = stats.get("embedding_cache", {})
                cache_hit_rate = embedding_cache.get("memory_hit_rate_pct", 0.0)
            except:
                pass

        # Overall data integrity score (weighted average)
        data_integrity = (
            success_rate * 0.4
            + embedding_success_rate * 0.2
            + entity_success_rate * 0.2
            + relationship_success_rate * 0.2
        )

        return QualityMetrics(
            total_items=total_items,
            successful_items=self.total_items_processed,
            failed_items=self.total_items_failed,
            success_rate_pct=success_rate,
            embedding_success_rate_pct=embedding_success_rate,
            entity_extraction_success_rate_pct=entity_success_rate,
            relationship_detection_success_rate_pct=relationship_success_rate,
            cache_hit_rate_pct=cache_hit_rate,
            data_integrity_score=data_integrity,
        )

    # Public interface methods

    def update_processing_stats(self, items_processed: int, items_failed: int = 0):
        """Update processing statistics."""
        self.total_items_processed += items_processed
        self.total_items_failed += items_failed

    def get_current_performance(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.performance_history:
            return {"status": "no_data"}

        latest_snapshot = self.performance_history[-1]
        latest_throughput = (
            self.throughput_history[-1] if self.throughput_history else None
        )
        latest_resources = self.resource_history[-1] if self.resource_history else None
        latest_quality = self.quality_history[-1] if self.quality_history else None

        return {
            "performance": asdict(latest_snapshot) if latest_snapshot else None,
            "throughput": asdict(latest_throughput) if latest_throughput else None,
            "resources": asdict(latest_resources) if latest_resources else None,
            "quality": asdict(latest_quality) if latest_quality else None,
        }

    def get_performance_trends(self, window_minutes: int = 30) -> Dict[str, Any]:
        """Get performance trends over specified time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Filter data to time window
        recent_performance = [
            s for s in self.performance_history if s.timestamp >= cutoff_time
        ]
        recent_throughput = [
            s for s in self.throughput_history if s.processing_start_time >= cutoff_time
        ]

        if not recent_performance:
            return {"status": "insufficient_data"}

        # Calculate trends
        throughput_trend = self._calculate_trend(
            [s.items_per_second for s in recent_performance]
        )
        memory_trend = self._calculate_trend(
            [s.memory_usage_mb for s in recent_performance]
        )
        cpu_trend = self._calculate_trend(
            [s.cpu_utilization_pct for s in recent_performance]
        )
        error_trend = self._calculate_trend(
            [s.error_rate_pct for s in recent_performance]
        )

        return {
            "window_minutes": window_minutes,
            "data_points": len(recent_performance),
            "trends": {
                "throughput": throughput_trend,
                "memory_usage": memory_trend,
                "cpu_utilization": cpu_trend,
                "error_rate": error_trend,
            },
            "current_vs_peak": {
                "throughput_pct": (
                    recent_performance[-1].items_per_second
                    / max(0.1, self.peak_throughput)
                )
                * 100,
                "efficiency_rating": recent_throughput[-1].efficiency_rating
                if recent_throughput
                else "unknown",
            },
        }

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and magnitude for a series of values."""
        if len(values) < 2:
            return {"direction": "stable", "magnitude": 0.0}

        # Simple linear trend calculation
        x_values = list(range(len(values)))
        y_values = values

        n = len(values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        # Linear regression slope
        slope = (n * sum_xy - sum_x * sum_y) / max(0.001, n * sum_x2 - sum_x * sum_x)

        # Determine trend direction and magnitude
        if abs(slope) < 0.1:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Magnitude as percentage change per data point
        avg_value = sum_y / n
        magnitude = abs(slope / max(0.001, avg_value)) * 100

        return {
            "direction": direction,
            "magnitude": magnitude,
            "slope": slope,
            "confidence": min(
                100.0, len(values) * 5
            ),  # Simple confidence based on data points
        }

    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on current metrics."""
        alerts = []

        if not self.performance_history or not self.resource_history:
            return alerts

        latest_perf = self.performance_history[-1]
        latest_resource = self.resource_history[-1]
        latest_quality = self.quality_history[-1] if self.quality_history else None

        # Throughput alerts
        if latest_perf.items_per_second < self.peak_throughput * 0.3:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": "Processing throughput significantly below peak performance",
                    "current_value": latest_perf.items_per_second,
                    "threshold": self.peak_throughput * 0.3,
                }
            )

        # Resource alerts
        if latest_resource.cpu_percent > 90:
            alerts.append(
                {
                    "type": "resource",
                    "severity": "critical",
                    "message": "CPU utilization critically high",
                    "current_value": latest_resource.cpu_percent,
                    "threshold": 90,
                }
            )

        if latest_resource.memory_percent > 85:
            alerts.append(
                {
                    "type": "resource",
                    "severity": "warning",
                    "message": "Memory utilization high",
                    "current_value": latest_resource.memory_percent,
                    "threshold": 85,
                }
            )

        # Quality alerts
        if latest_quality and latest_quality.success_rate_pct < 95:
            alerts.append(
                {
                    "type": "quality",
                    "severity": "warning",
                    "message": "Processing success rate below acceptable threshold",
                    "current_value": latest_quality.success_rate_pct,
                    "threshold": 95,
                }
            )

        # Database connection alerts
        if latest_resource.connection_pool_efficiency < 30:
            alerts.append(
                {
                    "type": "database",
                    "severity": "info",
                    "message": "Database connection pool utilization low",
                    "current_value": latest_resource.connection_pool_efficiency,
                    "threshold": 30,
                }
            )

        return alerts

    async def export_metrics_report(self, file_path: str) -> Dict[str, Any]:
        """Export comprehensive metrics report to file."""
        report = {
            "report_generated": datetime.utcnow().isoformat(),
            "collection_period": {
                "start": self.start_time.isoformat(),
                "end": datetime.utcnow().isoformat(),
                "duration_hours": (datetime.utcnow() - self.start_time).total_seconds()
                / 3600,
            },
            "summary": {
                "total_items_processed": self.total_items_processed,
                "total_items_failed": self.total_items_failed,
                "peak_throughput": self.peak_throughput,
                "data_points_collected": len(self.performance_history),
            },
            "current_performance": self.get_current_performance(),
            "performance_trends": self.get_performance_trends(60),  # Last hour
            "alerts": self.get_performance_alerts(),
            "detailed_history": {
                "performance_snapshots": [
                    asdict(s) for s in list(self.performance_history)
                ],
                "throughput_history": [
                    asdict(s) for s in list(self.throughput_history)
                ],
                "resource_history": [asdict(s) for s in list(self.resource_history)],
                "quality_history": [asdict(s) for s in list(self.quality_history)],
            },
        }

        try:
            with open(file_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            return {
                "status": "success",
                "file_path": file_path,
                "report_size_mb": len(json.dumps(report, default=str)) / 1024 / 1024,
            }
        except Exception as e:
            logger.error("Failed to export metrics report", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
            }


# Global metrics collector instance
performance_monitor = RealTimeMetricsCollector()


async def initialize_performance_monitoring(
    database_pool: Any = None,
    cache_manager: Any = None,
    batch_processor: Any = None,
    collection_interval: float = 5.0,
) -> RealTimeMetricsCollector:
    """Initialize and start performance monitoring."""
    global performance_monitor

    performance_monitor = RealTimeMetricsCollector(
        collection_interval=collection_interval
    )
    performance_monitor.register_components(
        database_pool=database_pool,
        cache_manager=cache_manager,
        batch_processor=batch_processor,
    )

    await performance_monitor.start_collection()
    logger.info("Performance monitoring initialized and started")
    return performance_monitor


def get_performance_monitor() -> RealTimeMetricsCollector:
    """Get the global performance monitor instance."""
    return performance_monitor
