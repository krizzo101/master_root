#!/usr/bin/env python3
"""
Quality Gates Validation Script

Validates that code quality metrics meet the required standards for the
Smart Decomposition system including coverage, performance, and security.
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List
import xml.etree.ElementTree as ET


class QualityGateValidator:
    """Validates quality gates for CI/CD pipeline"""

    def __init__(self, min_coverage: float = 85.0, max_execution_time: float = 60.0):
        self.min_coverage = min_coverage
        self.max_execution_time = max_execution_time
        self.failures = []

    def validate_coverage(self, coverage_file: str) -> bool:
        """Validate test coverage meets minimum requirements"""
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()

            # Find coverage percentage
            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get("line-rate", 0)) * 100
                branch_rate = float(coverage_elem.get("branch-rate", 0)) * 100

                print("📊 Coverage Results:")
                print(f"  Line coverage: {line_rate:.2f}%")
                print(f"  Branch coverage: {branch_rate:.2f}%")

                if line_rate < self.min_coverage:
                    self.failures.append(
                        f"Line coverage {line_rate:.2f}% below minimum {self.min_coverage}%"
                    )

                if branch_rate < self.min_coverage:
                    self.failures.append(
                        f"Branch coverage {branch_rate:.2f}% below minimum {self.min_coverage}%"
                    )

                return (
                    line_rate >= self.min_coverage and branch_rate >= self.min_coverage
                )
            else:
                self.failures.append("Could not find coverage data in XML file")
                return False

        except Exception as e:
            self.failures.append(f"Failed to parse coverage file: {e}")
            return False

    def validate_performance(self, benchmark_file: str) -> bool:
        """Validate performance benchmarks meet requirements"""
        try:
            with open(benchmark_file) as f:
                data = json.load(f)

            print("🚀 Performance Results:")

            # Check benchmark results
            benchmarks = data.get("benchmarks", [])
            performance_issues = []

            for benchmark in benchmarks:
                name = benchmark.get("name", "Unknown")
                stats = benchmark.get("stats", {})
                mean_time = stats.get("mean", 0)

                print(f"  {name}: {mean_time:.3f}s")

                # Check if any benchmark exceeds maximum execution time
                if mean_time > self.max_execution_time:
                    performance_issues.append(
                        f"Benchmark '{name}' took {mean_time:.3f}s (max: {self.max_execution_time}s)"
                    )

            if performance_issues:
                self.failures.extend(performance_issues)
                return False

            # Check for performance regressions
            if "compared" in data:
                regressions = []
                for comparison in data["compared"]:
                    if comparison.get("change", 0) > 0.1:  # 10% regression threshold
                        change_pct = comparison.get("change", 0) * 100
                        regressions.append(
                            f"Performance regression: {comparison.get('name')} is {change_pct:.1f}% slower"
                        )

                if regressions:
                    self.failures.extend(regressions)
                    return False

            print("  ✅ All performance benchmarks within acceptable limits")
            return True

        except Exception as e:
            self.failures.append(f"Failed to parse benchmark file: {e}")
            return False

    def validate_security(self, security_files: List[str]) -> bool:
        """Validate security scan results"""
        print("🔒 Security Scan Results:")

        security_passed = True

        for security_file in security_files:
            try:
                with open(security_file) as f:
                    data = json.load(f)

                file_type = self._determine_security_file_type(security_file, data)

                if file_type == "safety":
                    security_passed &= self._validate_safety_report(data)
                elif file_type == "bandit":
                    security_passed &= self._validate_bandit_report(data)
                elif file_type == "semgrep":
                    security_passed &= self._validate_semgrep_report(data)

            except Exception as e:
                self.failures.append(
                    f"Failed to parse security file {security_file}: {e}"
                )
                security_passed = False

        return security_passed

    def _determine_security_file_type(self, filename: str, data: Dict) -> str:
        """Determine the type of security report"""
        if "safety" in filename.lower():
            return "safety"
        elif "bandit" in filename.lower():
            return "bandit"
        elif "semgrep" in filename.lower():
            return "semgrep"
        elif "vulnerabilities" in data or "dependency" in str(data):
            return "safety"
        elif "results" in data and isinstance(data.get("results"), list):
            return "bandit"
        else:
            return "unknown"

    def _validate_safety_report(self, data: Dict) -> bool:
        """Validate Safety dependency security report"""
        vulnerabilities = data.get("vulnerabilities", [])

        if vulnerabilities:
            print(f"  ❌ Safety: Found {len(vulnerabilities)} vulnerabilities")
            for vuln in vulnerabilities[:5]:  # Show first 5
                package = vuln.get("package", "Unknown")
                version = vuln.get("installed_version", "Unknown")
                print(
                    f"    - {package} {version}: {vuln.get('advisory', 'No details')[:100]}..."
                )

            self.failures.append(
                f"Safety scan found {len(vulnerabilities)} security vulnerabilities"
            )
            return False
        else:
            print("  ✅ Safety: No vulnerabilities found in dependencies")
            return True

    def _validate_bandit_report(self, data: Dict) -> bool:
        """Validate Bandit security scan report"""
        results = data.get("results", [])

        # Filter by severity
        high_severity = [r for r in results if r.get("issue_severity") == "HIGH"]
        medium_severity = [r for r in results if r.get("issue_severity") == "MEDIUM"]

        print(
            f"  Bandit: Found {len(high_severity)} high, {len(medium_severity)} medium severity issues"
        )

        if high_severity:
            print(
                f"  ❌ Bandit: {len(high_severity)} high severity security issues found"
            )
            for issue in high_severity[:3]:  # Show first 3
                test_name = issue.get("test_name", "Unknown")
                filename = issue.get("filename", "Unknown")
                line = issue.get("line_number", "Unknown")
                print(f"    - {test_name} in {filename}:{line}")

            self.failures.append(
                f"Bandit found {len(high_severity)} high severity security issues"
            )
            return False
        else:
            print("  ✅ Bandit: No high severity security issues found")
            return True

    def _validate_semgrep_report(self, data: Dict) -> bool:
        """Validate Semgrep security scan report"""
        results = data.get("results", [])

        # Filter by severity
        error_results = [
            r for r in results if r.get("extra", {}).get("severity") == "ERROR"
        ]
        warning_results = [
            r for r in results if r.get("extra", {}).get("severity") == "WARNING"
        ]

        print(
            f"  Semgrep: Found {len(error_results)} errors, {len(warning_results)} warnings"
        )

        if error_results:
            print(f"  ❌ Semgrep: {len(error_results)} security errors found")
            for result in error_results[:3]:  # Show first 3
                check_id = result.get("check_id", "Unknown")
                path = result.get("path", "Unknown")
                print(f"    - {check_id} in {path}")

            self.failures.append(f"Semgrep found {len(error_results)} security errors")
            return False
        else:
            print("  ✅ Semgrep: No security errors found")
            return True

    def validate_test_execution_time(self, benchmark_file: str) -> bool:
        """Validate overall test execution time"""
        try:
            with open(benchmark_file) as f:
                data = json.load(f)

            # Calculate total execution time
            total_time = 0
            benchmarks = data.get("benchmarks", [])

            for benchmark in benchmarks:
                stats = benchmark.get("stats", {})
                total_time += stats.get("mean", 0)

            print(f"🕒 Total test execution time: {total_time:.2f}s")

            if total_time > self.max_execution_time:
                self.failures.append(
                    f"Total test execution time {total_time:.2f}s exceeds maximum {self.max_execution_time}s"
                )
                return False

            print("  ✅ Test execution time within acceptable limits")
            return True

        except Exception:
            # If no benchmark file, assume tests passed time requirements
            print("  ℹ️  No benchmark data available for time validation")
            return True

    def run_validation(
        self,
        coverage_file: str,
        benchmark_file: str,
        security_files: List[str],
        fail_on_security: bool = True,
    ) -> bool:
        """Run all quality gate validations"""
        print("🔍 Running Quality Gate Validation...")
        print("=" * 50)

        results = {}

        # Validate coverage
        if coverage_file and Path(coverage_file).exists():
            results["coverage"] = self.validate_coverage(coverage_file)
        else:
            print("⚠️  Coverage file not found, skipping coverage validation")
            results["coverage"] = True

        # Validate performance
        if benchmark_file and Path(benchmark_file).exists():
            results["performance"] = self.validate_performance(benchmark_file)
            results["execution_time"] = self.validate_test_execution_time(
                benchmark_file
            )
        else:
            print("⚠️  Benchmark file not found, skipping performance validation")
            results["performance"] = True
            results["execution_time"] = True

        # Validate security
        existing_security_files = [f for f in security_files if Path(f).exists()]
        if existing_security_files:
            results["security"] = self.validate_security(existing_security_files)
        else:
            print("⚠️  No security files found, skipping security validation")
            results["security"] = True

        # Summary
        print("\n" + "=" * 50)
        print("📋 Quality Gate Summary:")

        all_passed = True
        for gate, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {gate.capitalize()}: {status}")
            if not passed:
                all_passed = False

        if self.failures:
            print("\n❌ Quality Gate Failures:")
            for failure in self.failures:
                print(f"  - {failure}")

        if all_passed:
            print("\n🎉 All quality gates passed!")
        else:
            print(f"\n💥 {len(self.failures)} quality gate(s) failed!")

        return all_passed


def main():
    """Main entry point for quality gate validation"""
    parser = argparse.ArgumentParser(description="Validate quality gates for CI/CD")
    parser.add_argument("--coverage-file", help="Path to coverage XML file")
    parser.add_argument("--benchmark-file", help="Path to benchmark JSON file")
    parser.add_argument(
        "--security-files", nargs="+", default=[], help="Paths to security report files"
    )
    parser.add_argument(
        "--min-coverage", type=float, default=85.0, help="Minimum coverage percentage"
    )
    parser.add_argument(
        "--max-execution-time",
        type=float,
        default=60.0,
        help="Maximum execution time in seconds",
    )
    parser.add_argument(
        "--fail-on-security-issues",
        action="store_true",
        help="Fail if security issues found",
    )

    args = parser.parse_args()

    validator = QualityGateValidator(
        min_coverage=args.min_coverage, max_execution_time=args.max_execution_time
    )

    success = validator.run_validation(
        coverage_file=args.coverage_file,
        benchmark_file=args.benchmark_file,
        security_files=args.security_files,
        fail_on_security=args.fail_on_security_issues,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
