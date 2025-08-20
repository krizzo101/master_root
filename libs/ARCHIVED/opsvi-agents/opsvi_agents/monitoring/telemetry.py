"""Performance telemetry and tracking."""

import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data."""

    operation: str
    duration: float
    timestamp: str
    success: bool
    metadata: Dict[str, Any] = None


class TelemetryTracker:
    """Track agent performance metrics."""

    def __init__(self, metrics_path: str = ".proj-intel/performance_metrics.json"):
        """Initialize telemetry tracker."""
        self.metrics_path = Path(metrics_path)
        self.current_metrics: List[PerformanceMetric] = []
        self.aggregated: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "min_duration": float("inf"),
                "max_duration": 0,
            }
        )
        self._logger = logger.bind(component="TelemetryTracker")
        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load historical metrics."""
        if self.metrics_path.exists():
            try:
                with open(self.metrics_path, "r") as f:
                    data = json.load(f)
                    self.aggregated = defaultdict(
                        lambda: {
                            "count": 0,
                            "total_duration": 0,
                            "success_count": 0,
                            "min_duration": float("inf"),
                            "max_duration": 0,
                        },
                        data.get("aggregated", {}),
                    )
                self._logger.info(
                    f"Loaded metrics for {len(self.aggregated)} operations"
                )
            except Exception as e:
                self._logger.error(f"Failed to load metrics: {e}")

    def _save_metrics(self) -> None:
        """Save metrics to disk."""
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "aggregated": dict(self.aggregated),
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.metrics_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save metrics: {e}")

    def record(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            timestamp=datetime.now().isoformat(),
            success=success,
            metadata=metadata,
        )

        self.current_metrics.append(metric)

        # Update aggregated metrics
        agg = self.aggregated[operation]
        agg["count"] += 1
        agg["total_duration"] += duration
        if success:
            agg["success_count"] += 1
        agg["min_duration"] = min(agg["min_duration"], duration)
        agg["max_duration"] = max(agg["max_duration"], duration)

        # Save periodically
        if len(self.current_metrics) % 10 == 0:
            self._save_metrics()

    def get_statistics(self, operation: str = None) -> Dict[str, Any]:
        """Get performance statistics."""
        if operation:
            agg = self.aggregated.get(operation)
            if not agg:
                return {}

            avg_duration = (
                agg["total_duration"] / agg["count"] if agg["count"] > 0 else 0
            )
            success_rate = (
                agg["success_count"] / agg["count"] if agg["count"] > 0 else 0
            )

            return {
                "operation": operation,
                "count": agg["count"],
                "avg_duration": avg_duration,
                "min_duration": agg["min_duration"],
                "max_duration": agg["max_duration"],
                "success_rate": success_rate,
            }
        else:
            # Global statistics
            total_operations = len(self.aggregated)
            total_count = sum(a["count"] for a in self.aggregated.values())
            total_duration = sum(a["total_duration"] for a in self.aggregated.values())

            return {
                "total_operations": total_operations,
                "total_count": total_count,
                "total_duration": total_duration,
                "avg_duration": total_duration / total_count if total_count > 0 else 0,
            }

    def identify_bottlenecks(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """Identify slow operations."""
        bottlenecks = []

        for operation, agg in self.aggregated.items():
            if agg["count"] == 0:
                continue

            avg_duration = agg["total_duration"] / agg["count"]
            if avg_duration > threshold:
                bottlenecks.append(
                    {
                        "operation": operation,
                        "avg_duration": avg_duration,
                        "count": agg["count"],
                        "impact": avg_duration * agg["count"],
                    }
                )

        # Sort by impact
        bottlenecks.sort(key=lambda x: x["impact"], reverse=True)
        return bottlenecks

    def clear(self) -> None:
        """Clear all metrics."""
        self.current_metrics.clear()
        self.aggregated.clear()
        self._logger.info("Metrics cleared")


class Timer:
    """Context manager for timing operations."""

    def __init__(self, tracker: TelemetryTracker, operation: str):
        """Initialize timer."""
        self.tracker = tracker
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        duration = time.time() - self.start_time
        success = exc_type is None
        self.tracker.record(self.operation, duration, success)


# Global tracker instance
tracker = TelemetryTracker()
