#!/usr/bin/env python3
"""
Enhanced Error Adapter Validation Script.

This script validates the complete error ingestion system by:
1. Creating realistic test error logs
2. Processing them through the enhanced error adapter
3. Validating all intelligence features work correctly
4. Generating a comprehensive report

Usage:
    python validate_enhanced_error_adapter.py [--verbose] [--output-dir PATH]
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.project_context.ingestion.adapters.enhanced_error_adapter import (
    EnhancedErrorAdapter,
    ErrorClassifier,
    ErrorDeduplicator,
    LogFormatDetector,
    PerformanceMonitor,
    StackTraceParser,
    TrendAnalyzer,
)
from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationReport:
    """Generates comprehensive validation reports."""

    def __init__(self):
        self.results = {
            "validation_time": datetime.now(),
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": [],
            "performance_metrics": {},
            "error_analysis": {},
            "recommendations": [],
        }

    def add_test_result(
        self, test_name: str, passed: bool, details: str = "", metrics: Dict = None
    ):
        """Add a test result to the report."""
        if passed:
            self.results["tests_passed"] += 1
        else:
            self.results["tests_failed"] += 1

        self.results["test_details"].append(
            {
                "test_name": test_name,
                "passed": passed,
                "details": details,
                "metrics": metrics or {},
            }
        )

    def set_performance_metrics(self, metrics: Dict):
        """Set overall performance metrics."""
        self.results["performance_metrics"] = metrics

    def set_error_analysis(self, analysis: Dict):
        """Set error analysis results."""
        self.results["error_analysis"] = analysis

    def add_recommendation(self, recommendation: str):
        """Add a recommendation to the report."""
        self.results["recommendations"].append(recommendation)

    def generate_report(self) -> str:
        """Generate a comprehensive text report."""
        report = []
        report.append("=" * 80)
        report.append("ENHANCED ERROR ADAPTER VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Validation Time: {self.results['validation_time']}")
        report.append(f"Tests Passed: {self.results['tests_passed']}")
        report.append(f"Tests Failed: {self.results['tests_failed']}")
        report.append("")

        # Test Results
        report.append("TEST RESULTS:")
        report.append("-" * 40)
        for test in self.results["test_details"]:
            status = "PASS" if test["passed"] else "FAIL"
            report.append(f"[{status}] {test['test_name']}")
            if test["details"]:
                report.append(f"    Details: {test['details']}")
            if test["metrics"]:
                for key, value in test["metrics"].items():
                    report.append(f"    {key}: {value}")
            report.append("")

        # Performance Metrics
        if self.results["performance_metrics"]:
            report.append("PERFORMANCE METRICS:")
            report.append("-" * 40)
            for key, value in self.results["performance_metrics"].items():
                report.append(f"{key}: {value}")
            report.append("")

        # Error Analysis
        if self.results["error_analysis"]:
            report.append("ERROR ANALYSIS:")
            report.append("-" * 40)
            for key, value in self.results["error_analysis"].items():
                report.append(f"{key}: {value}")
            report.append("")

        # Recommendations
        if self.results["recommendations"]:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 40)
            for i, rec in enumerate(self.results["recommendations"], 1):
                report.append(f"{i}. {rec}")
            report.append("")

        # Summary
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (
            (self.results["tests_passed"] / total_tests) * 100 if total_tests > 0 else 0
        )

        report.append("SUMMARY:")
        report.append("-" * 40)
        report.append(f"Overall Success Rate: {success_rate:.1f}%")
        if success_rate >= 90:
            report.append("Status: EXCELLENT - System is production ready")
        elif success_rate >= 75:
            report.append("Status: GOOD - Minor issues to address")
        elif success_rate >= 50:
            report.append("Status: FAIR - Significant issues need attention")
        else:
            report.append("Status: POOR - Major issues require immediate attention")

        return "\\n".join(report)


class TestDataGenerator:
    """Generates realistic test error logs for validation."""

    @staticmethod
    def create_json_logs(log_file: Path, num_entries: int = 100):
        """Create JSON format error logs."""
        error_templates = [
            {
                "error_type": "DatabaseError",
                "message": "Connection timeout to database server",
                "file": "/app/database.py",
                "line": 123,
                "stack_trace": "DatabaseError: Connection timeout\\n  at connect() database.py:123\\n  at query() database.py:89",
            },
            {
                "error_type": "ValidationError",
                "message": "Invalid user input format",
                "file": "/app/validation.py",
                "line": 45,
            },
            {
                "error_type": "AuthenticationError",
                "message": "Failed to authenticate user",
                "file": "/app/auth.py",
                "line": 67,
                "stack_trace": "AuthenticationError: Invalid credentials\\n  at authenticate() auth.py:67",
            },
            {
                "error_type": "NetworkError",
                "message": "Connection refused to external service",
                "file": "/app/services.py",
                "line": 234,
            },
            {
                "error_type": "OutOfMemoryError",
                "message": "Java heap space exceeded",
                "file": "/app/processor.py",
                "line": 156,
            },
        ]

        severity_levels = [
            "ERROR",
            "WARN",
            "CRITICAL",
            "ERROR",
            "ERROR",
        ]  # Weighted distribution

        with log_file.open("w") as f:
            base_time = datetime.now() - timedelta(hours=24)

            for i in range(num_entries):
                template = error_templates[i % len(error_templates)]
                timestamp = base_time + timedelta(minutes=i * 2)

                log_entry = {
                    "timestamp": timestamp.isoformat() + "Z",
                    "level": severity_levels[i % len(severity_levels)],
                    "message": template["message"],
                    "error_type": template["error_type"],
                    "file": template["file"],
                    "line": template["line"],
                    "request_id": f"req_{i:04d}",
                    "user_id": f"user_{(i % 10) + 1}",
                }

                if "stack_trace" in template:
                    log_entry["stack_trace"] = template["stack_trace"]

                f.write(json.dumps(log_entry) + "\\n")

    @staticmethod
    def create_structured_logs(log_file: Path, num_entries: int = 50):
        """Create structured text logs."""
        error_messages = [
            "Database connection pool exhausted",
            "Cache miss rate exceeds threshold: 95%",
            "Service timeout after 30 seconds",
            "Authentication failed for admin user",
            "Invalid API key provided",
            "Rate limit exceeded for client",
            "Memory usage warning: 85% of limit",
        ]

        services = [
            "DatabaseService",
            "CacheService",
            "AuthService",
            "APIGateway",
            "MemoryManager",
        ]
        levels = ["ERROR", "WARN", "ERROR", "ERROR", "WARN"]

        with log_file.open("w") as f:
            base_time = datetime.now() - timedelta(hours=12)

            for i in range(num_entries):
                timestamp = base_time + timedelta(minutes=i * 5)
                level = levels[i % len(levels)]
                service = services[i % len(services)]
                message = error_messages[i % len(error_messages)]

                log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} {level} [{service}] {message}\\n"
                f.write(log_line)

    @staticmethod
    def create_plain_logs(log_file: Path, num_entries: int = 30):
        """Create plain text error logs."""
        plain_errors = [
            "FATAL ERROR: System crash detected in module core.dll",
            "Exception occurred: NullPointerException in thread main",
            "ERROR: Failed to allocate memory for buffer size 1024MB",
            "CRITICAL: Security breach detected - unauthorized access attempt",
            "WARNING: Disk space low on partition /data (5% remaining)",
        ]

        with log_file.open("w") as f:
            base_time = datetime.now() - timedelta(hours=6)

            for i in range(num_entries):
                timestamp = base_time + timedelta(minutes=i * 10)
                error_msg = plain_errors[i % len(plain_errors)]

                log_line = f"[{timestamp.isoformat()}] {error_msg}\\n"
                f.write(log_line)


class ErrorAdapterValidator:
    """Main validator for the Enhanced Error Adapter."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.report = ValidationReport()
        self.test_dir = None
        self.adapter = None

    def setup_test_environment(self) -> Path:
        """Set up test environment with sample log files."""
        logger.info("Setting up test environment...")

        # Create temporary directory
        self.test_dir = Path(tempfile.mkdtemp(prefix="error_adapter_test_"))
        logger.info(f"Created test directory: {self.test_dir}")

        # Generate test log files
        TestDataGenerator.create_json_logs(self.test_dir / "app.json.log", 100)
        TestDataGenerator.create_structured_logs(
            self.test_dir / "app.structured.log", 50
        )
        TestDataGenerator.create_plain_logs(self.test_dir / "app.plain.log", 30)

        logger.info("Generated test log files")
        return self.test_dir

    def create_adapter_config(self) -> AdapterConfig:
        """Create adapter configuration for testing."""
        return AdapterConfig(
            adapter_id="validation_test",
            source_type="error",
            batch_mode=BatchMode.STREAMING,
            batch_size=20,
            source_config={
                "input_sources": ["logs"],
                "log_directories": [str(self.test_dir)],
                "log_file_patterns": ["*.log"],
                "enable_error_classification": True,
                "enable_pattern_detection": True,
                "enable_correlation_detection": False,  # Disable for validation
                "pattern_similarity_threshold": 0.8,
                "pattern_time_window_hours": 24,
                "severity_filters": [],  # Process all severities
            },
        )

    async def validate_component_initialization(self):
        """Validate that all components initialize correctly."""
        logger.info("Validating component initialization...")

        try:
            # Test individual components
            trend_analyzer = TrendAnalyzer(time_window_hours=24)
            self.report.add_test_result(
                "TrendAnalyzer Initialization",
                True,
                f"Time window: {trend_analyzer.time_window}",
            )

            deduplicator = ErrorDeduplicator(similarity_threshold=0.8)
            self.report.add_test_result(
                "ErrorDeduplicator Initialization",
                True,
                f"Similarity threshold: {deduplicator.similarity_threshold}",
            )

            performance_monitor = PerformanceMonitor()
            self.report.add_test_result(
                "PerformanceMonitor Initialization",
                True,
                f"Thresholds configured: {len(performance_monitor.alert_thresholds)}",
            )

            classifier = ErrorClassifier()
            self.report.add_test_result(
                "ErrorClassifier Initialization",
                True,
                f"Classification rules: {len(classifier.classification_rules)}",
            )

            # Test main adapter
            config = self.create_adapter_config()
            self.adapter = EnhancedErrorAdapter(config)
            await self.adapter.initialize()

            self.report.add_test_result(
                "EnhancedErrorAdapter Initialization",
                True,
                f"Adapter ID: {self.adapter.config.adapter_id}",
            )

        except Exception as e:
            self.report.add_test_result(
                "Component Initialization", False, f"Error: {str(e)}"
            )
            raise

    async def validate_log_parsing(self):
        """Validate multi-format log parsing capabilities."""
        logger.info("Validating log parsing...")

        try:
            # Test format detection
            detector = LogFormatDetector()

            # Test JSON detection
            json_line = '{"timestamp": "2024-01-01T10:00:00Z", "level": "ERROR", "message": "test"}'
            json_format = detector.detect_format(json_line)
            self.report.add_test_result(
                "JSON Format Detection",
                json_format == "json",
                f"Detected format: {json_format}",
            )

            # Test structured detection
            structured_line = "2024-01-01 10:00:00 ERROR [Service] Test message"
            structured_format = detector.detect_format(structured_line)
            self.report.add_test_result(
                "Structured Format Detection",
                structured_format == "structured",
                f"Detected format: {structured_format}",
            )

            # Test actual parsing
            parsed_count = 0
            parsing_errors = 0

            async for raw_error in self.adapter.fetch_items(limit=50):
                try:
                    context_item = await self.adapter.transform_item(raw_error)
                    parsed_count += 1
                except Exception as e:
                    parsing_errors += 1
                    if self.verbose:
                        logger.warning(f"Parsing error: {e}")

            self.report.add_test_result(
                "Log Parsing Accuracy",
                parsing_errors < parsed_count * 0.1,  # Less than 10% errors
                f"Parsed: {parsed_count}, Errors: {parsing_errors}",
                {"parsed_count": parsed_count, "parsing_errors": parsing_errors},
            )

        except Exception as e:
            self.report.add_test_result("Log Parsing", False, f"Error: {str(e)}")

    async def validate_error_classification(self):
        """Validate error classification capabilities."""
        logger.info("Validating error classification...")

        try:
            classifier = ErrorClassifier()

            # Test known error patterns
            test_cases = [
                {
                    "message": "Connection refused to database server",
                    "error_type": "DatabaseError",
                    "expected_category": "database",
                },
                {
                    "message": "Out of memory error in heap allocation",
                    "error_type": "OutOfMemoryError",
                    "expected_category": "memory",
                },
                {
                    "message": "Authentication failed for user admin",
                    "error_type": "SecurityException",
                    "expected_category": "security",
                },
            ]

            correct_classifications = 0
            total_tests = len(test_cases)

            for test_case in test_cases:
                from src.project_context.ingestion.adapters.enhanced_error_adapter import (
                    ParsedError,
                )

                error = ParsedError(
                    error_id="test",
                    timestamp=datetime.now(),
                    severity="high",
                    error_type=test_case["error_type"],
                    message=test_case["message"],
                    source="test",
                )

                categories, confidence = classifier.classify_error(error)

                if test_case["expected_category"] in categories:
                    correct_classifications += 1

                if self.verbose:
                    logger.info(
                        f"Classification: {categories}, Confidence: {confidence}"
                    )

            accuracy = correct_classifications / total_tests
            self.report.add_test_result(
                "Error Classification Accuracy",
                accuracy >= 0.8,  # 80% accuracy threshold
                f"Accuracy: {accuracy:.2%}",
                {
                    "accuracy": accuracy,
                    "correct": correct_classifications,
                    "total": total_tests,
                },
            )

        except Exception as e:
            self.report.add_test_result(
                "Error Classification", False, f"Error: {str(e)}"
            )

    async def validate_trend_analysis(self):
        """Validate trend analysis and pattern detection."""
        logger.info("Validating trend analysis...")

        try:
            trend_analyzer = TrendAnalyzer(time_window_hours=24)

            # Simulate error pattern data
            pattern_id = "test_pattern_001"
            base_time = datetime.now()

            # Add increasing pattern
            for i in range(5):
                timestamp = base_time - timedelta(hours=4 - i)
                count = (i + 1) * 2  # Increasing trend
                trend_analyzer.update_pattern_frequency(pattern_id, timestamp, count)

            # Test trend detection
            trending_patterns = trend_analyzer.get_trending_patterns(min_frequency=1)

            has_trending_pattern = len(trending_patterns) > 0
            if has_trending_pattern:
                pattern = trending_patterns[0]
                trend_direction = pattern.get("trend_direction")
                is_increasing = trend_direction == "increasing"
            else:
                is_increasing = False

            self.report.add_test_result(
                "Trend Analysis Detection",
                has_trending_pattern and is_increasing,
                f"Patterns found: {len(trending_patterns)}, Direction: {trend_direction if has_trending_pattern else 'none'}",
                {"trending_patterns": len(trending_patterns)},
            )

            # Test prediction
            if has_trending_pattern:
                prediction = trend_analyzer.predict_future_occurrences(
                    pattern_id, hours_ahead=1
                )
                self.report.add_test_result(
                    "Error Volume Prediction",
                    prediction > 0,
                    f"Predicted volume: {prediction:.2f}",
                    {"prediction": prediction},
                )

        except Exception as e:
            self.report.add_test_result("Trend Analysis", False, f"Error: {str(e)}")

    async def validate_deduplication_clustering(self):
        """Validate error deduplication and clustering."""
        logger.info("Validating deduplication and clustering...")

        try:
            deduplicator = ErrorDeduplicator(similarity_threshold=0.8)

            # Create similar errors that should be clustered
            from src.project_context.ingestion.adapters.enhanced_error_adapter import (
                ParsedError,
            )

            similar_errors = [
                ParsedError(
                    error_id="err_001",
                    timestamp=datetime.now(),
                    severity="high",
                    error_type="DatabaseError",
                    message="Connection timeout to database after 30 seconds",
                    source="test",
                    file_path="/app/db.py",
                    function_name="connect",
                ),
                ParsedError(
                    error_id="err_002",
                    timestamp=datetime.now(),
                    severity="high",
                    error_type="DatabaseError",
                    message="Connection timeout to database after 45 seconds",
                    source="test",
                    file_path="/app/db.py",
                    function_name="connect",
                ),
            ]

            clusters = []
            for error in similar_errors:
                cluster_id = deduplicator.find_or_create_cluster(error)
                clusters.append(cluster_id)

            # Similar errors should be in same cluster
            same_cluster = len(set(clusters)) == 1

            self.report.add_test_result(
                "Error Deduplication",
                same_cluster,
                f"Cluster IDs: {clusters}, Same cluster: {same_cluster}",
                {"clusters_created": len(set(clusters))},
            )

            # Test different errors
            different_error = ParsedError(
                error_id="err_003",
                timestamp=datetime.now(),
                severity="medium",
                error_type="ValidationError",
                message="Invalid input format provided",
                source="test",
                file_path="/app/validation.py",
            )

            different_cluster = deduplicator.find_or_create_cluster(different_error)
            different_clustered = different_cluster not in clusters

            self.report.add_test_result(
                "Error Differentiation",
                different_clustered,
                f"Different error in separate cluster: {different_clustered}",
                {"separate_cluster": different_clustered},
            )

        except Exception as e:
            self.report.add_test_result(
                "Deduplication and Clustering", False, f"Error: {str(e)}"
            )

    async def validate_performance_monitoring(self):
        """Validate performance monitoring and alerting."""
        logger.info("Validating performance monitoring...")

        try:
            monitor = PerformanceMonitor()

            # Test normal operations
            normal_times = [100, 150, 120, 90, 110]  # Normal processing times
            for time_ms in normal_times:
                monitor.record_processing_time(time_ms)

            stats = monitor.get_performance_stats()
            has_stats = len(stats) > 0

            self.report.add_test_result(
                "Performance Stats Collection",
                has_stats,
                f"Stats collected: {len(stats)} metrics",
                stats,
            )

            # Test alert generation
            monitor.record_processing_time(6000)  # Trigger high processing time alert
            alerts = monitor.get_recent_alerts()

            has_alerts = len(alerts) > 0
            alert_types = [alert["type"] for alert in alerts]

            self.report.add_test_result(
                "Performance Alert Generation",
                has_alerts and "high_processing_time" in alert_types,
                f"Alerts generated: {len(alerts)}, Types: {alert_types}",
                {"alert_count": len(alerts), "alert_types": alert_types},
            )

        except Exception as e:
            self.report.add_test_result(
                "Performance Monitoring", False, f"Error: {str(e)}"
            )

    async def validate_end_to_end_processing(self):
        """Validate complete end-to-end error processing pipeline."""
        logger.info("Validating end-to-end processing...")

        try:
            start_time = datetime.now()

            # Process all test errors
            processed_errors = []
            total_processing_time = 0

            async for raw_error in self.adapter.fetch_items(limit=100):
                item_start = datetime.now()
                context_item = await self.adapter.transform_item(raw_error)
                item_time = (datetime.now() - item_start).total_seconds() * 1000
                total_processing_time += item_time

                processed_errors.append(context_item)

            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            # Validation checks
            errors_processed = len(processed_errors)
            avg_processing_time = (
                total_processing_time / errors_processed if errors_processed > 0 else 0
            )

            # Check that all errors have required fields
            valid_errors = 0
            for error in processed_errors:
                if (
                    error.source_type == "error"
                    and error.severity
                    and error.title
                    and error.content
                    and error.metrics
                ):
                    valid_errors += 1

            validation_rate = (
                valid_errors / errors_processed if errors_processed > 0 else 0
            )

            self.report.add_test_result(
                "End-to-End Processing",
                validation_rate >= 0.95,  # 95% of errors should be valid
                f"Processed: {errors_processed}, Valid: {valid_errors}, Rate: {validation_rate:.2%}",
                {
                    "errors_processed": errors_processed,
                    "valid_errors": valid_errors,
                    "validation_rate": validation_rate,
                    "total_time_seconds": total_time,
                    "avg_processing_time_ms": avg_processing_time,
                },
            )

            # Get final statistics
            adapter_stats = await self.adapter.get_adapter_statistics()
            self.report.set_performance_metrics(adapter_stats)

            # Get error analysis
            clusters = await self.adapter.get_error_clusters(limit=20)
            trending = await self.adapter.get_trending_errors(limit=10)

            self.report.set_error_analysis(
                {
                    "total_clusters": len(clusters),
                    "trending_patterns": len(trending),
                    "processing_rate_per_second": errors_processed / total_time
                    if total_time > 0
                    else 0,
                }
            )

        except Exception as e:
            self.report.add_test_result(
                "End-to-End Processing", False, f"Error: {str(e)}"
            )

    def generate_recommendations(self):
        """Generate recommendations based on validation results."""
        failed_tests = [
            test for test in self.report.results["test_details"] if not test["passed"]
        ]

        if not failed_tests:
            self.report.add_recommendation(
                "System validation completed successfully. Ready for production deployment."
            )

        # Performance recommendations
        perf_metrics = self.report.results.get("performance_metrics", {})
        avg_time = perf_metrics.get("avg_processing_time_ms", 0)

        if avg_time > 1000:  # > 1 second
            self.report.add_recommendation(
                f"Average processing time is {avg_time:.0f}ms. Consider optimizing parsing algorithms or increasing resources."
            )

        if avg_time > 500:  # > 500ms
            self.report.add_recommendation(
                "Consider implementing batch processing for high-volume scenarios."
            )

        # Error analysis recommendations
        error_analysis = self.report.results.get("error_analysis", {})
        cluster_count = error_analysis.get("total_clusters", 0)

        if cluster_count < 5:
            self.report.add_recommendation(
                "Low cluster count suggests errors may not be diverse enough for comprehensive testing."
            )

        # Failed test recommendations
        for test in failed_tests:
            if "Classification" in test["test_name"]:
                self.report.add_recommendation(
                    "Error classification accuracy is low. Review and expand classification rules."
                )
            elif "Parsing" in test["test_name"]:
                self.report.add_recommendation(
                    "Log parsing errors detected. Review log format patterns and add support for additional formats."
                )
            elif "Performance" in test["test_name"]:
                self.report.add_recommendation(
                    "Performance issues detected. Monitor system resources and optimize processing pipeline."
                )

    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            logger.info(f"Cleaned up test directory: {self.test_dir}")

    async def run_validation(self) -> ValidationReport:
        """Run complete validation suite."""
        logger.info("Starting Enhanced Error Adapter validation...")

        try:
            # Setup
            self.setup_test_environment()

            # Run validation tests
            await self.validate_component_initialization()
            await self.validate_log_parsing()
            await self.validate_error_classification()
            await self.validate_trend_analysis()
            await self.validate_deduplication_clustering()
            await self.validate_performance_monitoring()
            await self.validate_end_to_end_processing()

            # Generate recommendations
            self.generate_recommendations()

            # Cleanup
            if self.adapter:
                await self.adapter.cleanup()

        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            self.report.add_test_result(
                "Validation Suite", False, f"Critical error: {str(e)}"
            )

        finally:
            self.cleanup_test_environment()

        logger.info("Validation completed.")
        return self.report


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate Enhanced Error Adapter")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output-dir", "-o", help="Output directory for reports")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run validation
    validator = ErrorAdapterValidator(verbose=args.verbose)
    report = await validator.run_validation()

    # Generate report
    report_text = report.generate_report()
    print(report_text)

    # Save report if output directory specified
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        report_file = (
            output_dir
            / f"error_adapter_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        with report_file.open("w") as f:
            f.write(report_text)

        # Save JSON report
        json_file = (
            output_dir
            / f"error_adapter_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with json_file.open("w") as f:
            # Make datetime serializable
            results_copy = report.results.copy()
            results_copy["validation_time"] = results_copy[
                "validation_time"
            ].isoformat()
            json.dump(results_copy, f, indent=2)

        print(f"\\nReports saved to:")
        print(f"  Text: {report_file}")
        print(f"  JSON: {json_file}")

    # Exit with appropriate code
    if report.results["tests_failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
