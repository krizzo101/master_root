"""Module for extracting and analyzing code patterns across the codebase.

Identifies import, class, method, error handling, and logging patterns,
calculates frequency and consistency scores, detects rule violations, and
generates recommendations for new rules.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import statistics
from typing import Any, Dict, List

from src.tools.code_generation.o3_code_generator.auto_rules_generation.ast_analyzer import (
    FileAnalysis,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


@dataclass
class PatternGroup:
    """A group of similar patterns with statistics."""

    pattern_type: str
    pattern_signature: str
    frequency: int
    consistency_score: float
    examples: List[Any]
    violations: List[Any]
    total_occurrences: int


@dataclass
class ViolationReport:
    """Report of rule violations found in the codebase."""

    rule_name: str
    violation_type: str
    file_path: Path
    line_number: int
    description: str
    severity: str  # 'critical', 'important', 'optional'


@dataclass
class PatternAnalysis:
    """Complete pattern analysis of the codebase."""

    import_patterns: Dict[str, PatternGroup]
    class_patterns: Dict[str, PatternGroup]
    method_patterns: Dict[str, PatternGroup]
    error_handling_patterns: Dict[str, PatternGroup]
    logging_patterns: Dict[str, PatternGroup]
    violations: List[ViolationReport]
    consistency_scores: Dict[str, float]
    recommendations: List[str]


class PatternExtractor:
    """
    Extracts and analyzes patterns across the codebase.

    Identifies consistent patterns, calculates frequency and consistency scores,
    finds violations of existing rules, and generates recommendations for new rules.
    """

    def __init__(self) -> None:
        """
        Initialize the pattern extractor.

        Attributes:
            logger: O3Logger instance for logging.
            existing_rules: Mapping of rule names to descriptions for violation detection.
        """
        self.logger = get_logger()
        self.existing_rules: Dict[str, str] = {
            "absolute_imports": "All imports must use absolute paths starting with src.",
            "o3_logger_usage": "All logging must use O3Logger methods.",
            "setup_logger_required": "Main scripts must call setup_logger(LogConfig()).",
            "shared_utilities": "Use shared utility modules for common functionality.",
            "no_bare_except": "Avoid bare except statements.",
            "docstrings_required": "All classes and functions must have docstrings.",
            "type_annotations": "Use type annotations for function parameters and return values.",
        }
        self.logger.log_info("Initialized PatternExtractor")

    def extract_patterns(self, file_analyses: List[FileAnalysis]) -> PatternAnalysis:
        """
        Extract patterns from file analyses.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            PatternAnalysis: Complete pattern analysis.
        """
        self.logger.log_info(f"Extracting patterns from {len(file_analyses)} files")

        import_patterns = self._extract_import_patterns(file_analyses)
        class_patterns = self._extract_class_patterns(file_analyses)
        method_patterns = self._extract_method_patterns(file_analyses)
        error_handling_patterns = self._extract_error_handling_patterns(file_analyses)
        logging_patterns = self._extract_logging_patterns(file_analyses)
        violations = self._detect_violations(file_analyses)
        consistency_scores = self._calculate_consistency_scores(
            import_patterns,
            class_patterns,
            method_patterns,
            error_handling_patterns,
            logging_patterns,
        )
        recommendations = self._generate_recommendations(
            import_patterns,
            class_patterns,
            method_patterns,
            error_handling_patterns,
            logging_patterns,
            violations=violations,
        )

        return PatternAnalysis(
            import_patterns=import_patterns,
            class_patterns=class_patterns,
            method_patterns=method_patterns,
            error_handling_patterns=error_handling_patterns,
            logging_patterns=logging_patterns,
            violations=violations,
            consistency_scores=consistency_scores,
            recommendations=recommendations,
        )

    def _extract_import_patterns(
        self, file_analyses: List[FileAnalysis]
    ) -> Dict[str, PatternGroup]:
        """
        Extract and group import patterns.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            Mapping from pattern signature to PatternGroup.
        """
        pattern_groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"examples": [], "violations": [], "total_occurrences": 0}
        )

        for analysis in file_analyses:
            for pattern in analysis.import_patterns:
                signature = f"{pattern.import_type}:{pattern.module_name}"
                group = pattern_groups[signature]
                group["examples"].append(pattern)
                group["total_occurrences"] += 1
                if pattern.import_type == "relative":
                    group["violations"].append(pattern)

        result: Dict[str, PatternGroup] = {}
        for signature, data in pattern_groups.items():
            frequency = len(data["examples"])
            consistency_score = self._calculate_pattern_consistency(data["examples"])
            result[signature] = PatternGroup(
                pattern_type="import",
                pattern_signature=signature,
                frequency=frequency,
                consistency_score=consistency_score,
                examples=data["examples"],
                violations=data["violations"],
                total_occurrences=data["total_occurrences"],
            )

        return result

    def _extract_class_patterns(
        self, file_analyses: List[FileAnalysis]
    ) -> Dict[str, PatternGroup]:
        """
        Extract and group class patterns.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            Mapping from pattern signature to PatternGroup.
        """
        pattern_groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"examples": [], "violations": [], "total_occurrences": 0}
        )

        for analysis in file_analyses:
            for pattern in analysis.class_patterns:
                signature = f"class:{pattern.has_docstring}:{pattern.has_init}:{pattern.method_count}"
                group = pattern_groups[signature]
                group["examples"].append(pattern)
                group["total_occurrences"] += 1
                if not pattern.has_docstring:
                    group["violations"].append(pattern)

        result: Dict[str, PatternGroup] = {}
        for signature, data in pattern_groups.items():
            frequency = len(data["examples"])
            consistency_score = self._calculate_pattern_consistency(data["examples"])
            result[signature] = PatternGroup(
                pattern_type="class",
                pattern_signature=signature,
                frequency=frequency,
                consistency_score=consistency_score,
                examples=data["examples"],
                violations=data["violations"],
                total_occurrences=data["total_occurrences"],
            )

        return result

    def _extract_method_patterns(
        self, file_analyses: List[FileAnalysis]
    ) -> Dict[str, PatternGroup]:
        """
        Extract and group method patterns.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            Mapping from pattern signature to PatternGroup.
        """
        pattern_groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"examples": [], "violations": [], "total_occurrences": 0}
        )

        for analysis in file_analyses:
            for pattern in analysis.method_patterns:
                signature = f"method:{pattern.is_static}:{pattern.has_docstring}:{pattern.parameter_count}"
                group = pattern_groups[signature]
                group["examples"].append(pattern)
                group["total_occurrences"] += 1
                if not pattern.has_docstring:
                    group["violations"].append(pattern)

        result: Dict[str, PatternGroup] = {}
        for signature, data in pattern_groups.items():
            frequency = len(data["examples"])
            consistency_score = self._calculate_pattern_consistency(data["examples"])
            result[signature] = PatternGroup(
                pattern_type="method",
                pattern_signature=signature,
                frequency=frequency,
                consistency_score=consistency_score,
                examples=data["examples"],
                violations=data["violations"],
                total_occurrences=data["total_occurrences"],
            )

        return result

    def _extract_error_handling_patterns(
        self, file_analyses: List[FileAnalysis]
    ) -> Dict[str, PatternGroup]:
        """
        Extract and group error handling patterns.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            Mapping from pattern signature to PatternGroup.
        """
        pattern_groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"examples": [], "violations": [], "total_occurrences": 0}
        )

        for analysis in file_analyses:
            for pattern in analysis.error_handling_patterns:
                signature = (
                    f"error_handling:{pattern.pattern_type}:{pattern.has_logging}"
                )
                group = pattern_groups[signature]
                group["examples"].append(pattern)
                group["total_occurrences"] += 1
                if pattern.pattern_type == "bare_except":
                    group["violations"].append(pattern)

        result: Dict[str, PatternGroup] = {}
        for signature, data in pattern_groups.items():
            frequency = len(data["examples"])
            consistency_score = self._calculate_pattern_consistency(data["examples"])
            result[signature] = PatternGroup(
                pattern_type="error_handling",
                pattern_signature=signature,
                frequency=frequency,
                consistency_score=consistency_score,
                examples=data["examples"],
                violations=data["violations"],
                total_occurrences=data["total_occurrences"],
            )

        return result

    def _extract_logging_patterns(
        self, file_analyses: List[FileAnalysis]
    ) -> Dict[str, PatternGroup]:
        """
        Extract and group logging patterns.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            Mapping from pattern signature to PatternGroup.
        """
        pattern_groups: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"examples": [], "violations": [], "total_occurrences": 0}
        )

        for analysis in file_analyses:
            for pattern in analysis.logging_patterns:
                signature = f"logging:{pattern.logger_type}:{pattern.log_level}"
                group = pattern_groups[signature]
                group["examples"].append(pattern)
                group["total_occurrences"] += 1
                if pattern.logger_type == "print":
                    group["violations"].append(pattern)

        result: Dict[str, PatternGroup] = {}
        for signature, data in pattern_groups.items():
            frequency = len(data["examples"])
            consistency_score = self._calculate_pattern_consistency(data["examples"])
            result[signature] = PatternGroup(
                pattern_type="logging",
                pattern_signature=signature,
                frequency=frequency,
                consistency_score=consistency_score,
                examples=data["examples"],
                violations=data["violations"],
                total_occurrences=data["total_occurrences"],
            )

        return result

    def _detect_violations(
        self, file_analyses: List[FileAnalysis]
    ) -> List[ViolationReport]:
        """
        Detect violations of existing rules.

        Args:
            file_analyses: List of file analysis results.

        Returns:
            List of ViolationReport instances.
        """
        violations: List[ViolationReport] = []

        for analysis in file_analyses:
            for pattern in analysis.import_patterns:
                if pattern.import_type == "relative":
                    violations.append(
                        ViolationReport(
                            rule_name="absolute_imports",
                            violation_type="relative_import",
                            file_path=analysis.file_path,
                            line_number=pattern.line_number,
                            description=f"Relative import found: {pattern.import_statement}",
                            severity="critical",
                        )
                    )
            for pattern in analysis.logging_patterns:
                if pattern.logger_type == "print":
                    violations.append(
                        ViolationReport(
                            rule_name="o3_logger_usage",
                            violation_type="print_statement",
                            file_path=analysis.file_path,
                            line_number=pattern.line_number,
                            description="Print statement found instead of O3Logger",
                            severity="important",
                        )
                    )
            if analysis.has_main_function and not analysis.has_setup_logger:
                violations.append(
                    ViolationReport(
                        rule_name="setup_logger_required",
                        violation_type="missing_setup_logger",
                        file_path=analysis.file_path,
                        line_number=1,
                        description="Main script missing setup_logger(LogConfig()) call",
                        severity="critical",
                    )
                )
            for pattern in analysis.error_handling_patterns:
                if pattern.pattern_type == "bare_except":
                    violations.append(
                        ViolationReport(
                            rule_name="no_bare_except",
                            violation_type="bare_except",
                            file_path=analysis.file_path,
                            line_number=pattern.line_number,
                            description="Bare except statement found",
                            severity="important",
                        )
                    )
            for pattern in analysis.class_patterns:
                if not pattern.has_docstring:
                    violations.append(
                        ViolationReport(
                            rule_name="docstrings_required",
                            violation_type="missing_class_docstring",
                            file_path=analysis.file_path,
                            line_number=pattern.line_number,
                            description=f"Class '{pattern.class_name}' missing docstring",
                            severity="important",
                        )
                    )
            for pattern in analysis.method_patterns:
                if not pattern.has_docstring:
                    violations.append(
                        ViolationReport(
                            rule_name="docstrings_required",
                            violation_type="missing_method_docstring",
                            file_path=analysis.file_path,
                            line_number=pattern.line_number,
                            description=f"Method '{pattern.method_name}' missing docstring",
                            severity="important",
                        )
                    )

        return violations

    def _calculate_pattern_consistency(self, patterns: List[Any]) -> float:
        """
        Calculate consistency score for a group of patterns.

        Args:
            patterns: List of pattern instances.

        Returns:
            Consistency score between 0.0 and 1.0.
        """
        if not patterns:
            return 0.0
        total = len(patterns)
        unique = len(set(str(p) for p in patterns))
        if unique <= 1:
            return 1.0
        consistency = 1.0 - (unique - 1) / total
        return max(0.0, min(1.0, consistency))

    def _calculate_consistency_scores(
        self, *pattern_dicts: Dict[str, PatternGroup]
    ) -> Dict[str, float]:
        """
        Calculate overall consistency scores for different pattern types.

        Args:
            pattern_dicts: One or more mappings of pattern signatures to PatternGroup.

        Returns:
            Mapping from metric name to score.
        """
        scores: Dict[str, float] = {}
        for pattern_dict in pattern_dicts:
            if not pattern_dict:
                continue
            pattern_type = next(iter(pattern_dict.values())).pattern_type
            scores[f"{pattern_type}_consistency"] = statistics.mean(
                group.consistency_score for group in pattern_dict.values()
            )
            scores[f"{pattern_type}_frequency"] = sum(
                group.frequency for group in pattern_dict.values()
            )
        return scores

    def _generate_recommendations(
        self,
        *pattern_dicts: Dict[str, PatternGroup],
        violations: List[ViolationReport],
    ) -> list[str]:
        """
        Generate recommendations for new rules based on patterns and violations.

        Args:
            pattern_dicts: One or more mappings of pattern signatures to PatternGroup.
            violations: List of detected violations.

        Returns:
            List of recommendation strings.
        """
        recommendations: List[str] = []
        violation_counts = Counter(v.rule_name for v in violations)
        for rule_name, count in violation_counts.most_common():
            if count > 5:
                recommendations.append(
                    f"Strengthen enforcement of '{rule_name}' rule - {count} violations found"
                )
        for pattern_dict in pattern_dicts:
            if not pattern_dict:
                continue
            pattern_type = next(iter(pattern_dict.values())).pattern_type
            for group in pattern_dict.values():
                if group.frequency > 10 and group.consistency_score > 0.8:
                    recommendations.append(
                        f"Consider rule for {pattern_type} pattern: {group.pattern_signature} "
                        f"(frequency: {group.frequency}, consistency: {group.consistency_score:.2f})"
                    )
        return recommendations
