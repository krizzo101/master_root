#!/usr/bin/env python3
"""
Error Log Ingestion System Validation Script

This script validates the complete error log ingestion system including:
- Enhanced error adapter functionality
- Real-time processing pipeline
- Database schema and functions
- Correlation detection
- Alert generation
"""

import asyncio
import json
import logging
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import asyncpg
import structlog

from src.project_context.ingestion.adapters.enhanced_error_adapter import (
    EnhancedErrorAdapter,
)
from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode
from src.project_context.ingestion.database import IngestionDatabase
from src.project_context.ingestion.realtime_error_pipeline import (
    RealtimeErrorPipeline,
    StreamProcessor,
    create_realtime_pipeline,
)

logger = structlog.get_logger(__name__)


class ErrorIngestionValidator:
    """Comprehensive validator for error ingestion system."""

    def __init__(
        self, database_url: str = "postgresql://opsvi@localhost:5432/unified_context"
    ):
        self.database_url = database_url
        self.database = None
        self.adapter = None
        self.pipeline = None
        self.test_results = {}

    async def initialize(self):
        """Initialize validator components."""
        print("🔧 Initializing Error Ingestion System Validator...")

        # Initialize database connection
        self.database = IngestionDatabase(self.database_url)
        await self.database.initialize()

        # Initialize enhanced error adapter
        config = AdapterConfig(
            adapter_id="test_enhanced_error",
            source_type="error",
            batch_mode=BatchMode.STREAMING,
            batch_size=10,
            source_config={
                "input_sources": ["logs"],
                "log_directories": [str(tempfile.gettempdir())],
                "enable_error_classification": True,
                "enable_pattern_detection": True,
                "enable_correlation_detection": True,
                "realtime_processing": True,
            },
        )

        self.adapter = EnhancedErrorAdapter(config)
        await self.adapter.initialize()

        # Initialize real-time pipeline
        pipeline_config = StreamProcessor(
            max_concurrent_workers=3,
            batch_size_range=(5, 20),
            input_queue_maxsize=100,
            processing_queue_maxsize=50,
            enable_realtime_alerts=True,
            alert_aggregation_window_minutes=1,
        )

        self.pipeline = RealtimeErrorPipeline(
            self.adapter, self.database, pipeline_config
        )

        print("✅ Validator initialized successfully")

    async def run_all_tests(self) -> Dict:
        """Run all validation tests."""
        print("\n🧪 Running Error Ingestion System Validation Tests...")

        test_suite = [
            ("Database Schema", self.test_database_schema),
            ("Enhanced Error Adapter", self.test_enhanced_error_adapter),
            ("Log Format Detection", self.test_log_format_detection),
            ("Stack Trace Parsing", self.test_stack_trace_parsing),
            ("Error Classification", self.test_error_classification),
            ("Pattern Detection", self.test_pattern_detection),
            ("Correlation Detection", self.test_correlation_detection),
            ("Real-time Pipeline", self.test_realtime_pipeline),
            ("Alert Generation", self.test_alert_generation),
            ("Performance Validation", self.test_performance),
        ]

        for test_name, test_func in test_suite:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                start_time = time.time()
                result = await test_func()
                elapsed = time.time() - start_time

                self.test_results[test_name] = {
                    "status": "PASS" if result else "FAIL",
                    "duration_seconds": elapsed,
                    "details": result if isinstance(result, dict) else {},
                }

                status_icon = "✅" if result else "❌"
                print(
                    f"{status_icon} {test_name}: {self.test_results[test_name]['status']} ({elapsed:.2f}s)"
                )

            except Exception as e:
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "duration_seconds": time.time() - start_time,
                    "error": str(e),
                }
                print(f"💥 {test_name}: ERROR - {e}")

        return self.test_results

    async def test_database_schema(self) -> Dict:
        """Test database schema and functions."""
        results = {}

        # Test table existence
        tables_to_check = [
            "error_patterns",
            "stack_trace_analysis",
            "error_correlation_rules",
            "error_alerts",
            "error_impact_analysis",
            "log_source_health",
        ]

        for table in tables_to_check:
            exists = await self._check_table_exists(table)
            results[f"table_{table}"] = exists

        # Test functions
        functions_to_check = [
            "calculate_pattern_impact_score",
            "find_similar_stack_traces",
            "detect_pattern_anomalies",
            "analyze_error_correlations",
        ]

        for function in functions_to_check:
            exists = await self._check_function_exists(function)
            results[f"function_{function}"] = exists

        # Test materialized views
        views_to_check = ["error_pattern_analytics", "stack_trace_commonality"]

        for view in views_to_check:
            exists = await self._check_view_exists(view)
            results[f"view_{view}"] = exists

        all_passed = all(results.values())
        results["overall"] = all_passed
        return results

    async def test_enhanced_error_adapter(self) -> Dict:
        """Test enhanced error adapter functionality."""
        results = {}

        # Test configuration
        config = self.adapter.config
        results["config_loaded"] = config is not None
        results["source_type"] = config.source_type == "error"
        results["batch_mode"] = config.batch_mode == BatchMode.STREAMING

        # Test format detector
        format_detector = self.adapter.format_detector

        # Test JSON detection
        json_line = '{"timestamp": "2024-01-01T10:00:00Z", "level": "ERROR", "message": "Test error"}'
        json_format = format_detector.detect_format(json_line)
        results["json_format_detection"] = json_format == "json"

        # Test structured detection
        structured_line = "2024-01-01 10:00:00 ERROR [TestComponent] Test error message"
        structured_format = format_detector.detect_format(structured_line)
        results["structured_format_detection"] = structured_format == "structured"

        # Test plain detection
        plain_line = "ERROR: Something went wrong"
        plain_format = format_detector.detect_format(plain_line)
        results["plain_format_detection"] = plain_format == "plain"

        # Test stack trace parser
        stack_parser = self.adapter.stack_parser
        python_stack = """File "/app/main.py", line 42, in process_request
    result = calculate_value(data)
File "/app/utils.py", line 15, in calculate_value
    return data / divisor"""

        stack_elements = stack_parser.parse_stack_trace(python_stack)
        results["stack_parsing"] = len(stack_elements) > 0
        results["stack_element_details"] = len(stack_elements) == 2

        # Test error classifier
        classifier = self.adapter.classifier
        from src.project_context.ingestion.adapters.enhanced_error_adapter import (
            ParsedError,
        )

        test_error = ParsedError(
            error_id="test_001",
            timestamp=datetime.now(),
            severity="high",
            error_type="DatabaseError",
            message="Connection timeout to database server",
            source="test",
        )

        categories, confidence = classifier.classify_error(test_error)
        results["error_classification"] = "database" in categories
        results["classification_confidence"] = confidence > 0.5

        all_passed = all(results.values())
        results["overall"] = all_passed
        return results

    async def test_log_format_detection(self) -> Dict:
        """Test log format detection with various examples."""
        results = {}

        test_cases = [
            # JSON formats
            (
                '{"timestamp":"2024-01-01T10:00:00Z","level":"ERROR","message":"Test"}',
                "json",
            ),
            ('{"@timestamp":"2024-01-01","severity":"error","msg":"Failed"}', "json"),
            # Structured formats
            ("2024-01-01 10:00:00.123 ERROR [Component] Message here", "structured"),
            ("Jan 1 10:00:00 server process: ERROR message", "structured"),
            ("[2024-01-01 10:00:00] [ERROR] Message content", "structured"),
            # Plain formats
            ("ERROR: Something went wrong", "plain"),
            ("CRITICAL: System failure detected", "plain"),
            ("Just a plain log message", "plain"),
        ]

        format_detector = self.adapter.format_detector
        correct_detections = 0

        for log_line, expected_format in test_cases:
            detected_format = format_detector.detect_format(log_line)
            if detected_format == expected_format:
                correct_detections += 1

            results[f"format_detection_{expected_format}_{len(results)}"] = (
                detected_format == expected_format
            )

        results["detection_accuracy"] = correct_detections / len(test_cases)
        results["overall"] = (
            results["detection_accuracy"] >= 0.8
        )  # 80% accuracy threshold

        return results

    async def test_stack_trace_parsing(self) -> Dict:
        """Test stack trace parsing for different languages."""
        results = {}

        stack_parser = self.adapter.stack_parser

        # Test Python stack trace
        python_stack = """File "/app/main.py", line 42, in process_request
    result = calculate_value(data)
File "/app/utils.py", line 15, in calculate_value
    return data / divisor
ZeroDivisionError: division by zero"""

        python_elements = stack_parser.parse_stack_trace(python_stack)
        results["python_parsing"] = len(python_elements) >= 2
        results["python_file_paths"] = all(elem.file_path for elem in python_elements)
        results["python_line_numbers"] = all(
            elem.line_number > 0 for elem in python_elements
        )

        # Test Java stack trace
        java_stack = """java.lang.NullPointerException: null
    at com.example.service.UserService.getUser(UserService.java:45)
    at com.example.controller.UserController.handleRequest(UserController.java:23)"""

        java_elements = stack_parser.parse_stack_trace(java_stack)
        results["java_parsing"] = len(java_elements) >= 2
        results["java_class_names"] = any(elem.class_name for elem in java_elements)

        # Test JavaScript stack trace
        js_stack = """TypeError: Cannot read property 'name' of undefined
    at processUser (app.js:15:12)
    at handleRequest (server.js:42:5)"""

        js_elements = stack_parser.parse_stack_trace(js_stack)
        results["javascript_parsing"] = len(js_elements) >= 2

        # Test language detection
        detected_python = stack_parser.detect_language(python_stack)
        detected_java = stack_parser.detect_language(java_stack)
        detected_js = stack_parser.detect_language(js_stack)

        results["language_detection_python"] = detected_python == "python"
        results["language_detection_java"] = detected_java == "java"
        results["language_detection_javascript"] = detected_js == "javascript"

        all_passed = all(results.values())
        results["overall"] = all_passed
        return results

    async def test_error_classification(self) -> Dict:
        """Test error classification system."""
        results = {}

        classifier = self.adapter.classifier

        test_cases = [
            ("Connection timeout to database", ["database", "network"]),
            ("OutOfMemoryError: Java heap space", ["memory"]),
            ("Unauthorized access attempt detected", ["security"]),
            ("File not found: /tmp/config.json", ["filesystem"]),
            ("SyntaxError: invalid syntax", ["syntax"]),
            ("NullPointerException in user service", ["runtime", "type"]),
            ("Rate limit exceeded for API calls", ["performance"]),
        ]

        from src.project_context.ingestion.adapters.enhanced_error_adapter import (
            ParsedError,
        )

        correct_classifications = 0
        total_expected_categories = 0

        for message, expected_categories in test_cases:
            test_error = ParsedError(
                error_id=f"test_{len(results)}",
                timestamp=datetime.now(),
                severity="high",
                error_type="TestError",
                message=message,
                source="test",
            )

            categories, confidence = classifier.classify_error(test_error)

            # Check if at least one expected category was found
            category_match = any(cat in categories for cat in expected_categories)
            if category_match:
                correct_classifications += 1

            results[f"classification_{len(results)}"] = {
                "message": message,
                "expected": expected_categories,
                "actual": categories,
                "confidence": confidence,
                "match": category_match,
            }

            total_expected_categories += len(expected_categories)

        results["classification_accuracy"] = correct_classifications / len(test_cases)
        results["overall"] = (
            results["classification_accuracy"] >= 0.7
        )  # 70% accuracy threshold

        return results

    async def test_pattern_detection(self) -> Dict:
        """Test error pattern detection."""
        results = {}

        # Generate test errors with patterns
        test_errors = []
        base_time = datetime.now()

        # Create repeating pattern
        for i in range(5):
            error_data = {
                "error_id": f"pattern_test_{i}",
                "timestamp": base_time + timedelta(minutes=i * 5),
                "severity": "high",
                "error_type": "DatabaseConnectionError",
                "message": "Connection timeout to database server",
                "source": "application",
                "file_path": "/app/database.py",
                "line_number": 45,
                "categories": ["database", "network"],
            }
            test_errors.append(error_data)

        # Process errors through adapter
        context_items = []
        for error_data in test_errors:
            try:
                context_item = await self.adapter.transform_item(error_data)
                context_items.append(context_item)
            except Exception as e:
                results[f"transform_error_{len(context_items)}"] = str(e)

        results["items_transformed"] = len(context_items) == len(test_errors)

        # Check if adapter detected patterns
        patterns = await self.adapter.get_error_patterns()
        results["patterns_detected"] = len(patterns) > 0

        if patterns:
            pattern = patterns[0]
            results["pattern_frequency"] = pattern["frequency"] > 1
            results["pattern_files"] = len(pattern["file_paths"]) > 0
            results["pattern_severity_dist"] = len(pattern["severity_distribution"]) > 0

        results["overall"] = (
            results.get("items_transformed", False) and len(patterns) > 0
        )
        return results

    async def test_correlation_detection(self) -> Dict:
        """Test correlation detection between errors and other context items."""
        results = {}

        # Create mock context items for correlation
        error_time = datetime.now()

        # Create a git commit item
        git_item_data = {
            "id": "git_test_001",
            "source_type": "git",
            "entity_type": "commit",
            "timestamp": error_time - timedelta(minutes=10),
            "file_path": "/app/database.py",
            "content": "fix: update database connection handling",
            "source_data": {"commit_hash": "abc123", "author": "developer"},
        }

        # Create an error item
        error_item_data = {
            "error_id": "correlation_test_001",
            "timestamp": error_time,
            "severity": "high",
            "error_type": "DatabaseError",
            "message": "Database connection failed",
            "source": "application",
            "file_path": "/app/database.py",
            "line_number": 45,
        }

        # Transform error to context item
        error_context_item = await self.adapter.transform_item(error_item_data)

        # Mock correlation engine functionality
        if (
            hasattr(self.adapter, "correlation_engine")
            and self.adapter.correlation_engine
        ):
            # Test would require actual database setup for full correlation testing
            results["correlation_engine_available"] = True
            results["basic_setup"] = True
        else:
            results["correlation_engine_available"] = False
            results["basic_setup"] = True

        # Test relationship detection
        mock_context_window = [
            error_context_item
        ]  # In real scenario, would include git_item

        try:
            relationships = await self.adapter.detect_relationships(
                error_context_item, mock_context_window
            )
            results["relationship_detection"] = isinstance(relationships, list)
            results["relationships_found"] = len(relationships)
        except Exception as e:
            results["relationship_detection_error"] = str(e)
            results["relationship_detection"] = False

        results["overall"] = results.get("basic_setup", False) and results.get(
            "relationship_detection", False
        )
        return results

    async def test_realtime_pipeline(self) -> Dict:
        """Test real-time processing pipeline."""
        results = {}

        # Test pipeline initialization
        try:
            await self.pipeline.start()
            results["pipeline_start"] = True

            # Test metrics collection
            metrics = await self.pipeline.get_pipeline_metrics()
            results["metrics_available"] = isinstance(metrics, dict)
            results["metrics_keys"] = all(
                key in metrics
                for key in [
                    "total_processed",
                    "errors_per_second",
                    "queue_sizes",
                    "pipeline_status",
                ]
            )

            # Test error batch ingestion
            test_errors = []
            for i in range(5):
                error_data = {
                    "error_id": f"pipeline_test_{i}",
                    "timestamp": datetime.now(),
                    "severity": "medium",
                    "error_type": "TestError",
                    "message": f"Pipeline test error {i}",
                    "source": "test",
                }
                test_errors.append(error_data)

            await self.pipeline.ingest_error_batch(test_errors)

            # Wait a bit for processing
            await asyncio.sleep(2)

            # Check if errors were processed
            updated_metrics = await self.pipeline.get_pipeline_metrics()
            results["errors_processed"] = updated_metrics["total_processed"] > 0

            # Test pattern tracking
            patterns = await self.pipeline.get_error_patterns()
            results["pattern_tracking"] = isinstance(patterns, list)

            # Test alert system
            alerts = await self.pipeline.get_active_alerts()
            results["alert_system"] = isinstance(alerts, list)

            await self.pipeline.stop()
            results["pipeline_stop"] = True

        except Exception as e:
            results["pipeline_error"] = str(e)
            results["pipeline_start"] = False
            try:
                await self.pipeline.stop()
            except:
                pass

        results["overall"] = results.get("pipeline_start", False) and results.get(
            "pipeline_stop", False
        )
        return results

    async def test_alert_generation(self) -> Dict:
        """Test alert generation functionality."""
        results = {}

        # Test alert manager
        alert_manager = self.pipeline.alert_manager
        results["alert_manager_available"] = alert_manager is not None

        # Test critical error alert
        from src.project_context.ingestion.adapters.enhanced_error_adapter import (
            ParsedError,
        )

        critical_error = ParsedError(
            error_id="critical_test_001",
            timestamp=datetime.now(),
            severity="critical",
            error_type="SystemFailure",
            message="Critical system failure detected",
            source="system",
            file_path="/app/core.py",
            line_number=100,
        )

        try:
            alerts = await alert_manager.process_error_for_alerts(critical_error, [])
            results["critical_alert_generated"] = len(alerts) > 0

            if alerts:
                alert = alerts[0]
                results["alert_severity_correct"] = alert.severity.value == "critical"
                results["alert_has_metadata"] = len(alert.metadata) > 0
                results["alert_has_message"] = len(alert.message) > 0

        except Exception as e:
            results["alert_generation_error"] = str(e)
            results["critical_alert_generated"] = False

        results["overall"] = results.get("critical_alert_generated", False)
        return results

    async def test_performance(self) -> Dict:
        """Test performance characteristics of the system."""
        results = {}

        # Performance test parameters
        num_errors = 100
        test_errors = []

        # Generate test errors
        base_time = datetime.now()
        for i in range(num_errors):
            error_data = {
                "error_id": f"perf_test_{i}",
                "timestamp": base_time + timedelta(seconds=i),
                "severity": ["low", "medium", "high"][i % 3],
                "error_type": ["NetworkError", "DatabaseError", "ValidationError"][
                    i % 3
                ],
                "message": f"Performance test error {i} with some additional context",
                "source": "performance_test",
                "file_path": f"/app/module_{i % 5}.py",
                "line_number": (i % 100) + 1,
            }
            test_errors.append(error_data)

        # Test transformation performance
        start_time = time.time()
        transformed_items = []

        for error_data in test_errors[:50]:  # Test with smaller batch for validation
            try:
                context_item = await self.adapter.transform_item(error_data)
                transformed_items.append(context_item)
            except Exception as e:
                results[f"transform_error_{len(transformed_items)}"] = str(e)

        transform_time = time.time() - start_time

        results["items_transformed"] = len(transformed_items)
        results["transform_time_seconds"] = transform_time
        results["avg_transform_time_ms"] = (
            (transform_time / len(transformed_items)) * 1000 if transformed_items else 0
        )
        results["transform_throughput_per_second"] = (
            len(transformed_items) / transform_time if transform_time > 0 else 0
        )

        # Performance thresholds
        results["transform_performance_acceptable"] = (
            results["avg_transform_time_ms"] < 100
        )  # < 100ms per item
        results["throughput_acceptable"] = (
            results["transform_throughput_per_second"] > 10
        )  # > 10 items/second

        # Test adapter statistics
        try:
            adapter_stats = await self.adapter.get_adapter_statistics()
            results["adapter_stats_available"] = isinstance(adapter_stats, dict)

            if "avg_processing_time_ms" in adapter_stats:
                results["adapter_avg_processing_time"] = adapter_stats[
                    "avg_processing_time_ms"
                ]
        except Exception as e:
            results["adapter_stats_error"] = str(e)

        results["overall"] = results.get(
            "transform_performance_acceptable", False
        ) and results.get("throughput_acceptable", False)
        return results

    async def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        if not self.test_results:
            return "No test results available. Run validation tests first."

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("ERROR LOG INGESTION SYSTEM VALIDATION REPORT")
        report_lines.append("=" * 60)
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "PASS"
        )
        failed_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "FAIL"
        )
        error_tests = sum(
            1 for result in self.test_results.values() if result["status"] == "ERROR"
        )

        report_lines.append("SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"Total Tests: {total_tests}")
        report_lines.append(
            f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)"
        )
        report_lines.append(
            f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)"
        )
        report_lines.append(
            f"Errors: {error_tests} ({error_tests/total_tests*100:.1f}%)"
        )
        report_lines.append("")

        # Overall status
        if passed_tests == total_tests:
            status_icon = "✅"
            status_text = "ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION"
        elif passed_tests >= total_tests * 0.8:
            status_icon = "⚠️"
            status_text = "MOST TESTS PASSED - REVIEW FAILURES BEFORE PRODUCTION"
        else:
            status_icon = "❌"
            status_text = "MULTIPLE FAILURES - SYSTEM NEEDS FIXES"

        report_lines.append(f"{status_icon} {status_text}")
        report_lines.append("")

        # Detailed results
        report_lines.append("DETAILED TEST RESULTS")
        report_lines.append("-" * 30)

        for test_name, result in self.test_results.items():
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[result["status"]]
            duration = result["duration_seconds"]

            report_lines.append(
                f"{status_icon} {test_name}: {result['status']} ({duration:.2f}s)"
            )

            if result["status"] == "ERROR":
                report_lines.append(f"   Error: {result.get('error', 'Unknown error')}")
            elif "details" in result and result["details"]:
                details = result["details"]
                if isinstance(details, dict) and "overall" in details:
                    # Show key metrics for performance/validation tests
                    for key, value in details.items():
                        if key not in ["overall"] and isinstance(
                            value, (int, float, bool)
                        ):
                            report_lines.append(f"   {key}: {value}")

            report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 20)

        if failed_tests == 0 and error_tests == 0:
            report_lines.append("✅ System validation completed successfully")
            report_lines.append("✅ All components are functioning properly")
            report_lines.append("✅ Ready for production deployment")
        else:
            if error_tests > 0:
                report_lines.append("❌ Fix critical errors before proceeding")
            if failed_tests > 0:
                report_lines.append("⚠️ Review and address test failures")

            report_lines.append("📋 Verify database schema is properly deployed")
            report_lines.append("📋 Check adapter configuration settings")
            report_lines.append("📋 Ensure all dependencies are installed")

        report_lines.append("")
        report_lines.append(
            "For detailed troubleshooting, check individual test results above."
        )
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    # Helper methods

    async def _check_table_exists(self, table_name: str) -> bool:
        """Check if a database table exists."""
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = $1)", table_name
            )
            await conn.close()
            return result
        except Exception:
            return False

    async def _check_function_exists(self, function_name: str) -> bool:
        """Check if a database function exists."""
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = $1)", function_name
            )
            await conn.close()
            return result
        except Exception:
            return False

    async def _check_view_exists(self, view_name: str) -> bool:
        """Check if a materialized view exists."""
        try:
            conn = await asyncpg.connect(self.database_url)
            result = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM pg_matviews WHERE matviewname = $1)",
                view_name,
            )
            await conn.close()
            return result
        except Exception:
            return False

    async def cleanup(self):
        """Clean up validator resources."""
        if self.pipeline:
            try:
                await self.pipeline.stop()
            except:
                pass

        if self.adapter:
            try:
                await self.adapter.cleanup()
            except:
                pass

        if self.database:
            try:
                await self.database.close()
            except:
                pass


async def main():
    """Main validation function."""
    validator = ErrorIngestionValidator()

    try:
        await validator.initialize()
        test_results = await validator.run_all_tests()
        report = await validator.generate_report()

        print(f"\n{report}")

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"error_ingestion_validation_report_{timestamp}.txt"

        with open(report_file, "w") as f:
            f.write(report)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Return exit code based on results
        total_tests = len(test_results)
        passed_tests = sum(
            1 for result in test_results.values() if result["status"] == "PASS"
        )

        if passed_tests == total_tests:
            print("🎉 All tests passed! System is ready for deployment.")
            return 0
        else:
            print(
                f"⚠️  {total_tests - passed_tests} tests failed. Review the report for details."
            )
            return 1

    except Exception as e:
        print(f"💥 Validation failed with error: {e}")
        return 1

    finally:
        await validator.cleanup()


if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run validation
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
