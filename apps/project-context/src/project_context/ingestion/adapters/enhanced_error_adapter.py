"""Enhanced Error Log Ingestion System with Structured Parsing and Correlation Detection.

This adapter provides comprehensive error log ingestion with:
- Multi-format log parser (JSON, text, structured)
- Stack trace extraction and analysis
- Error classification and severity scoring
- Frequency tracking and pattern detection
- Automatic correlation with Git commits and chat conversations
- Real-time processing capabilities
"""

import asyncio
import hashlib
import json
import math
import re
import statistics
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


@dataclass
class ErrorPattern:
    """Represents a detected error pattern."""

    pattern_id: str
    error_signature: str
    frequency: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    file_paths: Set[str] = field(default_factory=set)
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    related_commits: List[str] = field(default_factory=list)
    related_chat_sessions: List[str] = field(default_factory=list)


@dataclass
class StackTraceElement:
    """Represents a single stack trace frame."""

    file_path: str
    function_name: str
    line_number: int
    class_name: Optional[str] = None
    code_context: Optional[str] = None


@dataclass
class ParsedError:
    """Structured representation of a parsed error."""

    error_id: str
    timestamp: datetime
    severity: str
    error_type: str
    message: str
    source: str

    # Location information
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None

    # Stack trace
    stack_trace: Optional[str] = None
    stack_elements: List[StackTraceElement] = field(default_factory=list)

    # Context
    environment: Optional[str] = None
    process_id: Optional[str] = None
    thread_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    # Additional metadata
    tags: Set[str] = field(default_factory=set)
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


class LogFormatDetector:
    """Detects and parses various log formats."""

    def __init__(self):
        self.json_patterns = [
            # Standard JSON log
            r"^\s*\{.*\}\s*$",
            # JSONL format
            r"^\s*\{.*\}(?:\s*\n)*$",
        ]

        self.structured_patterns = [
            # Standard format: timestamp LEVEL [component] message
            r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d{3,6})?(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<level>\w+)\s+(?:\[(?P<component>[^\]]+)\]\s*)?(?P<message>.*)",
            # Syslog format
            r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<process>\S+):\s*(?P<message>.*)",
            # Apache/Nginx error log
            r"\[(?P<timestamp>[^\]]+)\]\s+\[(?P<level>\w+)\]\s+(?P<message>.*)",
            # Java/Spring Boot format
            r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.,]\d{3})\s+(?P<level>\w+)\s+(?P<process>\d+)\s+---\s+\[(?P<thread>[^\]]+)\]\s+(?P<logger>\S+)\s*:\s*(?P<message>.*)",
        ]

    def detect_format(self, line: str) -> str:
        """Detect the format of a log line."""
        line = line.strip()

        # Check for JSON format
        for pattern in self.json_patterns:
            if re.match(pattern, line):
                try:
                    json.loads(line)
                    return "json"
                except (json.JSONDecodeError, ValueError):
                    continue

        # Check for structured formats
        for pattern in self.structured_patterns:
            if re.match(pattern, line):
                return "structured"

        # Default to plain text
        return "plain"


class StackTraceParser:
    """Parses stack traces from various languages and formats."""

    def __init__(self):
        self.parsers = {
            "python": self._parse_python_stack,
            "java": self._parse_java_stack,
            "javascript": self._parse_javascript_stack,
            "csharp": self._parse_csharp_stack,
            "ruby": self._parse_ruby_stack,
            "go": self._parse_go_stack,
        }

        self.language_indicators = {
            r'File\s+"[^"]+",\s+line\s+\d+': "python",
            r"at\s+[\w.]+\([^)]*\)": "java",
            r"at\s+[\w.]+\s+\([^)]*:\d+:\d+\)": "javascript",
            r"at\s+[\w.]+\.[^(]+\([^)]*\)\s+in\s+[^:]+:\d+": "csharp",
            r"from\s+[^:]+:\d+:in\s+": "ruby",
            r"goroutine\s+\d+\s+\[": "go",
        }

    def detect_language(self, stack_trace: str) -> Optional[str]:
        """Detect the programming language from stack trace format."""
        for pattern, language in self.language_indicators.items():
            if re.search(pattern, stack_trace, re.IGNORECASE):
                return language
        return None

    def parse_stack_trace(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse stack trace into structured elements."""
        language = self.detect_language(stack_trace)

        if language and language in self.parsers:
            return self.parsers[language](stack_trace)
        else:
            return self._parse_generic_stack(stack_trace)

    def _parse_python_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse Python stack traces."""
        elements = []
        pattern = r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+([^\n]+)(?:\n\s+(.+))?'

        for match in re.finditer(pattern, stack_trace):
            elements.append(
                StackTraceElement(
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    function_name=match.group(3).strip(),
                    code_context=match.group(4).strip() if match.group(4) else None,
                )
            )

        return elements

    def _parse_java_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse Java stack traces."""
        elements = []
        pattern = r"at\s+((?:[\w.]+\.)?(\w+))\.(\w+)\(([^)]*)\)"

        for match in re.finditer(pattern, stack_trace):
            file_info = match.group(4)
            line_number = None

            if ":" in file_info:
                parts = file_info.split(":")
                if len(parts) == 2 and parts[1].isdigit():
                    line_number = int(parts[1])
                    file_info = parts[0]

            elements.append(
                StackTraceElement(
                    file_path=file_info,
                    class_name=match.group(2),
                    function_name=match.group(3),
                    line_number=line_number or 0,
                )
            )

        return elements

    def _parse_javascript_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse JavaScript stack traces."""
        elements = []
        pattern = r"at\s+(?:(\w+)\s+)?\(?([^)]+):(\d+):(\d+)\)?"

        for match in re.finditer(pattern, stack_trace):
            elements.append(
                StackTraceElement(
                    file_path=match.group(2),
                    function_name=match.group(1) or "<anonymous>",
                    line_number=int(match.group(3)),
                )
            )

        return elements

    def _parse_csharp_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse C# stack traces."""
        elements = []
        pattern = r"at\s+([\w.]+)\.(\w+)\([^)]*\)\s+in\s+([^:]+):line\s+(\d+)"

        for match in re.finditer(pattern, stack_trace):
            elements.append(
                StackTraceElement(
                    file_path=match.group(3),
                    class_name=match.group(1).split(".")[-2]
                    if "." in match.group(1)
                    else None,
                    function_name=match.group(2),
                    line_number=int(match.group(4)),
                )
            )

        return elements

    def _parse_ruby_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse Ruby stack traces."""
        elements = []
        pattern = r"([^:]+):(\d+):in\s+`([^\']+)\'|([^:]+):(\d+)"

        for match in re.finditer(pattern, stack_trace):
            if match.group(1):  # Full format with method
                elements.append(
                    StackTraceElement(
                        file_path=match.group(1),
                        line_number=int(match.group(2)),
                        function_name=match.group(3),
                    )
                )
            else:  # Simple format
                elements.append(
                    StackTraceElement(
                        file_path=match.group(4),
                        line_number=int(match.group(5)),
                        function_name="<unknown>",
                    )
                )

        return elements

    def _parse_go_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse Go stack traces."""
        elements = []
        lines = stack_trace.split("\n")

        i = 0
        while i < len(lines) - 1:
            line = lines[i].strip()
            if re.match(r"[\w.]+\(", line):  # Function call line
                function_match = re.match(r"([\w./]+)\.([\w]+)", line)
                if function_match and i + 1 < len(lines):
                    location_line = lines[i + 1].strip()
                    location_match = re.match(r"([^:]+):(\d+)", location_line)

                    if location_match:
                        elements.append(
                            StackTraceElement(
                                file_path=location_match.group(1),
                                function_name=function_match.group(2),
                                line_number=int(location_match.group(2)),
                            )
                        )
                        i += 2
                        continue
            i += 1

        return elements

    def _parse_generic_stack(self, stack_trace: str) -> List[StackTraceElement]:
        """Parse generic stack traces when language is unknown."""
        elements = []

        # Try to extract file paths and line numbers
        pattern = r"([^\s:]+\.[\w]+):(\d+)"
        for match in re.finditer(pattern, stack_trace):
            elements.append(
                StackTraceElement(
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    function_name="<unknown>",
                )
            )

        return elements


class TrendAnalyzer:
    """Analyzes error trends and patterns for predictive insights."""

    def __init__(self, time_window_hours: int = 24):
        self.time_window = timedelta(hours=time_window_hours)
        self.pattern_cache: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)
        self.trend_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)

    def update_pattern_frequency(
        self, pattern_id: str, timestamp: datetime, count: int = 1
    ) -> None:
        """Update frequency data for a pattern."""
        # Clean old entries outside time window
        cutoff_time = timestamp - self.time_window
        self.pattern_cache[pattern_id] = [
            (ts, cnt) for ts, cnt in self.pattern_cache[pattern_id] if ts > cutoff_time
        ]

        # Add new entry
        self.pattern_cache[pattern_id].append((timestamp, count))

        # Update trend metrics
        self._calculate_trend_metrics(pattern_id, timestamp)

    def _calculate_trend_metrics(self, pattern_id: str, current_time: datetime) -> None:
        """Calculate trend metrics for a pattern."""
        data_points = self.pattern_cache[pattern_id]
        if len(data_points) < 2:
            return

        # Calculate frequency trend (errors per hour)
        time_buckets = defaultdict(int)
        for timestamp, count in data_points:
            hour_bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            time_buckets[hour_bucket] += count

        if len(time_buckets) < 2:
            return

        # Calculate trend slope (linear regression)
        x_values = [
            (ts - current_time).total_seconds() / 3600 for ts in time_buckets.keys()
        ]
        y_values = list(time_buckets.values())

        if len(x_values) >= 2:
            # Simple linear regression
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)

            denominator = n * sum_x2 - sum_x * sum_x
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator

                self.trend_metrics[pattern_id].update(
                    {
                        "slope": slope,
                        "frequency_per_hour": sum_y / len(time_buckets),
                        "total_occurrences": sum_y,
                        "time_span_hours": max(x_values) - min(x_values),
                        "trend_direction": "increasing"
                        if slope > 0.1
                        else "decreasing"
                        if slope < -0.1
                        else "stable",
                        "severity_score": min(
                            1.0, abs(slope) * sum_y / 10.0
                        ),  # Normalized severity
                    }
                )

    def get_trending_patterns(
        self, min_frequency: int = 3, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get patterns that are trending upward."""
        trending = []

        for pattern_id, metrics in self.trend_metrics.items():
            if (
                metrics.get("total_occurrences", 0) >= min_frequency
                and metrics.get("trend_direction") == "increasing"
            ):
                trending.append(
                    {
                        "pattern_id": pattern_id,
                        "slope": metrics["slope"],
                        "frequency_per_hour": metrics["frequency_per_hour"],
                        "total_occurrences": metrics["total_occurrences"],
                        "severity_score": metrics["severity_score"],
                        "trend_direction": metrics["trend_direction"],
                    }
                )

        # Sort by severity score descending
        trending.sort(key=lambda x: x["severity_score"], reverse=True)
        return trending[:limit]

    def predict_future_occurrences(
        self, pattern_id: str, hours_ahead: int = 1
    ) -> float:
        """Predict future occurrences based on current trend."""
        metrics = self.trend_metrics.get(pattern_id, {})
        if not metrics or "slope" not in metrics:
            return 0.0

        current_rate = metrics.get("frequency_per_hour", 0)
        slope = metrics["slope"]

        # Simple linear prediction
        predicted_rate = max(0, current_rate + (slope * hours_ahead))
        return predicted_rate * hours_ahead


class ErrorDeduplicator:
    """Handles error deduplication and clustering."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.error_clusters: Dict[str, List[str]] = {}  # cluster_id -> error_ids
        self.error_to_cluster: Dict[str, str] = {}  # error_id -> cluster_id
        self.cluster_representatives: Dict[
            str, Dict[str, Any]
        ] = {}  # cluster_id -> representative error

    def find_or_create_cluster(self, parsed_error: ParsedError) -> str:
        """Find existing cluster or create new one for the error."""
        error_signature = self._create_error_signature(parsed_error)

        # Check existing clusters for similarity
        best_cluster = None
        best_similarity = 0.0

        for cluster_id, representative in self.cluster_representatives.items():
            similarity = self._calculate_signature_similarity(
                error_signature, representative["signature"]
            )
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_cluster = cluster_id

        if best_cluster:
            # Add to existing cluster
            self.error_clusters[best_cluster].append(parsed_error.error_id)
            self.error_to_cluster[parsed_error.error_id] = best_cluster

            # Update cluster representative if this error is more recent
            if (
                parsed_error.timestamp
                > self.cluster_representatives[best_cluster]["timestamp"]
            ):
                self.cluster_representatives[best_cluster] = {
                    "signature": error_signature,
                    "timestamp": parsed_error.timestamp,
                    "error_id": parsed_error.error_id,
                    "representative_error": parsed_error,
                }

            return best_cluster
        else:
            # Create new cluster
            cluster_id = (
                f"cluster_{hashlib.md5(error_signature.encode()).hexdigest()[:12]}"
            )
            self.error_clusters[cluster_id] = [parsed_error.error_id]
            self.error_to_cluster[parsed_error.error_id] = cluster_id
            self.cluster_representatives[cluster_id] = {
                "signature": error_signature,
                "timestamp": parsed_error.timestamp,
                "error_id": parsed_error.error_id,
                "representative_error": parsed_error,
            }

            return cluster_id

    def _create_error_signature(self, parsed_error: ParsedError) -> str:
        """Create a signature for error matching."""
        parts = [
            parsed_error.error_type,
            # Normalize file path (remove line numbers and absolute paths)
            self._normalize_file_path(parsed_error.file_path)
            if parsed_error.file_path
            else "",
            # Extract key words from message (remove specific values)
            self._normalize_error_message(parsed_error.message),
            parsed_error.function_name or "",
        ]
        return "|".join(parts).lower()

    def _normalize_file_path(self, file_path: str) -> str:
        """Normalize file path for clustering."""
        # Convert to relative path and remove line-specific info
        path = Path(file_path)
        return str(path.name)  # Just use filename for clustering

    def _normalize_error_message(self, message: str) -> str:
        """Normalize error message by removing specific values."""
        # Remove specific numbers, IDs, timestamps, etc.
        normalized = re.sub(r"\b\d+\b", "<NUM>", message)
        normalized = re.sub(
            r"\b[a-f0-9]{8,}\b", "<ID>", normalized, flags=re.IGNORECASE
        )
        normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}", "<DATE>", normalized)
        normalized = re.sub(r"\b\d{2}:\d{2}:\d{2}", "<TIME>", normalized)

        # Extract first meaningful sentence
        sentences = normalized.split(". ")
        return sentences[0][:100] if sentences else normalized[:100]

    def _calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two error signatures."""
        parts1 = sig1.split("|")
        parts2 = sig2.split("|")

        if len(parts1) != len(parts2):
            return 0.0

        similarities = []
        for p1, p2 in zip(parts1, parts2):
            if not p1 and not p2:
                similarities.append(1.0)
            elif not p1 or not p2:
                similarities.append(0.0)
            elif p1 == p2:
                similarities.append(1.0)
            else:
                # Simple word-based similarity
                words1 = set(p1.split())
                words2 = set(p2.split())
                if words1 or words2:
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    similarities.append(intersection / union if union > 0 else 0.0)
                else:
                    similarities.append(0.0)

        return sum(similarities) / len(similarities)

    def get_cluster_info(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a cluster."""
        if cluster_id not in self.error_clusters:
            return None

        representative = self.cluster_representatives[cluster_id]
        return {
            "cluster_id": cluster_id,
            "error_count": len(self.error_clusters[cluster_id]),
            "error_ids": self.error_clusters[cluster_id],
            "representative_error_id": representative["error_id"],
            "latest_occurrence": representative["timestamp"],
            "signature": representative["signature"],
        }

    def get_all_clusters(self) -> List[Dict[str, Any]]:
        """Get information about all clusters."""
        clusters = []
        for cluster_id in self.error_clusters.keys():
            cluster_info = self.get_cluster_info(cluster_id)
            if cluster_info:
                clusters.append(cluster_info)

        # Sort by error count descending
        clusters.sort(key=lambda x: x["error_count"], reverse=True)
        return clusters


class PerformanceMonitor:
    """Monitors performance of error processing and raises alerts."""

    def __init__(self):
        self.metrics = {
            "processing_times": [],
            "errors_per_minute": defaultdict(int),
            "memory_usage_mb": [],
            "parsing_failures": 0,
            "correlation_failures": 0,
            "total_processed": 0,
        }
        self.alert_thresholds = {
            "max_processing_time_ms": 5000,  # 5 seconds
            "max_errors_per_minute": 100,
            "max_memory_usage_mb": 500,
            "max_parsing_failure_rate": 0.1,  # 10%
            "max_correlation_failure_rate": 0.05,  # 5%
        }
        self.alerts_raised = []

    def record_processing_time(self, processing_time_ms: float) -> None:
        """Record processing time for an error."""
        self.metrics["processing_times"].append(processing_time_ms)

        # Keep only recent measurements (last 1000)
        if len(self.metrics["processing_times"]) > 1000:
            self.metrics["processing_times"] = self.metrics["processing_times"][-1000:]

        # Check alert threshold
        if processing_time_ms > self.alert_thresholds["max_processing_time_ms"]:
            self._raise_alert(
                "high_processing_time",
                f'Processing time {processing_time_ms}ms exceeds threshold {self.alert_thresholds["max_processing_time_ms"]}ms',
            )

    def record_error_count(self, timestamp: datetime, count: int = 1) -> None:
        """Record error count for rate monitoring."""
        minute_bucket = timestamp.replace(second=0, microsecond=0)
        self.metrics["errors_per_minute"][minute_bucket] += count
        self.metrics["total_processed"] += count

        # Clean old buckets (keep last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        old_buckets = [
            bucket
            for bucket in self.metrics["errors_per_minute"].keys()
            if bucket < cutoff_time
        ]
        for bucket in old_buckets:
            del self.metrics["errors_per_minute"][bucket]

        # Check rate alert
        current_rate = sum(self.metrics["errors_per_minute"].values())
        if current_rate > self.alert_thresholds["max_errors_per_minute"]:
            self._raise_alert(
                "high_error_rate",
                f'Error rate {current_rate}/min exceeds threshold {self.alert_thresholds["max_errors_per_minute"]}/min',
            )

    def record_memory_usage(self, memory_mb: float) -> None:
        """Record memory usage."""
        self.metrics["memory_usage_mb"].append(memory_mb)

        # Keep only recent measurements
        if len(self.metrics["memory_usage_mb"]) > 100:
            self.metrics["memory_usage_mb"] = self.metrics["memory_usage_mb"][-100:]

        if memory_mb > self.alert_thresholds["max_memory_usage_mb"]:
            self._raise_alert(
                "high_memory_usage",
                f'Memory usage {memory_mb}MB exceeds threshold {self.alert_thresholds["max_memory_usage_mb"]}MB',
            )

    def record_parsing_failure(self) -> None:
        """Record parsing failure."""
        self.metrics["parsing_failures"] += 1

        # Check failure rate
        if self.metrics["total_processed"] > 0:
            failure_rate = (
                self.metrics["parsing_failures"] / self.metrics["total_processed"]
            )
            if failure_rate > self.alert_thresholds["max_parsing_failure_rate"]:
                self._raise_alert(
                    "high_parsing_failure_rate",
                    f'Parsing failure rate {failure_rate:.2%} exceeds threshold {self.alert_thresholds["max_parsing_failure_rate"]:.2%}',
                )

    def record_correlation_failure(self) -> None:
        """Record correlation failure."""
        self.metrics["correlation_failures"] += 1

        # Check failure rate
        if self.metrics["total_processed"] > 0:
            failure_rate = (
                self.metrics["correlation_failures"] / self.metrics["total_processed"]
            )
            if failure_rate > self.alert_thresholds["max_correlation_failure_rate"]:
                self._raise_alert(
                    "high_correlation_failure_rate",
                    f'Correlation failure rate {failure_rate:.2%} exceeds threshold {self.alert_thresholds["max_correlation_failure_rate"]:.2%}',
                )

    def _raise_alert(self, alert_type: str, message: str) -> None:
        """Raise an alert."""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(),
            "severity": "warning" if "high_" in alert_type else "info",
        }

        self.alerts_raised.append(alert)

        # Keep only recent alerts (last 100)
        if len(self.alerts_raised) > 100:
            self.alerts_raised = self.alerts_raised[-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        stats = {
            "total_processed": self.metrics["total_processed"],
            "parsing_failures": self.metrics["parsing_failures"],
            "correlation_failures": self.metrics["correlation_failures"],
            "recent_alerts_count": len(
                [
                    a
                    for a in self.alerts_raised
                    if a["timestamp"] > datetime.now() - timedelta(minutes=15)
                ]
            ),
            "total_alerts": len(self.alerts_raised),
        }

        if self.metrics["processing_times"]:
            stats.update(
                {
                    "avg_processing_time_ms": statistics.mean(
                        self.metrics["processing_times"]
                    ),
                    "p95_processing_time_ms": statistics.quantiles(
                        self.metrics["processing_times"], n=20
                    )[18]
                    if len(self.metrics["processing_times"]) >= 20
                    else max(self.metrics["processing_times"]),
                    "max_processing_time_ms": max(self.metrics["processing_times"]),
                }
            )

        if self.metrics["memory_usage_mb"]:
            stats.update(
                {
                    "current_memory_mb": self.metrics["memory_usage_mb"][-1],
                    "avg_memory_mb": statistics.mean(self.metrics["memory_usage_mb"]),
                    "peak_memory_mb": max(self.metrics["memory_usage_mb"]),
                }
            )

        if self.metrics["errors_per_minute"]:
            stats["current_error_rate_per_minute"] = sum(
                self.metrics["errors_per_minute"].values()
            )

        return stats

    def get_recent_alerts(self, minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            alert for alert in self.alerts_raised if alert["timestamp"] > cutoff_time
        ]


class ErrorClassifier:
    """Classifies errors based on content, patterns, and context."""

    def __init__(self):
        self.classification_rules = {
            "network": {
                "patterns": [
                    r"connection.*(?:refused|timeout|reset|failed)",
                    r"(?:dns|host).*(?:not found|unreachable)",
                    r"socket.*(?:error|timeout|closed)",
                    r"http.*(?:error|timeout|\d{4,5})",
                    r"ssl.*(?:error|handshake|certificate)",
                ],
                "severity_boost": 0.1,
            },
            "database": {
                "patterns": [
                    r"(?:sql|database|db).*(?:error|exception|timeout|deadlock)",
                    r"connection.*(?:pool|database|sql)",
                    r"(?:mysql|postgresql|sqlite|oracle|sql server).*error",
                    r"(?:table|column|index).*(?:not found|missing|duplicate)",
                    r"(?:foreign key|constraint).*(?:violation|error)",
                ],
                "severity_boost": 0.2,
            },
            "memory": {
                "patterns": [
                    r"(?:out of|insufficient).*memory",
                    r"memory.*(?:leak|error|allocation)",
                    r"heap.*(?:overflow|error|full)",
                    r"stack.*overflow",
                    r"gc.*(?:error|pressure)",
                ],
                "severity_boost": 0.3,
            },
            "security": {
                "patterns": [
                    r"(?:unauthorized|forbidden|access denied)",
                    r"authentication.*(?:failed|error)",
                    r"authorization.*(?:failed|error)",
                    r"(?:csrf|xss|sql injection).*(?:detected|blocked)",
                    r"security.*(?:violation|error|breach)",
                ],
                "severity_boost": 0.4,
            },
            "filesystem": {
                "patterns": [
                    r"(?:file|directory).*(?:not found|missing|access denied)",
                    r"(?:disk|storage).*(?:full|error|failure)",
                    r"permission.*denied",
                    r"(?:read|write).*(?:error|failed)",
                ],
                "severity_boost": 0.1,
            },
            "syntax": {
                "patterns": [
                    r"syntax.*error",
                    r"parse.*error",
                    r"invalid.*syntax",
                    r"(?:unexpected|missing).*(?:token|character|symbol)",
                ],
                "severity_boost": -0.1,
            },
            "type": {
                "patterns": [
                    r"type.*error",
                    r"attribute.*error",
                    r"(?:null|undefined).*(?:reference|pointer)",
                    r"cast.*(?:error|exception)",
                    r"(?:invalid|incompatible).*type",
                ],
                "severity_boost": 0.0,
            },
            "runtime": {
                "patterns": [
                    r"runtime.*(?:error|exception)",
                    r"(?:null|undefined).*(?:exception|error)",
                    r"array.*(?:index|bounds).*(?:error|exception)",
                    r"division.*by.*zero",
                ],
                "severity_boost": 0.1,
            },
            "performance": {
                "patterns": [
                    r"timeout.*(?:error|exception)",
                    r"(?:slow|performance).*(?:query|request|operation)",
                    r"(?:high|excessive).*(?:cpu|memory|latency)",
                    r"rate.*(?:limit|exceeded)",
                ],
                "severity_boost": 0.2,
            },
        }

    def classify_error(self, parsed_error: ParsedError) -> Tuple[List[str], float]:
        """Classify error and return categories with confidence score."""
        message_lower = parsed_error.message.lower()
        stack_trace_lower = (parsed_error.stack_trace or "").lower()

        categories = []
        confidence_adjustments = []

        for category, rules in self.classification_rules.items():
            category_matches = 0

            for pattern in rules["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    category_matches += 1
                elif re.search(pattern, stack_trace_lower, re.IGNORECASE):
                    category_matches += 0.5

            if category_matches > 0:
                categories.append(category)
                confidence_adjustments.append(rules["severity_boost"])

        # Default category if no matches
        if not categories:
            categories = ["unknown"]
            confidence_adjustments = [0.0]

        # Calculate overall confidence (0.0 to 1.0)
        base_confidence = 0.7  # Base confidence for classified errors
        confidence_adjustment = sum(confidence_adjustments) / len(
            confidence_adjustments
        )
        confidence = max(0.1, min(1.0, base_confidence + confidence_adjustment))

        return categories, confidence


class CorrelationEngine:
    """Engine for detecting correlations between errors and other context items."""

    def __init__(self, database_connection):
        self.database = database_connection
        self.correlation_window = timedelta(
            hours=2
        )  # Look for correlations within 2 hours

    async def detect_correlations(
        self, parsed_error: ParsedError, context_items: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Detect correlations with existing context items."""
        correlations = []

        # Git commit correlations
        git_correlations = await self._find_git_correlations(parsed_error)
        correlations.extend(git_correlations)

        # Chat conversation correlations
        chat_correlations = await self._find_chat_correlations(
            parsed_error, context_items
        )
        correlations.extend(chat_correlations)

        # Code change correlations
        code_correlations = await self._find_code_correlations(
            parsed_error, context_items
        )
        correlations.extend(code_correlations)

        # Similar error correlations
        similar_error_correlations = await self._find_similar_error_correlations(
            parsed_error, context_items
        )
        correlations.extend(similar_error_correlations)

        return correlations

    async def _find_git_correlations(
        self, parsed_error: ParsedError
    ) -> List[Tuple[str, str, float]]:
        """Find correlations with Git commits."""
        correlations = []

        if not parsed_error.file_path:
            return correlations

        # Look for recent commits to the error file
        start_time = parsed_error.timestamp - self.correlation_window
        end_time = parsed_error.timestamp + timedelta(minutes=30)

        try:
            query = """
                SELECT id, source_id, timestamp, file_path, content
                FROM context_items
                WHERE source_type = 'git'
                  AND entity_type = 'commit'
                  AND file_path = %s
                  AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
                LIMIT 10
            """

            results = await self.database.fetch_all(
                query, [parsed_error.file_path, start_time, end_time]
            )

            for result in results:
                # Calculate temporal proximity score
                time_diff = abs(
                    (parsed_error.timestamp - result["timestamp"]).total_seconds()
                )
                proximity_score = max(0.1, 1.0 - (time_diff / 7200))  # 2-hour window

                # Check for error-related keywords in commit message
                commit_content = result["content"].lower()
                error_keywords = ["fix", "bug", "error", "issue", "crash", "fail"]
                keyword_matches = sum(
                    1 for keyword in error_keywords if keyword in commit_content
                )
                keyword_score = min(1.0, keyword_matches * 0.2)

                final_score = (proximity_score * 0.6) + (keyword_score * 0.4)

                if final_score > 0.3:
                    correlations.append(("git_commit", result["id"], final_score))

        except Exception as e:
            logger.warning(f"Error finding git correlations: {e}")

        return correlations

    async def _find_chat_correlations(
        self, parsed_error: ParsedError, context_items: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Find correlations with chat conversations."""
        correlations = []

        # Look for chat messages discussing the error or related files
        error_terms = [
            parsed_error.error_type.lower(),
            parsed_error.message.split()[0].lower() if parsed_error.message else "",
        ]

        if parsed_error.file_path:
            file_name = Path(parsed_error.file_path).name
            error_terms.append(file_name)

        for item in context_items:
            if item.source_type != "chat":
                continue

            # Time-based correlation (within correlation window)
            if item.timestamp:
                time_diff = abs(
                    (parsed_error.timestamp - item.timestamp).total_seconds()
                )
                if time_diff > self.correlation_window.total_seconds():
                    continue

            # Content-based correlation
            item_content_lower = (item.content or "").lower()
            matches = sum(
                1 for term in error_terms if term and term in item_content_lower
            )

            if matches > 0:
                content_score = min(1.0, matches * 0.3)
                time_score = (
                    max(0.1, 1.0 - (time_diff / 7200)) if item.timestamp else 0.5
                )
                final_score = (content_score * 0.7) + (time_score * 0.3)

                if final_score > 0.3:
                    correlations.append(("chat_discussion", item.id, final_score))

        return correlations

    async def _find_code_correlations(
        self, parsed_error: ParsedError, context_items: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Find correlations with code changes."""
        correlations = []

        if not parsed_error.file_path:
            return correlations

        for item in context_items:
            if item.source_type != "code":
                continue

            # Same file correlation
            if item.file_path == parsed_error.file_path:
                score = 0.8

                # Line proximity bonus
                if (
                    parsed_error.line_number
                    and item.line_start
                    and abs(parsed_error.line_number - item.line_start) <= 10
                ):
                    score += 0.1

                # Function name match
                if (
                    parsed_error.function_name
                    and item.function_name
                    and parsed_error.function_name == item.function_name
                ):
                    score += 0.1

                correlations.append(("code_location", item.id, min(1.0, score)))

        return correlations

    async def _find_similar_error_correlations(
        self, parsed_error: ParsedError, context_items: List[ContextItem]
    ) -> List[Tuple[str, str, float]]:
        """Find correlations with similar errors."""
        correlations = []

        for item in context_items:
            if item.source_type != "error":
                continue

            similarity_score = self._calculate_error_similarity(parsed_error, item)

            if similarity_score > 0.7:
                correlations.append(("similar_error", item.id, similarity_score))

        return correlations

    def _calculate_error_similarity(
        self, parsed_error: ParsedError, context_item: ContextItem
    ) -> float:
        """Calculate similarity between two errors."""
        if not context_item.metrics:
            return 0.0

        similarity_score = 0.0

        # Error type similarity
        item_error_type = context_item.metrics.get("error_type", "")
        if parsed_error.error_type and item_error_type:
            if parsed_error.error_type.lower() == item_error_type.lower():
                similarity_score += 0.3

        # Message similarity (simple word overlap)
        if parsed_error.message and context_item.content:
            message_words = set(parsed_error.message.lower().split())
            content_words = set(context_item.content.lower().split())

            if message_words and content_words:
                overlap = len(message_words & content_words)
                union = len(message_words | content_words)
                similarity_score += 0.4 * (overlap / union) if union > 0 else 0

        # File path similarity
        if parsed_error.file_path and context_item.file_path:
            if parsed_error.file_path == context_item.file_path:
                similarity_score += 0.2

                # Line proximity bonus
                if (
                    parsed_error.line_number
                    and context_item.line_start
                    and abs(parsed_error.line_number - context_item.line_start) <= 5
                ):
                    similarity_score += 0.1

        return min(1.0, similarity_score)


class EnhancedErrorAdapter(BaseAdapter):
    """Enhanced error adapter with comprehensive parsing and correlation detection."""

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for enhanced error adapter."""
        return AdapterConfig(
            adapter_id="enhanced_error",
            source_type="error",
            batch_mode=BatchMode.STREAMING,
            batch_size=50,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                # Input sources
                "input_sources": ["logs", "realtime", "api", "monitoring"],
                "log_file_patterns": ["*.log", "*.err", "error*.log", "*.out"],
                "log_directories": ["./logs", "./log", "/var/log", "/tmp"],
                "watch_directories": True,
                "realtime_processing": True,
                # Parsing configuration
                "supported_formats": ["json", "structured", "plain"],
                "auto_detect_format": True,
                "extract_stack_traces": True,
                "parse_multiline_errors": True,
                "multiline_timeout_seconds": 5,
                # Classification
                "enable_error_classification": True,
                "enable_severity_scoring": True,
                "severity_keywords": {
                    "critical": ["fatal", "critical", "crash", "panic", "abort"],
                    "high": ["error", "err", "exception", "fail"],
                    "medium": ["warn", "warning", "caution"],
                    "low": ["info", "debug", "trace"],
                },
                # Pattern detection
                "enable_pattern_detection": True,
                "pattern_similarity_threshold": 0.8,
                "pattern_frequency_threshold": 3,
                "pattern_time_window_hours": 24,
                # Correlation detection
                "enable_correlation_detection": True,
                "correlation_window_hours": 2,
                "git_correlation_enabled": True,
                "chat_correlation_enabled": True,
                "code_correlation_enabled": True,
                # Performance
                "max_file_size_mb": 100,
                "max_stack_trace_length": 10000,
                "max_error_age_days": 30,
                "batch_processing_timeout": 60,
                # Filtering
                "exclude_patterns": [
                    r".*DEBUG.*",
                    r".*TRACE.*",
                    r".*health.*check.*",
                    r".*heartbeat.*",
                ],
                "severity_filters": ["error", "warning"],  # empty = all
                "min_message_length": 10,
                "max_message_length": 10000,
            },
        )

    def __init__(self, config: AdapterConfig):
        """Initialize enhanced error adapter."""
        super().__init__(config)

        # Core components
        self.transformer = DataTransformer()
        self.format_detector = LogFormatDetector()
        self.stack_parser = StackTraceParser()
        self.classifier = ErrorClassifier()

        # State tracking
        self.processed_files: Set[str] = set()
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.pattern_cache: Dict[str, Tuple[List[str], float]] = {}

        # Async components
        self.correlation_engine: Optional[CorrelationEngine] = None
        self.file_watchers: Dict[str, Any] = {}

        # Intelligence components
        self.trend_analyzer = TrendAnalyzer(
            time_window_hours=self.config.source_config.get(
                "pattern_time_window_hours", 24
            )
        )
        self.deduplicator = ErrorDeduplicator(
            similarity_threshold=self.config.source_config.get(
                "pattern_similarity_threshold", 0.8
            )
        )
        self.performance_monitor = PerformanceMonitor()

        # Metrics
        self.stats = {
            "total_errors_processed": 0,
            "errors_by_severity": defaultdict(int),
            "errors_by_category": defaultdict(int),
            "patterns_detected": 0,
            "correlations_found": 0,
            "processing_time_ms": [],
        }

    async def initialize(self) -> None:
        """Initialize the enhanced error adapter."""
        self.logger.info("Initializing enhanced error adapter")

        # Initialize correlation engine if enabled
        if self.config.source_config.get("enable_correlation_detection", True):
            # We'll get database connection from pipeline
            self.correlation_engine = CorrelationEngine(None)  # Will be set by pipeline

        # Set up file watchers if realtime processing is enabled
        if self.config.source_config.get("realtime_processing", False):
            await self._setup_file_watchers()

        # Validate configuration
        await self._validate_configuration()

        self.logger.info("Enhanced error adapter initialized successfully")

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch and parse error items from various sources."""
        input_sources = self.config.source_config.get("input_sources", ["logs"])
        count = 0

        for source in input_sources:
            if limit and count >= limit:
                break

            try:
                async for item in self._fetch_from_source(
                    source, since, until, limit - count
                ):
                    yield item
                    count += 1
            except Exception as e:
                self.logger.error(f"Error fetching from source {source}: {e}")
                continue

    async def _fetch_from_source(
        self,
        source: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch errors from a specific source."""
        if source == "logs":
            async for item in self._fetch_from_logs(since, until, limit):
                yield item
        elif source == "realtime":
            async for item in self._fetch_from_realtime(since, until, limit):
                yield item
        elif source == "api":
            async for item in self._fetch_from_api(since, until, limit):
                yield item
        elif source == "monitoring":
            async for item in self._fetch_from_monitoring(since, until, limit):
                yield item
        else:
            self.logger.warning(f"Unknown source: {source}")

    async def _fetch_from_logs(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch errors from log files with enhanced parsing."""
        log_dirs = self.config.source_config.get("log_directories", ["./logs"])
        patterns = self.config.source_config.get("log_file_patterns", ["*.log"])
        max_file_size = (
            self.config.source_config.get("max_file_size_mb", 100) * 1024 * 1024
        )

        count = 0

        for log_dir in log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue

            for pattern in patterns:
                for log_file in dir_path.glob(pattern):
                    # Check file size
                    if log_file.stat().st_size > max_file_size:
                        self.logger.warning(
                            f"Skipping large file: {log_file} ({log_file.stat().st_size} bytes)"
                        )
                        continue

                    # Skip already processed files (unless watching)
                    file_key = f"{log_file}:{log_file.stat().st_mtime}"
                    if (
                        file_key in self.processed_files
                        and not self.config.source_config.get(
                            "realtime_processing", False
                        )
                    ):
                        continue

                    try:
                        async for parsed_error in self._parse_log_file_enhanced(
                            log_file, since, until
                        ):
                            if limit and count >= limit:
                                return

                            error_dict = await self._parsed_error_to_dict(parsed_error)
                            yield error_dict
                            count += 1

                        self.processed_files.add(file_key)

                    except Exception as e:
                        self.logger.error(f"Error processing log file {log_file}: {e}")
                        continue

    async def _parse_log_file_enhanced(
        self,
        log_file: Path,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[ParsedError]:
        """Enhanced log file parsing with multi-format support."""
        exclude_patterns = self.config.source_config.get("exclude_patterns", [])
        severity_filters = self.config.source_config.get("severity_filters", [])
        multiline_timeout = self.config.source_config.get(
            "multiline_timeout_seconds", 5
        )

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                current_error_lines = []
                last_timestamp = None
                line_buffer = []

                for line_num, line in enumerate(f, 1):
                    line = line.rstrip()

                    if not line:
                        continue

                    # Check exclusion patterns
                    if any(
                        re.search(pattern, line, re.IGNORECASE)
                        for pattern in exclude_patterns
                    ):
                        continue

                    # Detect format and parse
                    format_type = self.format_detector.detect_format(line)
                    parsed_line = await self._parse_single_line(
                        line, format_type, line_num, str(log_file)
                    )

                    if parsed_line:
                        # If we have accumulated lines, process them as one error
                        if line_buffer:
                            try:
                                combined_error = await self._combine_multiline_error(
                                    line_buffer
                                )
                                if combined_error and self._passes_filters(
                                    combined_error, severity_filters, since, until
                                ):
                                    yield combined_error
                            except Exception as e:
                                self.logger.debug(
                                    f"Error combining multiline error: {e}"
                                )

                            line_buffer = []

                        # Check if this line passes filters
                        if self._passes_filters(
                            parsed_line, severity_filters, since, until
                        ):
                            line_buffer = [parsed_line]
                            last_timestamp = parsed_line.timestamp
                    else:
                        # This might be a continuation line (stack trace, etc.)
                        if line_buffer and self._is_continuation_line(line):
                            # Add to current error context
                            if line_buffer[-1].stack_trace:
                                line_buffer[-1].stack_trace += "\n" + line
                            else:
                                line_buffer[-1].stack_trace = line

                            # Parse stack trace elements
                            stack_elements = self.stack_parser.parse_stack_trace(line)
                            line_buffer[-1].stack_elements.extend(stack_elements)
                        elif line_buffer:
                            # Process accumulated error and start fresh
                            try:
                                combined_error = await self._combine_multiline_error(
                                    line_buffer
                                )
                                if combined_error:
                                    yield combined_error
                            except Exception as e:
                                self.logger.debug(
                                    f"Error combining multiline error: {e}"
                                )

                            line_buffer = []

                # Process any remaining buffered error
                if line_buffer:
                    try:
                        combined_error = await self._combine_multiline_error(
                            line_buffer
                        )
                        if combined_error:
                            yield combined_error
                    except Exception as e:
                        self.logger.debug(f"Error combining final multiline error: {e}")

        except Exception as e:
            self.logger.error(f"Error reading log file {log_file}: {e}")

    async def _parse_single_line(
        self, line: str, format_type: str, line_num: int, file_path: str
    ) -> Optional[ParsedError]:
        """Parse a single log line based on detected format."""
        try:
            if format_type == "json":
                return await self._parse_json_line(line, line_num, file_path)
            elif format_type == "structured":
                return await self._parse_structured_line(line, line_num, file_path)
            else:
                return await self._parse_plain_line(line, line_num, file_path)
        except Exception as e:
            self.logger.debug(f"Error parsing line {line_num}: {e}")
            self.performance_monitor.record_parsing_failure()
            return None

    async def _parse_json_line(
        self, line: str, line_num: int, file_path: str
    ) -> Optional[ParsedError]:
        """Parse JSON-formatted log line."""
        try:
            data = json.loads(line)

            # Extract timestamp
            timestamp_field = None
            for field in ["timestamp", "@timestamp", "time", "datetime", "ts"]:
                if field in data:
                    timestamp_field = data[field]
                    break

            timestamp = (
                await self._parse_timestamp(timestamp_field)
                if timestamp_field
                else datetime.now()
            )

            # Extract severity/level
            level_field = None
            for field in ["level", "severity", "log_level", "priority"]:
                if field in data:
                    level_field = data[field]
                    break

            severity = (
                self._normalize_severity(level_field) if level_field else "unknown"
            )

            # Extract message
            message_field = None
            for field in ["message", "msg", "text", "content"]:
                if field in data:
                    message_field = data[field]
                    break

            message = str(message_field) if message_field else ""

            # Create parsed error
            error_id = self._generate_error_id(message, file_path, line_num)

            parsed_error = ParsedError(
                error_id=error_id,
                timestamp=timestamp,
                severity=severity,
                error_type=data.get("error_type", data.get("exception", "unknown")),
                message=message,
                source="json_log",
                file_path=data.get("file", data.get("source_file")),
                line_number=data.get("line", data.get("line_number")),
                function_name=data.get("function", data.get("method")),
                class_name=data.get("class", data.get("class_name")),
                stack_trace=data.get("stack_trace", data.get("traceback")),
                environment=data.get("env", data.get("environment")),
                process_id=data.get("pid", data.get("process_id")),
                thread_id=data.get("tid", data.get("thread_id")),
                user_id=data.get("user", data.get("user_id")),
                request_id=data.get("request_id", data.get("correlation_id")),
                raw_data=data,
            )

            # Parse stack trace if present
            if parsed_error.stack_trace:
                parsed_error.stack_elements = self.stack_parser.parse_stack_trace(
                    parsed_error.stack_trace
                )

            return parsed_error

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.debug(f"Failed to parse JSON line {line_num}: {e}")
            return None

    async def _parse_structured_line(
        self, line: str, line_num: int, file_path: str
    ) -> Optional[ParsedError]:
        """Parse structured log line using regex patterns."""
        # Standard format pattern
        pattern = r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d{3,6})?(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<level>\w+)\s+(?:\[(?P<component>[^\]]+)\]\s*)?(?P<message>.*)"

        match = re.match(pattern, line)
        if not match:
            return None

        groups = match.groupdict()

        # Parse timestamp
        timestamp = await self._parse_timestamp(groups["timestamp"])
        if not timestamp:
            timestamp = datetime.now()

        # Create error ID
        error_id = self._generate_error_id(groups["message"], file_path, line_num)

        parsed_error = ParsedError(
            error_id=error_id,
            timestamp=timestamp,
            severity=self._normalize_severity(groups["level"]),
            error_type=self._extract_error_type(groups["message"]),
            message=groups["message"],
            source="structured_log",
            raw_data={
                "file": file_path,
                "line_number": line_num,
                "component": groups.get("component"),
                "original_line": line,
            },
        )

        return parsed_error

    async def _parse_plain_line(
        self, line: str, line_num: int, file_path: str
    ) -> Optional[ParsedError]:
        """Parse plain text log line."""
        # Simple pattern matching for common error indicators
        error_indicators = ["error", "exception", "fail", "crash", "panic", "fatal"]

        line_lower = line.lower()
        if not any(indicator in line_lower for indicator in error_indicators):
            return None

        # Try to extract timestamp from beginning of line
        timestamp_match = re.match(r"^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})", line)
        timestamp = datetime.now()
        if timestamp_match:
            timestamp = await self._parse_timestamp(timestamp_match.group(1))

        # Detect severity from keywords
        severity = "medium"
        for sev_level, keywords in self.config.source_config.get(
            "severity_keywords", {}
        ).items():
            if any(keyword in line_lower for keyword in keywords):
                severity = sev_level
                break

        # Create error ID
        error_id = self._generate_error_id(line, file_path, line_num)

        parsed_error = ParsedError(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            error_type=self._extract_error_type(line),
            message=line.strip(),
            source="plain_log",
            raw_data={
                "file": file_path,
                "line_number": line_num,
                "original_line": line,
            },
        )

        return parsed_error

    def _passes_filters(
        self,
        parsed_error: ParsedError,
        severity_filters: List[str],
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> bool:
        """Check if parsed error passes configured filters."""
        # Severity filter
        if severity_filters and parsed_error.severity not in severity_filters:
            return False

        # Time filter
        if since and parsed_error.timestamp < since:
            return False
        if until and parsed_error.timestamp > until:
            return False

        # Message length filter
        min_length = self.config.source_config.get("min_message_length", 0)
        max_length = self.config.source_config.get("max_message_length", float("inf"))

        message_length = len(parsed_error.message)
        if message_length < min_length or message_length > max_length:
            return False

        return True

    def _is_continuation_line(self, line: str) -> bool:
        """Check if line is a continuation of previous error (stack trace, etc.)."""
        continuation_patterns = [
            r"^\s+at\s+",  # Java/JavaScript stack traces
            r'^\s+File\s+".*",\s+line\s+\d+',  # Python stack traces
            r"^\s+in\s+.*:\d+",  # Various formats
            r"^\s+.*\(\s*.*:\d+\s*\)",  # Function calls with line numbers
            r"^\s*Caused by:",  # Exception chains
            r"^\s{2,}",  # General indentation
        ]

        return any(re.match(pattern, line) for pattern in continuation_patterns)

    async def _combine_multiline_error(
        self, error_lines: List[ParsedError]
    ) -> Optional[ParsedError]:
        """Combine multiple related error lines into single structured error."""
        if not error_lines:
            return None

        # Use first line as base
        base_error = error_lines[0]

        # Combine stack traces and content from additional lines
        all_stack_elements = []
        for error_line in error_lines:
            all_stack_elements.extend(error_line.stack_elements)

        base_error.stack_elements = all_stack_elements

        return base_error

    async def _parsed_error_to_dict(self, parsed_error: ParsedError) -> Dict[str, Any]:
        """Convert ParsedError to dictionary format expected by pipeline."""
        # Classify error if enabled
        categories, confidence = [], 0.7
        if self.config.source_config.get("enable_error_classification", True):
            categories, confidence = self.classifier.classify_error(parsed_error)

        # Update pattern tracking and clustering
        if self.config.source_config.get("enable_pattern_detection", True):
            await self._update_error_patterns(parsed_error, categories)

            # Update trend analysis
            pattern_signature = self._create_pattern_signature(parsed_error, categories)
            self.trend_analyzer.update_pattern_frequency(
                pattern_signature, parsed_error.timestamp
            )

            # Handle deduplication and clustering
            cluster_id = self.deduplicator.find_or_create_cluster(parsed_error)
            raw_item["cluster_id"] = cluster_id
            raw_item["is_duplicate"] = (
                len(self.deduplicator.error_clusters[cluster_id]) > 1
            )

        # Update statistics
        self.stats["total_errors_processed"] += 1
        self.stats["errors_by_severity"][parsed_error.severity] += 1
        for category in categories:
            self.stats["errors_by_category"][category] += 1

        # Convert to dictionary
        return {
            "error_id": parsed_error.error_id,
            "timestamp": parsed_error.timestamp,
            "severity": parsed_error.severity,
            "error_type": parsed_error.error_type,
            "message": parsed_error.message,
            "source": parsed_error.source,
            "file_path": parsed_error.file_path,
            "line_number": parsed_error.line_number,
            "function_name": parsed_error.function_name,
            "class_name": parsed_error.class_name,
            "stack_trace": parsed_error.stack_trace,
            "environment": parsed_error.environment,
            "process_id": parsed_error.process_id,
            "thread_id": parsed_error.thread_id,
            "user_id": parsed_error.user_id,
            "request_id": parsed_error.request_id,
            "categories": categories,
            "classification_confidence": confidence,
            "stack_elements": [
                {
                    "file_path": elem.file_path,
                    "function_name": elem.function_name,
                    "line_number": elem.line_number,
                    "class_name": elem.class_name,
                    "code_context": elem.code_context,
                }
                for elem in parsed_error.stack_elements
            ],
            "tags": list(parsed_error.tags),
            "metrics": parsed_error.metrics,
            "raw_data": parsed_error.raw_data,
        }

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw error item into ContextItem."""
        start_time = datetime.now()

        # Create base context item
        item = self.transformer.create_base_context_item(
            source_type="error", source_id=raw_item["error_id"], raw_data=raw_item
        )

        # Error-specific fields
        item.title = self._generate_error_title(raw_item)
        item.content = self._generate_error_content(raw_item)
        item.timestamp = raw_item["timestamp"]
        item.severity = raw_item["severity"]

        # Location information
        item.file_path = raw_item.get("file_path")
        item.line_start = raw_item.get("line_number")
        item.function_name = raw_item.get("function_name")
        item.class_name = raw_item.get("class_name")

        # Entity type based on severity and categories
        item.entity_type = self._determine_entity_type(raw_item)

        # Build comprehensive metadata
        item.metrics = {
            "error_type": raw_item["error_type"],
            "source": raw_item["source"],
            "categories": raw_item.get("categories", []),
            "classification_confidence": raw_item.get("classification_confidence", 0.7),
            "stack_depth": len(raw_item.get("stack_elements", [])),
            "has_stack_trace": bool(raw_item.get("stack_trace")),
            "environment": raw_item.get("environment"),
            "process_id": raw_item.get("process_id"),
            "thread_id": raw_item.get("thread_id"),
            "user_id": raw_item.get("user_id"),
            "request_id": raw_item.get("request_id"),
            # Enhanced metadata
            "cluster_id": raw_item.get("cluster_id"),
            "is_duplicate": raw_item.get("is_duplicate", False),
            "pattern_signature": raw_item.get("pattern_signature"),
        }

        # Generate comprehensive tags
        item.tags = self._generate_comprehensive_tags(raw_item)

        # Apply transformations
        item = await self.transformer.transform_item(item)

        # Track processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        self.stats["processing_time_ms"].append(processing_time)
        self.performance_monitor.record_processing_time(processing_time)
        self.performance_monitor.record_error_count(item.timestamp)

        return item

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships with enhanced correlation detection."""
        relationships = []

        # Use correlation engine if available and enabled
        if self.correlation_engine and self.config.source_config.get(
            "enable_correlation_detection", True
        ):
            # Convert ContextItem back to ParsedError for correlation analysis
            parsed_error = self._context_item_to_parsed_error(item)

            try:
                correlations = await self.correlation_engine.detect_correlations(
                    parsed_error, context_window
                )

                # Convert correlation results to relationship tuples
                for correlation_type, target_id, confidence in correlations:
                    relationships.append((correlation_type, target_id, confidence))

                self.stats["correlations_found"] += len(correlations)

            except Exception as e:
                self.logger.warning(f"Error in correlation detection: {e}")
                self.performance_monitor.record_correlation_failure()

        # Add traditional relationship detection
        traditional_relationships = await self._detect_traditional_relationships(
            item, context_window
        )
        relationships.extend(traditional_relationships)

        return relationships

    async def cleanup(self) -> None:
        """Clean up adapter resources."""
        self.logger.info("Cleaning up enhanced error adapter")

        # Stop file watchers
        for watcher in self.file_watchers.values():
            try:
                await watcher.stop()
            except Exception as e:
                self.logger.warning(f"Error stopping file watcher: {e}")

        # Clear caches
        self.processed_files.clear()
        self.error_patterns.clear()
        self.pattern_cache.clear()

        # Clear intelligence components
        self.trend_analyzer.pattern_cache.clear()
        self.deduplicator.error_clusters.clear()
        self.deduplicator.error_to_cluster.clear()
        self.deduplicator.cluster_representatives.clear()

        # Log final statistics
        self.logger.info(f"Final statistics: {dict(self.stats)}")

    # Helper methods

    async def _setup_file_watchers(self) -> None:
        """Set up file watchers for real-time log monitoring."""
        # This would set up file system watchers for real-time processing
        # Implementation depends on chosen file watching library
        pass

    async def _validate_configuration(self) -> None:
        """Validate adapter configuration."""
        # Check required directories exist
        log_dirs = self.config.source_config.get("log_directories", [])
        for log_dir in log_dirs:
            if not Path(log_dir).exists():
                self.logger.warning(f"Log directory does not exist: {log_dir}")

    async def _fetch_from_realtime(
        self, since, until, limit
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from real-time log streams."""
        # Placeholder for real-time log streaming
        # Would integrate with log streaming systems like Kafka, Redis Streams, etc.
        return
        yield  # Make this a generator

    async def _fetch_from_api(
        self, since, until, limit
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from API endpoints."""
        # Placeholder for API-based error fetching
        return
        yield  # Make this a generator

    async def _fetch_from_monitoring(
        self, since, until, limit
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from monitoring systems."""
        # Placeholder for monitoring system integration
        return
        yield  # Make this a generator

    async def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats."""
        if not timestamp_str:
            return None

        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%b/%Y:%H:%M:%S %z",  # Apache format
            "%b %d %H:%M:%S",  # Syslog format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(timestamp_str), fmt)
            except ValueError:
                continue

        return None

    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity levels."""
        if not severity:
            return "medium"

        severity = str(severity).upper()

        if severity in ["CRITICAL", "FATAL", "PANIC", "EMERGENCY"]:
            return "critical"
        elif severity in ["ERROR", "ERR", "SEVERE"]:
            return "high"
        elif severity in ["WARN", "WARNING", "CAUTION"]:
            return "medium"
        elif severity in ["INFO", "INFORMATION", "NOTICE"]:
            return "low"
        elif severity in ["DEBUG", "TRACE", "VERBOSE"]:
            return "low"
        else:
            return "medium"

    def _extract_error_type(self, message: str) -> str:
        """Extract error type from message."""
        # Common error type patterns
        patterns = [
            r"(\w*Exception)",
            r"(\w*Error)",
            r"(\w*Failure)",
            r"(\w*Fault)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)

        return "UnknownError"

    def _generate_error_id(self, message: str, file_path: str, line_num: int) -> str:
        """Generate unique error ID."""
        content = f"{message}{file_path}{line_num}{datetime.now().isoformat()}"
        hash_object = hashlib.md5(content.encode())
        return f"error_{hash_object.hexdigest()[:12]}"

    def _generate_error_title(self, raw_error: Dict[str, Any]) -> str:
        """Generate concise error title."""
        error_type = raw_error.get("error_type", "Error")
        message = raw_error.get("message", "")

        if message:
            # Take first meaningful part of message
            first_line = message.split("\n")[0].strip()
            if len(first_line) > 100:
                first_line = first_line[:97] + "..."
            return f"{error_type}: {first_line}"

        return error_type

    def _generate_error_content(self, raw_error: Dict[str, Any]) -> str:
        """Generate comprehensive error content."""
        parts = []

        # Main message
        if raw_error.get("message"):
            parts.append(f"Message: {raw_error['message']}")

        # Error details
        if raw_error.get("error_type"):
            parts.append(f"Error Type: {raw_error['error_type']}")

        # Location information
        if raw_error.get("file_path"):
            location = f"File: {raw_error['file_path']}"
            if raw_error.get("line_number"):
                location += f":{raw_error['line_number']}"
            if raw_error.get("function_name"):
                location += f" in {raw_error['function_name']}()"
            parts.append(location)

        # Stack trace
        if raw_error.get("stack_trace"):
            parts.append("Stack Trace:")
            parts.append(raw_error["stack_trace"])

        # Environment context
        env_parts = []
        for field in [
            "environment",
            "process_id",
            "thread_id",
            "user_id",
            "request_id",
        ]:
            if raw_error.get(field):
                env_parts.append(f"{field}: {raw_error[field]}")

        if env_parts:
            parts.append("Environment: " + ", ".join(env_parts))

        # Categories
        if raw_error.get("categories"):
            parts.append(f"Categories: {', '.join(raw_error['categories'])}")

        return "\n".join(parts)

    def _determine_entity_type(self, raw_error: Dict[str, Any]) -> str:
        """Determine entity type based on error characteristics."""
        severity = raw_error.get("severity", "medium")
        categories = raw_error.get("categories", [])

        if severity == "critical":
            return "critical_error"
        elif "security" in categories:
            return "security_error"
        elif "performance" in categories:
            return "performance_error"
        elif severity == "high":
            return "error"
        elif severity == "medium":
            return "warning"
        else:
            return "diagnostic"

    def _generate_comprehensive_tags(self, raw_error: Dict[str, Any]) -> List[str]:
        """Generate comprehensive tags for error."""
        tags = ["error", raw_error["severity"]]

        # Add categories as tags
        if raw_error.get("categories"):
            tags.extend(raw_error["categories"])

        # Add source tag
        if raw_error.get("source"):
            tags.append(f"source_{raw_error['source']}")

        # Add environment tag
        if raw_error.get("environment"):
            tags.append(f"env_{raw_error['environment']}")

        # Add file extension tag
        if raw_error.get("file_path"):
            file_path = Path(raw_error["file_path"])
            if file_path.suffix:
                tags.append(f"lang_{file_path.suffix[1:]}")

        # Add error type tag
        if raw_error.get("error_type"):
            tags.append(f"type_{raw_error['error_type'].lower()}")

        return list(set(tags))  # Remove duplicates

    async def _update_error_patterns(
        self, parsed_error: ParsedError, categories: List[str]
    ) -> None:
        """Update error pattern tracking."""
        try:
            # Create error signature for pattern detection
            signature_parts = [
                parsed_error.error_type,
                str(parsed_error.file_path) if parsed_error.file_path else "",
            ]

            if categories:
                signature_parts.extend(categories[:2])  # Top 2 categories

            error_signature = "|".join(signature_parts)
            signature_hash = hashlib.md5(error_signature.encode()).hexdigest()[:12]

            # Update or create pattern
            if signature_hash not in self.error_patterns:
                self.error_patterns[signature_hash] = ErrorPattern(
                    pattern_id=signature_hash,
                    error_signature=error_signature,
                    first_seen=parsed_error.timestamp,
                )
                self.stats["patterns_detected"] += 1

            pattern = self.error_patterns[signature_hash]
            pattern.frequency += 1
            pattern.last_seen = parsed_error.timestamp

            if parsed_error.file_path:
                pattern.file_paths.add(parsed_error.file_path)

            pattern.severity_distribution[parsed_error.severity] = (
                pattern.severity_distribution.get(parsed_error.severity, 0) + 1
            )

        except Exception as e:
            self.logger.debug(f"Error updating patterns: {e}")

    def _context_item_to_parsed_error(self, item: ContextItem) -> ParsedError:
        """Convert ContextItem back to ParsedError for correlation analysis."""
        metrics = item.metrics or {}

        return ParsedError(
            error_id=item.source_id,
            timestamp=item.timestamp,
            severity=item.severity or "medium",
            error_type=metrics.get("error_type", "unknown"),
            message=item.content or "",
            source=metrics.get("source", "unknown"),
            file_path=item.file_path,
            line_number=item.line_start,
            function_name=item.function_name,
            class_name=item.class_name,
            stack_trace=metrics.get("stack_trace"),
            environment=metrics.get("environment"),
            process_id=metrics.get("process_id"),
            thread_id=metrics.get("thread_id"),
            user_id=metrics.get("user_id"),
            request_id=metrics.get("request_id"),
            raw_data=item.source_data or {},
        )

    async def _detect_traditional_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships using traditional methods."""
        relationships = []

        if not item.metrics:
            return relationships

        # Similar error relationships
        similarity_threshold = self.config.source_config.get(
            "pattern_similarity_threshold", 0.8
        )

        for context_item in context_window:
            if context_item.source_type != "error" or not context_item.metrics:
                continue

            similarity = self._calculate_item_similarity(item, context_item)
            if similarity > similarity_threshold:
                relationships.append(("similar_error", context_item.id, similarity))

        # File location relationships
        if item.file_path:
            for context_item in context_window:
                if (
                    context_item.file_path == item.file_path
                    and context_item.id != item.id
                ):
                    score = 0.7
                    # Line proximity bonus
                    if (
                        item.line_start
                        and context_item.line_start
                        and abs(item.line_start - context_item.line_start) <= 10
                    ):
                        score += 0.2

                    relationships.append(("same_file", context_item.id, score))

        return relationships

    def _calculate_item_similarity(
        self, item1: ContextItem, item2: ContextItem
    ) -> float:
        """Calculate similarity between two context items."""
        if not item1.metrics or not item2.metrics:
            return 0.0

        similarity_score = 0.0

        # Error type similarity
        type1 = item1.metrics.get("error_type", "")
        type2 = item2.metrics.get("error_type", "")
        if type1 and type2 and type1 == type2:
            similarity_score += 0.3

        # Content similarity (word overlap)
        if item1.content and item2.content:
            words1 = set(item1.content.lower().split())
            words2 = set(item2.content.lower().split())

            if words1 and words2:
                overlap = len(words1 & words2)
                union = len(words1 | words2)
                similarity_score += 0.4 * (overlap / union) if union > 0 else 0

        # File path similarity
        if item1.file_path and item2.file_path:
            if item1.file_path == item2.file_path:
                similarity_score += 0.2

                # Line proximity bonus
                if (
                    item1.line_start
                    and item2.line_start
                    and abs(item1.line_start - item2.line_start) <= 5
                ):
                    similarity_score += 0.1

        return min(1.0, similarity_score)

    def _create_pattern_signature(
        self, parsed_error: ParsedError, categories: List[str]
    ) -> str:
        """Create a pattern signature for trend analysis."""
        parts = [
            parsed_error.error_type,
            parsed_error.file_path.split("/")[-1]
            if parsed_error.file_path
            else "unknown",
            categories[0] if categories else "unknown",
        ]
        return "|".join(parts)

    # Public API methods for external integration

    async def get_error_patterns(self) -> List[Dict[str, Any]]:
        """Get detected error patterns."""
        return [
            {
                "pattern_id": pattern.pattern_id,
                "error_signature": pattern.error_signature,
                "frequency": pattern.frequency,
                "first_seen": pattern.first_seen.isoformat()
                if pattern.first_seen
                else None,
                "last_seen": pattern.last_seen.isoformat()
                if pattern.last_seen
                else None,
                "file_paths": list(pattern.file_paths),
                "severity_distribution": dict(pattern.severity_distribution),
            }
            for pattern in self.error_patterns.values()
        ]

    async def get_adapter_statistics(self) -> Dict[str, Any]:
        """Get comprehensive adapter statistics."""
        stats_copy = dict(self.stats)

        # Calculate average processing time
        processing_times = stats_copy.get("processing_time_ms", [])
        if processing_times:
            stats_copy["avg_processing_time_ms"] = sum(processing_times) / len(
                processing_times
            )
            stats_copy["max_processing_time_ms"] = max(processing_times)

        # Add performance monitor stats
        stats_copy.update(
            {
                "performance_stats": self.performance_monitor.get_performance_stats(),
                "recent_alerts": self.performance_monitor.get_recent_alerts(),
                "cluster_count": len(self.deduplicator.error_clusters),
                "trending_patterns": self.trend_analyzer.get_trending_patterns(
                    limit=10
                ),
            }
        )

        return stats_copy

    async def get_trending_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get currently trending error patterns."""
        return self.trend_analyzer.get_trending_patterns(limit=limit)

    async def get_error_clusters(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get error clusters for deduplication analysis."""
        return self.deduplicator.get_all_clusters()[:limit]

    async def predict_error_volume(
        self, pattern_id: str, hours_ahead: int = 1
    ) -> float:
        """Predict future error volume for a pattern."""
        return self.trend_analyzer.predict_future_occurrences(pattern_id, hours_ahead)

    async def get_performance_alerts(self, minutes: int = 15) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return self.performance_monitor.get_recent_alerts(minutes)
