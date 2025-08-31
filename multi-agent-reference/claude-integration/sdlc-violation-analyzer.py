#!/usr/bin/env python3
"""
SDLC Violation Analyzer
Detects and analyzes SDLC process violations to improve compliance
Part of SDLC Enhancement Suite
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ViolationType(Enum):
    """Types of SDLC violations."""

    SKIPPED_TOOL = "skipped_tool"
    MISSING_ARTIFACT = "missing_artifact"
    SHORTCUT_TAKEN = "shortcut_taken"
    INCOMPLETE_PHASE = "incomplete_phase"
    OUT_OF_ORDER = "out_of_order"
    MISSING_TESTS = "missing_tests"
    NO_DOCUMENTATION = "no_documentation"
    IGNORED_GATE = "ignored_gate"


class ViolationSeverity(Enum):
    """Severity levels for violations."""

    CRITICAL = "critical"  # Must fix, blocks completion
    MAJOR = "major"  # Should fix, impacts quality
    MINOR = "minor"  # Nice to fix, best practice


@dataclass
class Violation:
    """Represents a single SDLC violation."""

    phase: str
    type: ViolationType
    severity: ViolationSeverity
    description: str
    impact: str
    prevention: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["type"] = self.type.value
        result["severity"] = self.severity.value
        return result


@dataclass
class ViolationReport:
    """Complete violation analysis report."""

    project: str
    analyzed_at: str
    violations: List[Violation]
    compliance_score: float
    recommendations: List[str]
    phase_compliance: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project": self.project,
            "analyzed_at": self.analyzed_at,
            "violations": [v.to_dict() for v in self.violations],
            "compliance_score": self.compliance_score,
            "recommendations": self.recommendations,
            "phase_compliance": self.phase_compliance,
        }


class ViolationAnalyzer:
    """Main analyzer class for SDLC violations."""

    REQUIRED_ARTIFACTS = {
        "discovery": ["docs/1-requirements.md", ".sdlc/discovery-complete.json"],
        "design": ["docs/2-design.md", ".sdlc/design-complete.json"],
        "planning": ["docs/3-planning.md", ".sdlc/planning-complete.json"],
        "development": [".sdlc/development-complete.json"],
        "testing": [".sdlc/testing-complete.json"],
        "deployment": [".sdlc/deployment-complete.json"],
        "production": [".sdlc/production-complete.json"],
    }

    REQUIRED_TOOLS = {
        "discovery": ["knowledge_query", "resource_discovery", "web_search"],
        "design": ["architecture_diagram"],
        "planning": ["task_breakdown", "todo_list"],
        "development": ["version_control", "testing"],
        "testing": ["unit_tests", "integration_tests"],
        "deployment": ["ci_cd", "monitoring"],
        "production": ["documentation", "handover"],
    }

    def __init__(self, project_path: Path):
        """Initialize analyzer with project path."""
        self.project_path = project_path
        self.violations: List[Violation] = []
        self.phase_scores: Dict[str, float] = {}

    def scan_project(self) -> ViolationReport:
        """Perform complete project scan for violations."""
        print(f"🔍 Scanning project: {self.project_path}")

        # Check each phase
        for phase in self.REQUIRED_ARTIFACTS.keys():
            self._check_phase(phase)

        # Check additional patterns
        self._check_testing_violations()
        self._check_documentation_violations()
        self._check_process_order()

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Create report
        report = ViolationReport(
            project=str(self.project_path),
            analyzed_at=datetime.now().isoformat(),
            violations=self.violations,
            compliance_score=compliance_score,
            recommendations=recommendations,
            phase_compliance=self.phase_scores,
        )

        return report

    def _check_phase(self, phase: str) -> None:
        """Check violations for a specific phase."""
        phase_violations = 0
        phase_checks = 0

        # Check required artifacts
        for artifact in self.REQUIRED_ARTIFACTS.get(phase, []):
            phase_checks += 1
            artifact_path = self.project_path / artifact
            if not artifact_path.exists():
                phase_violations += 1
                self.violations.append(
                    Violation(
                        phase=phase,
                        type=ViolationType.MISSING_ARTIFACT,
                        severity=ViolationSeverity.MAJOR,
                        description=f"Missing required artifact: {artifact}",
                        impact="Phase completion cannot be verified",
                        prevention=f"Create {artifact} before completing {phase} phase",
                        file_path=str(artifact_path),
                    )
                )

        # Check gate file content if it exists
        gate_file = self.project_path / ".sdlc" / f"{phase}-complete.json"
        if gate_file.exists():
            phase_checks += 1
            if not self._validate_gate_content(gate_file, phase):
                phase_violations += 1

        # Calculate phase compliance
        if phase_checks > 0:
            self.phase_scores[phase] = 1.0 - (phase_violations / phase_checks)
        else:
            self.phase_scores[phase] = 0.0

    def _validate_gate_content(self, gate_file: Path, phase: str) -> bool:
        """Validate the content of a gate file."""
        try:
            with open(gate_file) as f:
                gate_data = json.load(f)

            # Check for required tools usage
            if "tools_used" in gate_data:
                required_tools = set(self.REQUIRED_TOOLS.get(phase, []))
                used_tools = set(gate_data.get("tools_used", []))
                missing_tools = required_tools - used_tools

                for tool in missing_tools:
                    self.violations.append(
                        Violation(
                            phase=phase,
                            type=ViolationType.SKIPPED_TOOL,
                            severity=ViolationSeverity.MINOR,
                            description=f"Required tool not used: {tool}",
                            impact="May have missed important insights or validation",
                            prevention=f"Use {tool} tool during {phase} phase",
                            file_path=str(gate_file),
                        )
                    )

            return len(self.violations) == 0

        except (json.JSONDecodeError, KeyError) as e:
            self.violations.append(
                Violation(
                    phase=phase,
                    type=ViolationType.MISSING_ARTIFACT,
                    severity=ViolationSeverity.MAJOR,
                    description=f"Invalid gate file format: {e}",
                    impact="Cannot validate phase completion",
                    prevention="Ensure gate file contains valid JSON with required fields",
                    file_path=str(gate_file),
                )
            )
            return False

    def _check_testing_violations(self) -> None:
        """Check for testing-related violations."""
        # Check for test files
        test_dirs = ["tests", "test", "spec"]
        has_tests = any((self.project_path / d).exists() for d in test_dirs)

        if not has_tests:
            # Check for test files in subdirectories
            test_files = (
                list(self.project_path.glob("**/test_*.py"))
                + list(self.project_path.glob("**/*_test.py"))
                + list(self.project_path.glob("**/*.test.js"))
                + list(self.project_path.glob("**/*.spec.js"))
            )

            if not test_files:
                self.violations.append(
                    Violation(
                        phase="testing",
                        type=ViolationType.MISSING_TESTS,
                        severity=ViolationSeverity.CRITICAL,
                        description="No test files found in project",
                        impact="Code quality and reliability cannot be verified",
                        prevention="Create comprehensive test suite with >80% coverage",
                    )
                )

    def _check_documentation_violations(self) -> None:
        """Check for documentation-related violations."""
        docs_dir = self.project_path / "docs"
        readme = self.project_path / "README.md"

        if not docs_dir.exists():
            self.violations.append(
                Violation(
                    phase="production",
                    type=ViolationType.NO_DOCUMENTATION,
                    severity=ViolationSeverity.MAJOR,
                    description="Missing docs directory",
                    impact="Project documentation not organized",
                    prevention="Create docs/ directory with all phase documentation",
                )
            )

        if not readme.exists():
            self.violations.append(
                Violation(
                    phase="production",
                    type=ViolationType.NO_DOCUMENTATION,
                    severity=ViolationSeverity.MAJOR,
                    description="Missing README.md",
                    impact="Project lacks basic documentation",
                    prevention="Create comprehensive README.md with usage instructions",
                )
            )

    def _check_process_order(self) -> None:
        """Check if phases were completed in correct order."""
        sdlc_dir = self.project_path / ".sdlc"
        if not sdlc_dir.exists():
            return

        phase_order = [
            "discovery",
            "design",
            "planning",
            "development",
            "testing",
            "deployment",
            "production",
        ]
        phase_timestamps = {}

        for phase in phase_order:
            gate_file = sdlc_dir / f"{phase}-complete.json"
            if gate_file.exists():
                try:
                    with open(gate_file) as f:
                        data = json.load(f)
                        if "completed" in data:
                            phase_timestamps[phase] = data["completed"]
                except (json.JSONDecodeError, KeyError):
                    pass

        # Check order
        prev_time = None
        prev_phase = None
        for phase in phase_order:
            if phase in phase_timestamps:
                curr_time = phase_timestamps[phase]
                if prev_time and curr_time < prev_time:
                    self.violations.append(
                        Violation(
                            phase=phase,
                            type=ViolationType.OUT_OF_ORDER,
                            severity=ViolationSeverity.MAJOR,
                            description=f"Phase {phase} completed before {prev_phase}",
                            impact="SDLC process not followed correctly",
                            prevention="Complete phases in sequential order",
                        )
                    )
                prev_time = curr_time
                prev_phase = phase

    def _calculate_compliance_score(self) -> float:
        """Calculate overall compliance score."""
        if not self.violations:
            return 1.0

        # Weight violations by severity
        weights = {
            ViolationSeverity.CRITICAL: 0.3,
            ViolationSeverity.MAJOR: 0.2,
            ViolationSeverity.MINOR: 0.1,
        }

        total_penalty = sum(weights[v.severity] for v in self.violations)
        max_penalty = len(self.violations) * weights[ViolationSeverity.CRITICAL]

        # Normalize to 0-1 scale
        if max_penalty > 0:
            score = max(0, 1 - (total_penalty / max_penalty))
        else:
            score = 1.0

        return round(score, 2)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []

        # Group violations by type
        violation_types = {}
        for v in self.violations:
            if v.type not in violation_types:
                violation_types[v.type] = []
            violation_types[v.type].append(v)

        # Generate type-specific recommendations
        if ViolationType.MISSING_ARTIFACT in violation_types:
            recommendations.append(
                "Create all required artifacts for each phase before proceeding"
            )

        if ViolationType.SKIPPED_TOOL in violation_types:
            recommendations.append(
                "Use all required tools to ensure thorough analysis and validation"
            )

        if ViolationType.MISSING_TESTS in violation_types:
            recommendations.append(
                "Implement comprehensive test suite with >80% code coverage"
            )

        if ViolationType.NO_DOCUMENTATION in violation_types:
            recommendations.append(
                "Create complete documentation including README and API docs"
            )

        if ViolationType.OUT_OF_ORDER in violation_types:
            recommendations.append(
                "Follow SDLC phases in sequential order to ensure proper foundation"
            )

        # Add general recommendations based on compliance score
        if self.phase_scores:
            avg_score = sum(self.phase_scores.values()) / len(self.phase_scores)
            if avg_score < 0.5:
                recommendations.append(
                    "Consider SDLC training or review sessions to improve process adherence"
                )
            elif avg_score < 0.8:
                recommendations.append(
                    "Focus on completing all phase requirements before moving forward"
                )

        return recommendations

    def analyze_patterns(self) -> List[Dict[str, Any]]:
        """Analyze violation patterns for insights."""
        patterns = []

        # Phase-specific patterns
        phase_violations = {}
        for v in self.violations:
            if v.phase not in phase_violations:
                phase_violations[v.phase] = 0
            phase_violations[v.phase] += 1

        if phase_violations:
            most_violated = max(phase_violations, key=phase_violations.get)
            patterns.append(
                {
                    "type": "phase_focus",
                    "description": (
                        f"Phase '{most_violated}' has most violations "
                        f"({phase_violations[most_violated]})"
                    ),
                    "action": (
                        f"Provide additional training or tooling "
                        f"for {most_violated} phase"
                    ),
                }
            )

        # Severity patterns
        severity_counts = {s: 0 for s in ViolationSeverity}
        for v in self.violations:
            severity_counts[v.severity] += 1

        if severity_counts[ViolationSeverity.CRITICAL] > 2:
            patterns.append(
                {
                    "type": "critical_issues",
                    "description": (
                        f"Multiple critical violations "
                        f"({severity_counts[ViolationSeverity.CRITICAL]})"
                    ),
                    "action": (
                        "Address critical violations immediately " "before proceeding"
                    ),
                }
            )

        return patterns

    def suggest_improvements(self) -> List[Dict[str, str]]:
        """Suggest specific improvements for the SDLC process."""
        improvements = []

        # Check for systematic issues
        if len(self.violations) > 10:
            improvements.append(
                {
                    "area": "Process",
                    "suggestion": "Implement automated SDLC validation checks",
                    "priority": "High",
                }
            )

        # Check for repeated violation types
        type_counts = {}
        for v in self.violations:
            if v.type not in type_counts:
                type_counts[v.type] = 0
            type_counts[v.type] += 1

        for vtype, count in type_counts.items():
            if count > 3:
                improvements.append(
                    {
                        "area": vtype.value,
                        "suggestion": f"Create checklist or automation for {vtype.value}",
                        "priority": "Medium",
                    }
                )

        return improvements


def print_report(report: ViolationReport) -> None:
    """Print formatted violation report."""
    print("\n" + "=" * 60)
    print("SDLC VIOLATION ANALYSIS REPORT")
    print("=" * 60)
    print(f"Project: {report.project}")
    print(f"Analyzed: {report.analyzed_at}")
    print(f"Compliance Score: {report.compliance_score:.0%}")
    print()

    # Phase compliance
    print("Phase Compliance:")
    for phase, score in report.phase_compliance.items():
        bar = "█" * int(score * 20) + "░" * int((1 - score) * 20)
        print(f"  {phase:12} [{bar}] {score:.0%}")
    print()

    # Violations by severity
    severity_counts = {s: 0 for s in ViolationSeverity}
    for v in report.violations:
        severity_counts[v.severity] += 1

    print("Violations by Severity:")
    for severity, count in severity_counts.items():
        if count > 0:
            print(f"  {severity.value:8}: {count}")
    print()

    # Detailed violations
    if report.violations:
        print("Detailed Violations:")
        for i, v in enumerate(report.violations, 1):
            print(f"\n  {i}. [{v.severity.value.upper()}] {v.description}")
            print(f"     Phase: {v.phase}")
            print(f"     Impact: {v.impact}")
            print(f"     Prevention: {v.prevention}")
    else:
        print("✅ No violations detected!")
    print()

    # Recommendations
    if report.recommendations:
        print("Recommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python sdlc-violation-analyzer.py <project-path>")
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)

    # Create analyzer
    analyzer = ViolationAnalyzer(project_path)

    # Run analysis
    report = analyzer.scan_project()

    # Print report
    print_report(report)

    # Save report to file
    report_file = project_path / ".sdlc" / "violation-report.json"
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(report.to_dict(), f, indent=2)
    print(f"Report saved to: {report_file}")

    # Exit with non-zero if compliance is below threshold
    if report.compliance_score < 0.7:
        print("\n⚠️  Compliance score below 70% threshold!")
        sys.exit(1)


if __name__ == "__main__":
    main()
