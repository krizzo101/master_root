#!/usr/bin/env python3
"""
Bulletproofing Validation System for Auto Rules Generation

This module provides comprehensive validation capabilities to ensure the
auto rules generation system is truly bulletproof before git hook integration.
"""

import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from src.tools.code_generation.o3_code_generator.auto_rules_generation.auto_rules_generator import (
    AutoRulesGenerationResult,
    AutoRulesGenerator,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


@dataclass
class ValidationMetrics:
    """Validation metrics for bulletproofing."""

    execution_time: float
    memory_usage_mb: float
    file_count: int
    rule_count: int
    safety_score: float
    quality_score: float
    success: bool


@dataclass
class ValidationResult:
    """Result of a validation test."""

    test_name: str
    passed: bool
    metrics: ValidationMetrics | None
    error_message: str | None
    details: dict[str, Any]
    timestamp: datetime


class BulletproofingValidator:
    """Comprehensive validator for bulletproofing the auto rules generation system."""

    def __init__(self):
        """Initialize the validator."""
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.validation_results: list[ValidationResult] = []
        self.performance_thresholds = {
            "max_execution_time": 30.0,  # seconds
            "max_memory_usage": 512.0,  # MB
            "max_file_count": 1000,  # files
            "min_rule_accuracy": 0.9,  # 90%
            "min_safety_score": 0.8,  # 80%
            "min_quality_score": 0.85,  # 85%
        }

    def validate_system(self, test_codebase_path: Path) -> list[ValidationResult]:
        """Run comprehensive validation tests."""
        self.logger.log_info("Starting comprehensive bulletproofing validation")

        # Performance Validation
        self.validation_results.extend(
            [
                self._validate_performance(test_codebase_path),
                self._validate_memory_usage(test_codebase_path),
                self._validate_concurrent_execution(test_codebase_path),
            ]
        )

        # Error Handling Validation
        self.validation_results.extend(
            [
                self._validate_error_handling(test_codebase_path),
                self._validate_recovery_mechanisms(test_codebase_path),
            ]
        )

        # Quality Validation
        self.validation_results.extend(
            [
                self._validate_rule_quality(test_codebase_path),
                self._validate_rule_consistency(test_codebase_path),
                self._validate_safety_checks(test_codebase_path),
            ]
        )

        # Integration Validation
        self.validation_results.extend(
            [
                self._validate_enhanced_auto_align_integration(test_codebase_path),
                self._validate_workflow_completeness(test_codebase_path),
            ]
        )

        return self.validation_results

    def _validate_performance(self, test_codebase_path: Path) -> ValidationResult:
        """Validate performance benchmarks."""
        start_time = time.time()
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            execution_time = time.time() - start_time
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            file_count = len(list(test_codebase_path.rglob("*.py")))
            rule_count = len(result.generated_rules) if result.generated_rules else 0

            # Calculate quality and safety scores
            quality_score = self._calculate_quality_score(result)
            safety_score = (
                result.validation_report.safety_score
                if result.validation_report
                else 0.0
            )

            metrics = ValidationMetrics(
                execution_time=execution_time,
                memory_usage_mb=memory_increase,
                file_count=file_count,
                rule_count=rule_count,
                safety_score=safety_score,
                quality_score=quality_score,
                success=result.success,
            )

            # Check performance thresholds
            performance_checks = {
                "execution_time": execution_time
                < self.performance_thresholds["max_execution_time"],
                "memory_usage": memory_increase
                < self.performance_thresholds["max_memory_usage"],
                "file_count": file_count
                < self.performance_thresholds["max_file_count"],
                "success": result.success,
            }

            passed = all(performance_checks.values())

            return ValidationResult(
                test_name="Performance Validation",
                passed=passed,
                metrics=metrics,
                error_message=None if passed else "Performance thresholds exceeded",
                details={"performance_checks": performance_checks},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Performance Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_memory_usage(self, test_codebase_path: Path) -> ValidationResult:
        """Validate memory usage and leak prevention."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        try:
            # Run multiple generations to test for memory leaks
            memory_readings = []

            for i in range(5):
                generator = AutoRulesGenerator(base_path=test_codebase_path)
                result = generator.generate_rules()

                if not result.success:
                    return ValidationResult(
                        test_name="Memory Usage Validation",
                        passed=False,
                        metrics=None,
                        error_message=f"Generation {i+1} failed",
                        details={"iteration": i + 1},
                        timestamp=datetime.now(),
                    )

                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_readings.append(current_memory)

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Check for memory leaks (memory should not continuously increase)
            memory_stable = all(
                abs(memory_readings[i] - memory_readings[i - 1]) < 50  # 50MB tolerance
                for i in range(1, len(memory_readings))
            )

            passed = (
                memory_increase < self.performance_thresholds["max_memory_usage"]
                and memory_stable
            )

            metrics = ValidationMetrics(
                execution_time=0.0,
                memory_usage_mb=memory_increase,
                file_count=0,
                rule_count=0,
                safety_score=0.0,
                quality_score=0.0,
                success=True,
            )

            return ValidationResult(
                test_name="Memory Usage Validation",
                passed=passed,
                metrics=metrics,
                error_message=(
                    None
                    if passed
                    else "Memory usage exceeded limits or memory leak detected"
                ),
                details={
                    "memory_increase": memory_increase,
                    "memory_readings": memory_readings,
                    "memory_stable": memory_stable,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Memory Usage Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_concurrent_execution(
        self, test_codebase_path: Path
    ) -> ValidationResult:
        """Validate concurrent execution safety."""
        try:
            results_queue = queue.Queue()

            def run_generation():
                try:
                    generator = AutoRulesGenerator(base_path=test_codebase_path)
                    result = generator.generate_rules()
                    results_queue.put(("success", result))
                except Exception as e:
                    results_queue.put(("error", str(e)))

            # Run multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=run_generation)
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Check results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())

            # All should succeed
            all_successful = all(status == "success" for status, _ in results)
            successful_count = len([r for r in results if r[0] == "success"])

            passed = all_successful

            return ValidationResult(
                test_name="Concurrent Execution Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None
                    if passed
                    else f"Only {successful_count}/{len(threads)} threads succeeded"
                ),
                details={
                    "thread_count": len(threads),
                    "successful_threads": successful_count,
                    "all_successful": all_successful,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Concurrent Execution Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_error_handling(self, test_codebase_path: Path) -> ValidationResult:
        """Validate error handling capabilities."""
        try:
            # Test with various error conditions
            error_tests = []

            # Test with malformed files
            malformed_file = test_codebase_path / "malformed.py"
            malformed_file.write_text(
                "def broken_function(\n    # Missing closing parenthesis\n"
            )
            error_tests.append(("malformed_file", malformed_file))

            # Test with empty files
            empty_file = test_codebase_path / "empty.py"
            empty_file.write_text("")
            error_tests.append(("empty_file", empty_file))

            # Test with large files
            large_content = ["def large_function():\n    pass"] * 1000
            large_file = test_codebase_path / "large.py"
            large_file.write_text("\n".join(large_content))
            error_tests.append(("large_file", large_file))

            # Run generation with error conditions
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            # Should handle errors gracefully
            passed = result.success

            # Cleanup test files
            for test_name, file_path in error_tests:
                if file_path.exists():
                    file_path.unlink()

            return ValidationResult(
                test_name="Error Handling Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None if passed else "Failed to handle error conditions gracefully"
                ),
                details={"error_tests": len(error_tests)},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Error Handling Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_recovery_mechanisms(
        self, test_codebase_path: Path
    ) -> ValidationResult:
        """Validate recovery mechanisms."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)

            # Run multiple times to test recovery
            results = []
            for i in range(3):
                result = generator.generate_rules()
                results.append(result)

                if not result.success:
                    return ValidationResult(
                        test_name="Recovery Mechanisms Validation",
                        passed=False,
                        metrics=None,
                        error_message=f"Generation {i+1} failed",
                        details={"iteration": i + 1},
                        timestamp=datetime.now(),
                    )

            # Check consistency
            all_successful = all(r.success for r in results)
            rule_counts = [len(r.generated_rules) for r in results if r.generated_rules]

            if rule_counts:
                consistency_score = (
                    min(rule_counts) / max(rule_counts) if max(rule_counts) > 0 else 0
                )
            else:
                consistency_score = 0

            passed = all_successful and consistency_score >= 0.8  # 80% consistency

            return ValidationResult(
                test_name="Recovery Mechanisms Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None
                    if passed
                    else f"Recovery failed or consistency score {consistency_score:.2f} below threshold"
                ),
                details={
                    "iterations": len(results),
                    "consistency_score": consistency_score,
                    "rule_counts": rule_counts,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Recovery Mechanisms Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_rule_quality(self, test_codebase_path: Path) -> ValidationResult:
        """Validate rule quality and accuracy."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            if not result.success or not result.generated_rules:
                return ValidationResult(
                    test_name="Rule Quality Validation",
                    passed=False,
                    metrics=None,
                    error_message="No rules generated",
                    details={},
                    timestamp=datetime.now(),
                )

            # Calculate quality metrics
            quality_metrics = {
                "rule_count": len(result.generated_rules),
                "rules_with_description": sum(
                    1 for r in result.generated_rules if "description" in r
                ),
                "rules_with_confidence": sum(
                    1 for r in result.generated_rules if "confidence" in r
                ),
                "high_confidence_rules": sum(
                    1 for r in result.generated_rules if r.get("confidence", 0) > 0.7
                ),
                "rules_with_examples": sum(
                    1 for r in result.generated_rules if "examples" in r
                ),
            }

            # Calculate quality score
            quality_score = (
                quality_metrics["rules_with_description"]
                / quality_metrics["rule_count"]
                * 0.3
                + quality_metrics["rules_with_confidence"]
                / quality_metrics["rule_count"]
                * 0.3
                + quality_metrics["high_confidence_rules"]
                / quality_metrics["rule_count"]
                * 0.3
                + quality_metrics["rules_with_examples"]
                / quality_metrics["rule_count"]
                * 0.1
            )

            passed = quality_score >= self.performance_thresholds["min_quality_score"]

            return ValidationResult(
                test_name="Rule Quality Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None
                    if passed
                    else f"Quality score {quality_score:.2f} below threshold"
                ),
                details={"quality_score": quality_score, **quality_metrics},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Rule Quality Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_rule_consistency(self, test_codebase_path: Path) -> ValidationResult:
        """Validate rule consistency across runs."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)

            # Run multiple times
            results = []
            for i in range(3):
                result = generator.generate_rules()
                results.append(result)

                if not result.success:
                    return ValidationResult(
                        test_name="Rule Consistency Validation",
                        passed=False,
                        metrics=None,
                        error_message=f"Generation {i+1} failed",
                        details={"iteration": i + 1},
                        timestamp=datetime.now(),
                    )

            # Check consistency
            rule_counts = [len(r.generated_rules) for r in results if r.generated_rules]
            if not rule_counts:
                return ValidationResult(
                    test_name="Rule Consistency Validation",
                    passed=False,
                    metrics=None,
                    error_message="No rules generated in any run",
                    details={},
                    timestamp=datetime.now(),
                )

            # Calculate consistency score
            min_count = min(rule_counts)
            max_count = max(rule_counts)
            consistency_score = min_count / max_count if max_count > 0 else 0

            passed = consistency_score >= 0.8  # 80% consistency

            return ValidationResult(
                test_name="Rule Consistency Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None
                    if passed
                    else f"Consistency score {consistency_score:.2f} below threshold"
                ),
                details={
                    "consistency_score": consistency_score,
                    "rule_counts": rule_counts,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Rule Consistency Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_safety_checks(self, test_codebase_path: Path) -> ValidationResult:
        """Validate safety checks and validation."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            if not result.validation_report:
                return ValidationResult(
                    test_name="Safety Checks Validation",
                    passed=False,
                    metrics=None,
                    error_message="No validation report generated",
                    details={},
                    timestamp=datetime.now(),
                )

            # Check safety metrics
            safety_score = result.validation_report.safety_score
            passed = safety_score >= self.performance_thresholds["min_safety_score"]

            return ValidationResult(
                test_name="Safety Checks Validation",
                passed=passed,
                metrics=None,
                error_message=(
                    None
                    if passed
                    else f"Safety score {safety_score:.2f} below threshold"
                ),
                details={"safety_score": safety_score},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Safety Checks Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_enhanced_auto_align_integration(
        self, test_codebase_path: Path
    ) -> ValidationResult:
        """Validate integration with enhanced auto-align system."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            # Check integration requirements
            integration_checks = {
                "generation_successful": result.success,
                "rules_generated": result.generated_rules is not None,
                "validation_report": result.validation_report is not None,
                "pattern_analysis": result.pattern_analysis is not None,
                "codebase_metadata": result.codebase_metadata is not None,
            }

            passed = all(integration_checks.values())

            return ValidationResult(
                test_name="Enhanced Auto-Align Integration Validation",
                passed=passed,
                metrics=None,
                error_message=None if passed else "Integration requirements not met",
                details={"integration_checks": integration_checks},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Enhanced Auto-Align Integration Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _validate_workflow_completeness(
        self, test_codebase_path: Path
    ) -> ValidationResult:
        """Validate complete workflow end-to-end."""
        try:
            generator = AutoRulesGenerator(base_path=test_codebase_path)
            result = generator.generate_rules()

            # Check complete workflow
            workflow_checks = {
                "generation_successful": result.success,
                "rules_generated": result.generated_rules is not None,
                "validation_report": result.validation_report is not None,
                "pattern_analysis": result.pattern_analysis is not None,
                "codebase_metadata": result.codebase_metadata is not None,
                "output_files_created": len(result.output_files) > 0,
                "summary_generated": bool(result.summary),
                "recommendations_provided": len(result.recommendations) > 0,
                "execution_time_recorded": isinstance(
                    result.execution_time, (int, float)
                ),
            }

            passed = all(workflow_checks.values())

            return ValidationResult(
                test_name="Workflow Completeness Validation",
                passed=passed,
                metrics=None,
                error_message=None if passed else "Workflow completeness check failed",
                details={"workflow_checks": workflow_checks},
                timestamp=datetime.now(),
            )

        except Exception as e:
            return ValidationResult(
                test_name="Workflow Completeness Validation",
                passed=False,
                metrics=None,
                error_message=str(e),
                details={},
                timestamp=datetime.now(),
            )

    def _calculate_quality_score(self, result: AutoRulesGenerationResult) -> float:
        """Calculate quality score for generated rules."""
        if not result.generated_rules:
            return 0.0

        quality_metrics = {
            "rules_with_description": sum(
                1 for r in result.generated_rules if "description" in r
            ),
            "rules_with_confidence": sum(
                1 for r in result.generated_rules if "confidence" in r
            ),
            "high_confidence_rules": sum(
                1 for r in result.generated_rules if r.get("confidence", 0) > 0.7
            ),
        }

        total_rules = len(result.generated_rules)

        quality_score = (
            quality_metrics["rules_with_description"] / total_rules * 0.4
            + quality_metrics["rules_with_confidence"] / total_rules * 0.3
            + quality_metrics["high_confidence_rules"] / total_rules * 0.3
        )

        return quality_score

    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for r in self.validation_results if r.passed)
        failed_tests = total_tests - passed_tests

        report = f"""
🛡️ BULLETPROOFING VALIDATION REPORT
{'='*60}

📊 SUMMARY:
- Total Validations: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {(passed_tests/total_tests*100):.1f}%

{'='*60}

📋 DETAILED RESULTS:
"""

        for result in self.validation_results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report += f"\n{status} {result.test_name}"
            report += (
                f"\n   - Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if result.metrics:
                report += f"\n   - Execution Time: {result.metrics.execution_time:.2f}s"
                report += f"\n   - Memory Usage: {result.metrics.memory_usage_mb:.2f}MB"
                report += f"\n   - File Count: {result.metrics.file_count}"
                report += f"\n   - Rule Count: {result.metrics.rule_count}"
                report += f"\n   - Safety Score: {result.metrics.safety_score:.2f}"
                report += f"\n   - Quality Score: {result.metrics.quality_score:.2f}"

            if result.error_message:
                report += f"\n   - Error: {result.error_message}"

            if result.details:
                report += f"\n   - Details: {result.details}"

        report += f"\n\n{'='*60}"

        if failed_tests == 0:
            report += "\n🎉 ALL VALIDATIONS PASSED - SYSTEM IS BULLETPROOF!"
            report += "\n✅ Ready for git hook integration"
        else:
            report += (
                f"\n⚠️  {failed_tests} VALIDATIONS FAILED - SYSTEM NEEDS IMPROVEMENT"
            )
            report += "\n❌ NOT ready for git hook integration"

        return report

    def is_bulletproof(self) -> bool:
        """Check if the system is bulletproof."""
        return all(result.passed for result in self.validation_results)


def validate_bulletproofing(test_codebase_path: Path) -> tuple[bool, str]:
    """Validate bulletproofing and return result with report."""
    validator = BulletproofingValidator()
    validator.validate_system(test_codebase_path)

    is_bulletproof = validator.is_bulletproof()
    report = validator.generate_validation_report()

    return is_bulletproof, report


if __name__ == "__main__":
    # Example usage
    test_path = Path("src/applications/oamat_sd")
    is_bulletproof, report = validate_bulletproofing(test_path)
    print(report)
    print(f"\nBulletproof Status: {'✅ YES' if is_bulletproof else '❌ NO'}")
