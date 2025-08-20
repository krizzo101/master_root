"""AnalysisAgent - Deep analysis and insights."""

import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class AnalysisType(Enum):
    """Types of analysis."""

    STATISTICAL = "statistical"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COMPARISON = "comparison"
    TREND = "trend"
    ANOMALY = "anomaly"
    DEPENDENCY = "dependency"
    IMPACT = "impact"


class InsightLevel(Enum):
    """Levels of insights."""

    SURFACE = "surface"
    MODERATE = "moderate"
    DEEP = "deep"
    EXPERT = "expert"


@dataclass
class Metric:
    """Analysis metric."""

    name: str
    value: Any
    unit: Optional[str] = None
    category: str = "general"
    description: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class Pattern:
    """Identified pattern."""

    id: str
    type: str
    occurrences: int
    locations: List[str] = field(default_factory=list)
    confidence: float = 1.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "occurrences": self.occurrences,
            "locations": self.locations,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class Insight:
    """Analysis insight."""

    id: str
    level: InsightLevel
    category: str
    title: str
    description: str
    evidence: List[Any] = field(default_factory=list)
    confidence: float = 1.0
    actionable: bool = False
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "level": self.level.value,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "actionable": self.actionable,
            "recommendations": self.recommendations,
        }


@dataclass
class AnalysisReport:
    """Complete analysis report."""

    id: str
    type: AnalysisType
    target: str
    metrics: List[Metric] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)
    insights: List[Insight] = field(default_factory=list)
    summary: str = ""
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key metrics."""
        return {m.name: m.value for m in self.metrics[:5]}

    def get_actionable_insights(self) -> List[Insight]:
        """Get actionable insights."""
        return [i for i in self.insights if i.actionable]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "target": self.target,
            "metrics": [m.to_dict() for m in self.metrics],
            "patterns": [p.to_dict() for p in self.patterns],
            "insights": [i.to_dict() for i in self.insights],
            "summary": self.summary,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "metadata": self.metadata,
        }


class AnalysisAgent(BaseAgent):
    """Performs deep analysis and generates insights."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize analysis agent."""
        super().__init__(
            config
            or AgentConfig(
                name="AnalysisAgent",
                description="Deep analysis and insights",
                capabilities=["analyze", "detect", "measure", "compare", "predict"],
                max_retries=2,
                timeout=120,
            )
        )
        self.reports: Dict[str, AnalysisReport] = {}
        self.metrics_cache: Dict[str, List[Metric]] = {}
        self.patterns_db: Dict[str, Pattern] = {}
        self._report_counter = 0
        self._insight_counter = 0
        self._pattern_counter = 0

    def initialize(self) -> bool:
        """Initialize the analysis agent."""
        logger.info("analysis_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis task."""
        action = task.get("action", "analyze")

        if action == "analyze":
            return self._perform_analysis(task)
        elif action == "statistical":
            return self._statistical_analysis(task)
        elif action == "structural":
            return self._structural_analysis(task)
        elif action == "behavioral":
            return self._behavioral_analysis(task)
        elif action == "performance":
            return self._performance_analysis(task)
        elif action == "compare":
            return self._comparative_analysis(task)
        elif action == "detect_patterns":
            return self._detect_patterns(task)
        elif action == "generate_insights":
            return self._generate_insights(task)
        elif action == "predict":
            return self._predictive_analysis(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def analyze(
        self,
        data: Any,
        analysis_type: AnalysisType = AnalysisType.STATISTICAL,
        depth: InsightLevel = InsightLevel.MODERATE,
    ) -> AnalysisReport:
        """Perform analysis on data."""
        result = self.execute(
            {
                "action": "analyze",
                "data": data,
                "analysis_type": analysis_type.value,
                "depth": depth.value,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["report"]

    def _perform_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive analysis."""
        data = task.get("data")
        analysis_type = task.get("analysis_type", "statistical")
        depth = task.get("depth", "moderate")

        if data is None:
            return {"error": "Data is required"}

        start_time = time.time()

        # Determine analysis type
        type_enum = AnalysisType[analysis_type.upper()]
        depth_enum = InsightLevel[depth.upper()]

        # Create report
        self._report_counter += 1
        report = AnalysisReport(
            id=f"report_{self._report_counter}",
            type=type_enum,
            target=str(type(data).__name__),
        )

        # Perform analysis based on type
        if type_enum == AnalysisType.STATISTICAL:
            metrics = self._compute_statistical_metrics(data)
        elif type_enum == AnalysisType.STRUCTURAL:
            metrics = self._analyze_structure(data)
        elif type_enum == AnalysisType.BEHAVIORAL:
            metrics = self._analyze_behavior(data)
        elif type_enum == AnalysisType.PERFORMANCE:
            metrics = self._analyze_performance(data)
        else:
            metrics = self._general_analysis(data)

        report.metrics = metrics

        # Detect patterns
        patterns = self._detect_data_patterns(data, depth_enum)
        report.patterns = patterns

        # Generate insights
        insights = self._create_insights(metrics, patterns, depth_enum)
        report.insights = insights

        # Generate summary
        report.summary = self._generate_summary(metrics, patterns, insights)
        report.duration = time.time() - start_time

        # Store report
        self.reports[report.id] = report

        logger.info(
            "analysis_completed",
            report_id=report.id,
            type=type_enum.value,
            metrics_count=len(metrics),
            insights_count=len(insights),
            duration=report.duration,
        )

        return {
            "report": report,
            "key_metrics": report.get_key_metrics(),
            "actionable_insights": [
                i.to_dict() for i in report.get_actionable_insights()
            ],
        }

    def _compute_statistical_metrics(self, data: Any) -> List[Metric]:
        """Compute statistical metrics."""
        metrics = []

        if (
            isinstance(data, list)
            and data
            and all(isinstance(x, (int, float)) for x in data)
        ):
            # Numerical data statistics
            metrics.append(Metric("count", len(data), category="basic"))
            metrics.append(Metric("mean", statistics.mean(data), category="central"))
            metrics.append(
                Metric("median", statistics.median(data), category="central")
            )
            metrics.append(Metric("min", min(data), category="range"))
            metrics.append(Metric("max", max(data), category="range"))

            if len(data) > 1:
                metrics.append(
                    Metric("stdev", statistics.stdev(data), category="dispersion")
                )
                metrics.append(
                    Metric("variance", statistics.variance(data), category="dispersion")
                )

            # Quartiles
            if len(data) >= 4:
                sorted_data = sorted(data)
                q1_idx = len(data) // 4
                q3_idx = 3 * len(data) // 4
                metrics.append(Metric("q1", sorted_data[q1_idx], category="quartiles"))
                metrics.append(Metric("q3", sorted_data[q3_idx], category="quartiles"))
                metrics.append(
                    Metric(
                        "iqr",
                        sorted_data[q3_idx] - sorted_data[q1_idx],
                        category="quartiles",
                    )
                )

        elif isinstance(data, dict):
            # Dictionary statistics
            metrics.append(Metric("keys_count", len(data), category="basic"))
            metrics.append(
                Metric("total_size", len(str(data)), unit="bytes", category="size")
            )

            # Value type distribution
            type_counts = {}
            for value in data.values():
                t = type(value).__name__
                type_counts[t] = type_counts.get(t, 0) + 1

            for t, count in type_counts.items():
                metrics.append(Metric(f"type_{t}_count", count, category="types"))

        elif isinstance(data, str):
            # String statistics
            metrics.append(Metric("length", len(data), unit="chars", category="basic"))
            metrics.append(Metric("lines", data.count("\n") + 1, category="structure"))
            metrics.append(Metric("words", len(data.split()), category="structure"))
            metrics.append(Metric("unique_chars", len(set(data)), category="diversity"))

        else:
            # Generic metrics
            metrics.append(Metric("type", type(data).__name__, category="basic"))
            metrics.append(
                Metric("size", len(str(data)), unit="bytes", category="size")
            )

        return metrics

    def _analyze_structure(self, data: Any) -> List[Metric]:
        """Analyze data structure."""
        metrics = []

        if isinstance(data, (list, tuple)):
            metrics.append(Metric("type", "sequence", category="structure"))
            metrics.append(Metric("length", len(data), category="structure"))
            metrics.append(
                Metric("depth", self._calculate_depth(data), category="structure")
            )
            metrics.append(
                Metric("homogeneous", self._is_homogeneous(data), category="structure")
            )

        elif isinstance(data, dict):
            metrics.append(Metric("type", "mapping", category="structure"))
            metrics.append(Metric("keys", len(data), category="structure"))
            metrics.append(
                Metric("depth", self._calculate_depth(data), category="structure")
            )
            metrics.append(
                Metric(
                    "nested_dicts", self._count_nested_dicts(data), category="structure"
                )
            )

        elif isinstance(data, set):
            metrics.append(Metric("type", "set", category="structure"))
            metrics.append(Metric("size", len(data), category="structure"))
            metrics.append(
                Metric(
                    "unique_types",
                    len(set(type(x).__name__ for x in data)),
                    category="structure",
                )
            )

        return metrics

    def _analyze_behavior(self, data: Any) -> List[Metric]:
        """Analyze behavioral characteristics."""
        metrics = []

        # Analyze mutability
        metrics.append(
            Metric("mutable", isinstance(data, (list, dict, set)), category="behavior")
        )

        # Analyze access patterns
        if isinstance(data, (list, tuple)):
            metrics.append(Metric("sequential_access", True, category="behavior"))
            metrics.append(Metric("random_access", True, category="behavior"))
        elif isinstance(data, dict):
            metrics.append(Metric("key_access", True, category="behavior"))
            metrics.append(Metric("ordered", True, category="behavior"))  # Python 3.7+

        # Analyze growth patterns
        if isinstance(data, (list, dict, set)):
            metrics.append(Metric("growable", True, category="behavior"))
            metrics.append(Metric("shrinkable", True, category="behavior"))

        return metrics

    def _analyze_performance(self, data: Any) -> List[Metric]:
        """Analyze performance characteristics."""
        metrics = []

        # Memory usage estimation
        size_bytes = self._estimate_memory_usage(data)
        metrics.append(
            Metric("memory_usage", size_bytes, unit="bytes", category="performance")
        )

        # Access complexity
        if isinstance(data, list):
            metrics.append(Metric("access_complexity", "O(1)", category="performance"))
            metrics.append(Metric("search_complexity", "O(n)", category="performance"))
        elif isinstance(data, dict):
            metrics.append(Metric("access_complexity", "O(1)", category="performance"))
            metrics.append(Metric("search_complexity", "O(1)", category="performance"))
        elif isinstance(data, set):
            metrics.append(
                Metric("contains_complexity", "O(1)", category="performance")
            )
            metrics.append(Metric("add_complexity", "O(1)", category="performance"))

        return metrics

    def _general_analysis(self, data: Any) -> List[Metric]:
        """Perform general analysis."""
        metrics = []

        # Combine multiple analysis types
        metrics.extend(self._compute_statistical_metrics(data))
        metrics.extend(self._analyze_structure(data))

        return metrics

    def _detect_data_patterns(self, data: Any, depth: InsightLevel) -> List[Pattern]:
        """Detect patterns in data."""
        patterns = []

        if isinstance(data, list):
            # Detect sequences
            if self._is_arithmetic_sequence(data):
                self._pattern_counter += 1
                patterns.append(
                    Pattern(
                        id=f"pattern_{self._pattern_counter}",
                        type="arithmetic_sequence",
                        occurrences=1,
                        confidence=0.95,
                        description="Arithmetic progression detected",
                    )
                )

            # Detect repetitions
            repetitions = self._find_repetitions(data)
            for item, count in repetitions.items():
                if count > 1:
                    self._pattern_counter += 1
                    patterns.append(
                        Pattern(
                            id=f"pattern_{self._pattern_counter}",
                            type="repetition",
                            occurrences=count,
                            confidence=1.0,
                            description=f"Value '{item}' repeats {count} times",
                        )
                    )

        elif isinstance(data, dict):
            # Detect key patterns
            key_pattern = self._analyze_key_pattern(list(data.keys()))
            if key_pattern:
                self._pattern_counter += 1
                patterns.append(
                    Pattern(
                        id=f"pattern_{self._pattern_counter}",
                        type="key_pattern",
                        occurrences=len(data),
                        confidence=0.8,
                        description=key_pattern,
                    )
                )

        elif isinstance(data, str):
            # Detect string patterns
            if self._is_json_like(data):
                self._pattern_counter += 1
                patterns.append(
                    Pattern(
                        id=f"pattern_{self._pattern_counter}",
                        type="json_structure",
                        occurrences=1,
                        confidence=0.9,
                        description="JSON-like structure detected",
                    )
                )

        return patterns

    def _create_insights(
        self, metrics: List[Metric], patterns: List[Pattern], depth: InsightLevel
    ) -> List[Insight]:
        """Create insights from metrics and patterns."""
        insights = []

        # Analyze metrics for insights
        for metric in metrics:
            if metric.name == "stdev" and metric.value is not None:
                if metric.value < 1:
                    self._insight_counter += 1
                    insights.append(
                        Insight(
                            id=f"insight_{self._insight_counter}",
                            level=InsightLevel.MODERATE,
                            category="distribution",
                            title="Low variance detected",
                            description="Data shows low variability, indicating consistency",
                            evidence=[metric.to_dict()],
                            confidence=0.85,
                            actionable=True,
                            recommendations=[
                                "Consider if low variance is expected",
                                "May indicate stable system",
                            ],
                        )
                    )

        # Analyze patterns for insights
        for pattern in patterns:
            if pattern.type == "repetition" and pattern.occurrences > 5:
                self._insight_counter += 1
                insights.append(
                    Insight(
                        id=f"insight_{self._insight_counter}",
                        level=InsightLevel.SURFACE,
                        category="redundancy",
                        title="High repetition detected",
                        description=f"Pattern repeats {pattern.occurrences} times",
                        evidence=[pattern.to_dict()],
                        confidence=0.9,
                        actionable=True,
                        recommendations=[
                            "Consider data deduplication",
                            "Investigate source of repetition",
                        ],
                    )
                )

        # Deep insights based on depth level
        if depth in [InsightLevel.DEEP, InsightLevel.EXPERT]:
            # Add more sophisticated insights
            if metrics and patterns:
                self._insight_counter += 1
                insights.append(
                    Insight(
                        id=f"insight_{self._insight_counter}",
                        level=InsightLevel.DEEP,
                        category="correlation",
                        title="Multi-dimensional analysis",
                        description="Combined metric and pattern analysis reveals structure",
                        evidence=[m.to_dict() for m in metrics[:3]],
                        confidence=0.75,
                        actionable=False,
                    )
                )

        return insights

    def _generate_summary(
        self, metrics: List[Metric], patterns: List[Pattern], insights: List[Insight]
    ) -> str:
        """Generate analysis summary."""
        parts = []

        parts.append(f"Analysis identified {len(metrics)} metrics")

        if patterns:
            parts.append(f"{len(patterns)} patterns detected")

        if insights:
            actionable = sum(1 for i in insights if i.actionable)
            parts.append(f"{len(insights)} insights ({actionable} actionable)")

        return ". ".join(parts) + "."

    def _statistical_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical analysis."""
        data = task.get("data")

        if data is None:
            return {"error": "Data is required"}

        metrics = self._compute_statistical_metrics(data)

        return {
            "metrics": [m.to_dict() for m in metrics],
            "summary": f"Computed {len(metrics)} statistical metrics",
        }

    def _structural_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform structural analysis."""
        data = task.get("data")

        if data is None:
            return {"error": "Data is required"}

        metrics = self._analyze_structure(data)

        return {
            "metrics": [m.to_dict() for m in metrics],
            "structure_type": type(data).__name__,
        }

    def _behavioral_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform behavioral analysis."""
        data = task.get("data")

        if data is None:
            return {"error": "Data is required"}

        metrics = self._analyze_behavior(data)

        return {
            "metrics": [m.to_dict() for m in metrics],
            "behavior_profile": "dynamic"
            if isinstance(data, (list, dict, set))
            else "static",
        }

    def _performance_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform performance analysis."""
        data = task.get("data")

        if data is None:
            return {"error": "Data is required"}

        metrics = self._analyze_performance(data)

        return {
            "metrics": [m.to_dict() for m in metrics],
            "performance_class": self._classify_performance(metrics),
        }

    def _comparative_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comparative analysis."""
        data1 = task.get("data1")
        data2 = task.get("data2")

        if data1 is None or data2 is None:
            return {"error": "Both data1 and data2 are required"}

        # Compare structures
        comparison = {
            "type_match": type(data1) == type(data2),
            "size_diff": len(str(data1)) - len(str(data2)),
            "similarities": [],
            "differences": [],
        }

        # Find similarities and differences
        if isinstance(data1, dict) and isinstance(data2, dict):
            keys1 = set(data1.keys())
            keys2 = set(data2.keys())
            comparison["similarities"] = list(keys1 & keys2)
            comparison["differences"] = list(keys1 ^ keys2)

        return {"comparison": comparison}

    def _detect_patterns(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Detect patterns in data."""
        data = task.get("data")

        if data is None:
            return {"error": "Data is required"}

        patterns = self._detect_data_patterns(data, InsightLevel.DEEP)

        return {
            "patterns": [p.to_dict() for p in patterns],
            "pattern_count": len(patterns),
        }

    def _generate_insights(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from analysis."""
        metrics_data = task.get("metrics", [])
        patterns_data = task.get("patterns", [])
        depth = task.get("depth", "moderate")

        # Convert to objects
        metrics = [Metric(**m) if isinstance(m, dict) else m for m in metrics_data]
        patterns = [Pattern(**p) if isinstance(p, dict) else p for p in patterns_data]
        depth_enum = InsightLevel[depth.upper()]

        insights = self._create_insights(metrics, patterns, depth_enum)

        return {
            "insights": [i.to_dict() for i in insights],
            "actionable_count": sum(1 for i in insights if i.actionable),
        }

    def _predictive_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform predictive analysis."""
        data = task.get("data")
        horizon = task.get("horizon", 5)

        if data is None:
            return {"error": "Data is required"}

        predictions = []

        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            # Simple trend prediction
            if len(data) >= 2:
                trend = (data[-1] - data[0]) / len(data)
                for i in range(horizon):
                    predictions.append(data[-1] + trend * (i + 1))

        return {
            "predictions": predictions,
            "horizon": horizon,
            "method": "linear_trend",
        }

    # Helper methods
    def _calculate_depth(self, data: Any, current_depth: int = 0) -> int:
        """Calculate structure depth."""
        if not isinstance(data, (list, dict, tuple)):
            return current_depth

        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(
                self._calculate_depth(v, current_depth + 1) for v in data.values()
            )
        else:
            if not data:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in data)

    def _is_homogeneous(self, data: List[Any]) -> bool:
        """Check if list contains same type."""
        if not data:
            return True
        first_type = type(data[0])
        return all(type(item) == first_type for item in data)

    def _count_nested_dicts(self, data: Dict[str, Any]) -> int:
        """Count nested dictionaries."""
        count = 0
        for value in data.values():
            if isinstance(value, dict):
                count += 1 + self._count_nested_dicts(value)
        return count

    def _estimate_memory_usage(self, data: Any) -> int:
        """Estimate memory usage in bytes."""
        # Simplified estimation
        if isinstance(data, (int, float)):
            return 8
        elif isinstance(data, str):
            return len(data)
        elif isinstance(data, (list, tuple)):
            return sum(self._estimate_memory_usage(item) for item in data) + 8 * len(
                data
            )
        elif isinstance(data, dict):
            return sum(
                self._estimate_memory_usage(k) + self._estimate_memory_usage(v)
                for k, v in data.items()
            ) + 16 * len(data)
        else:
            return len(str(data))

    def _is_arithmetic_sequence(self, data: List[Any]) -> bool:
        """Check if list is arithmetic sequence."""
        if not isinstance(data, list) or len(data) < 3:
            return False

        if not all(isinstance(x, (int, float)) for x in data):
            return False

        diff = data[1] - data[0]
        return all(data[i] - data[i - 1] == diff for i in range(2, len(data)))

    def _find_repetitions(self, data: List[Any]) -> Dict[str, int]:
        """Find repeated values."""
        counts = {}
        for item in data:
            key = str(item)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _analyze_key_pattern(self, keys: List[str]) -> Optional[str]:
        """Analyze pattern in dictionary keys."""
        if not keys:
            return None

        # Check for common prefixes
        if all(k.startswith(keys[0][:3]) for k in keys if len(k) >= 3):
            return f"Common prefix: {keys[0][:3]}"

        # Check for common suffixes
        if all(k.endswith(keys[0][-3:]) for k in keys if len(k) >= 3):
            return f"Common suffix: {keys[0][-3:]}"

        return None

    def _is_json_like(self, data: str) -> bool:
        """Check if string looks like JSON."""
        data = data.strip()
        return (data.startswith("{") and data.endswith("}")) or (
            data.startswith("[") and data.endswith("]")
        )

    def _classify_performance(self, metrics: List[Metric]) -> str:
        """Classify performance based on metrics."""
        for metric in metrics:
            if metric.name == "memory_usage":
                if metric.value < 1000:
                    return "lightweight"
                elif metric.value < 1000000:
                    return "moderate"
                else:
                    return "heavyweight"
        return "unknown"

    def shutdown(self) -> bool:
        """Shutdown the analysis agent."""
        logger.info(
            "analysis_agent_shutdown",
            reports_count=len(self.reports),
            patterns_count=len(self.patterns_db),
        )
        self.reports.clear()
        self.metrics_cache.clear()
        self.patterns_db.clear()
        return True
