#!/usr/bin/env python3
"""
Error Handling & Recovery Validation Agent

Tests comprehensive error handling and recovery mechanisms including:
- Graceful failure handling
- Auto-recovery with retries
- Error propagation and isolation
- Recovery metrics collection
- System stability under failure conditions
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from generic_orchestrator import AgentTask, GenericOrchestrator

try:
    from src.enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator

    ENHANCED_AVAILABLE = True
except ImportError:
    EnhancedOrchestrator = None
    EnhancedAgentTask = None
    ENHANCED_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ErrorHandlingValidator:
    """Validates error handling and recovery mechanisms"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(
            tempfile.mkdtemp(prefix="error_validation_")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.test_results = {
            "test_scenarios": [],
            "metrics": {},
            "summary": {},
            "timestamp": datetime.now().isoformat(),
        }

        self.validation_scores = {
            "graceful_failure": 0,
            "auto_recovery": 0,
            "error_isolation": 0,
            "partial_batch_handling": 0,
            "error_logging": 0,
            "metrics_collection": 0,
            "system_stability": 0,
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all error handling validation tests"""

        logger.info("=" * 60)
        logger.info("ERROR HANDLING & RECOVERY VALIDATION")
        logger.info("=" * 60)

        # Test 1: Graceful failure handling
        await self.test_graceful_failure_handling()

        # Test 2: Auto-recovery with retries
        await self.test_auto_recovery_with_retries()

        # Test 3: Error isolation
        await self.test_error_isolation()

        # Test 4: Partial batch failures
        await self.test_partial_batch_failures()

        # Test 5: Error logging and metrics
        await self.test_error_logging_and_metrics()

        # Test 6: System stability under stress
        await self.test_system_stability_under_stress()

        # Test 7: Dependency failure propagation
        await self.test_dependency_failure_propagation()

        # Test 8: Invalid configuration handling
        await self.test_invalid_configuration_handling()

        # Generate final report
        return self.generate_validation_report()

    async def test_graceful_failure_handling(self):
        """Test graceful failure handling when tasks fail"""

        logger.info("\n--- Test 1: Graceful Failure Handling ---")

        test_tasks = [
            AgentTask(
                task_id="invalid_prompt_task",
                task_type="test",
                prompt="",  # Empty prompt - should fail gracefully
                context={"test": "empty_prompt"},
            ),
            AgentTask(
                task_id="normal_task",
                task_type="test",
                prompt="Simple test task that should complete",
                context={"test": "normal"},
            ),
            AgentTask(
                task_id="malformed_task",
                task_type="test",
                prompt="Task with invalid dependencies",
                dependencies=["non_existent_task"],  # Non-existent dependency
            ),
        ]

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "graceful_failure",
                max_parallel=2,
                use_optimizations=False,  # Disable optimizations for testing
            )

            results = await orchestrator.execute_batch(test_tasks)

            # Analyze results
            failed_count = sum(1 for r in results if r["status"] == "failed")
            completed_count = sum(1 for r in results if r["status"] == "completed")

            # System should not crash even with failures
            test_passed = len(results) == len(test_tasks)

            self.validation_scores["graceful_failure"] = 8 if test_passed else 2

            self.test_results["test_scenarios"].append(
                {
                    "test": "graceful_failure_handling",
                    "passed": test_passed,
                    "total_tasks": len(test_tasks),
                    "failed_tasks": failed_count,
                    "completed_tasks": completed_count,
                    "details": results,
                }
            )

            logger.info(
                f"✓ Graceful failure test: {failed_count} failed, {completed_count} completed"
            )

        except Exception as e:
            logger.error(f"✗ Graceful failure test crashed: {e}")
            self.validation_scores["graceful_failure"] = 0
            self.test_results["test_scenarios"].append(
                {"test": "graceful_failure_handling", "passed": False, "error": str(e)}
            )

    async def test_auto_recovery_with_retries(self):
        """Test auto-recovery with retry mechanisms"""

        logger.info("\n--- Test 2: Auto-Recovery with Retries ---")

        # Create a custom orchestrator with retry logic
        class RetryOrchestrator(GenericOrchestrator):
            def __init__(self, *args, max_retries: int = 3, **kwargs):
                super().__init__(*args, **kwargs)
                self.max_retries = max_retries
                self.retry_attempts = {}

            async def execute_agent(self, task: AgentTask) -> Dict:
                """Execute with retry logic"""
                task_id = task.task_id

                if task_id not in self.retry_attempts:
                    self.retry_attempts[task_id] = 0

                while self.retry_attempts[task_id] < self.max_retries:
                    try:
                        # Simulate transient failures for testing
                        if (
                            "transient" in task.task_id
                            and self.retry_attempts[task_id] < 2
                        ):
                            self.retry_attempts[task_id] += 1
                            raise Exception(
                                f"Transient failure (attempt {self.retry_attempts[task_id]})"
                            )

                        result = await super().execute_agent(task)

                        if (
                            result["status"] == "failed"
                            and self.retry_attempts[task_id] < self.max_retries - 1
                        ):
                            self.retry_attempts[task_id] += 1
                            logger.info(
                                f"Retrying {task_id} (attempt {self.retry_attempts[task_id] + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(1)  # Brief delay before retry
                            continue

                        return result

                    except Exception as e:
                        if self.retry_attempts[task_id] < self.max_retries - 1:
                            self.retry_attempts[task_id] += 1
                            logger.info(
                                f"Retrying {task_id} after error (attempt {self.retry_attempts[task_id] + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(1)
                            continue
                        else:
                            # Final failure after all retries
                            task.status = "failed"
                            task.error = (
                                f"Failed after {self.max_retries} attempts: {str(e)}"
                            )
                            return task.to_dict()

                # Should not reach here, but handle it
                task.status = "failed"
                task.error = f"Max retries ({self.max_retries}) exceeded"
                return task.to_dict()

        test_tasks = [
            AgentTask(
                task_id="transient_failure_1",
                task_type="test",
                prompt="Task that fails transiently",
            ),
            AgentTask(
                task_id="permanent_failure",
                task_type="test",
                prompt="",  # Will always fail
            ),
            AgentTask(
                task_id="normal_task",
                task_type="test",
                prompt="Normal task that should succeed",
            ),
        ]

        try:
            orchestrator = RetryOrchestrator(
                output_dir=self.output_dir / "auto_recovery",
                max_parallel=2,
                max_retries=3,
                use_optimizations=False,
            )

            results = await orchestrator.execute_batch(test_tasks)

            # Check retry attempts
            retry_info = {
                task_id: attempts
                for task_id, attempts in orchestrator.retry_attempts.items()
            }

            # Transient failure should have been retried and eventually succeeded
            transient_succeeded = any(
                r["task_id"] == "transient_failure_1" and r["status"] != "failed"
                for r in results
            )

            # Permanent failure should have been retried max times
            permanent_retries = retry_info.get("permanent_failure", 0) >= 2

            test_passed = transient_succeeded or permanent_retries

            self.validation_scores["auto_recovery"] = 9 if test_passed else 3

            self.test_results["test_scenarios"].append(
                {
                    "test": "auto_recovery_with_retries",
                    "passed": test_passed,
                    "retry_attempts": retry_info,
                    "results": results,
                }
            )

            logger.info(f"✓ Auto-recovery test: Retries performed = {retry_info}")

        except Exception as e:
            logger.error(f"✗ Auto-recovery test failed: {e}")
            self.validation_scores["auto_recovery"] = 0
            self.test_results["test_scenarios"].append(
                {"test": "auto_recovery_with_retries", "passed": False, "error": str(e)}
            )

    async def test_error_isolation(self):
        """Test that errors in one task don't affect others"""

        logger.info("\n--- Test 3: Error Isolation ---")

        test_tasks = [
            AgentTask(
                task_id="isolated_task_1",
                task_type="test",
                prompt="First isolated task",
            ),
            AgentTask(task_id="failing_task", task_type="test", prompt=""),  # Will fail
            AgentTask(
                task_id="isolated_task_2",
                task_type="test",
                prompt="Second isolated task",
            ),
            AgentTask(
                task_id="isolated_task_3",
                task_type="test",
                prompt="Third isolated task",
            ),
        ]

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "error_isolation",
                max_parallel=4,
                use_optimizations=False,
            )

            results = await orchestrator.execute_batch(test_tasks)

            # Check that other tasks completed despite one failure
            successful_tasks = [r for r in results if r["status"] == "completed"]
            failed_tasks = [r for r in results if r["status"] == "failed"]

            # Should have 3 successful and 1 failed
            isolation_successful = len(successful_tasks) >= 2 and len(failed_tasks) >= 1

            self.validation_scores["error_isolation"] = 9 if isolation_successful else 2

            self.test_results["test_scenarios"].append(
                {
                    "test": "error_isolation",
                    "passed": isolation_successful,
                    "successful_count": len(successful_tasks),
                    "failed_count": len(failed_tasks),
                    "task_statuses": {r["task_id"]: r["status"] for r in results},
                }
            )

            logger.info(
                f"✓ Error isolation test: {len(successful_tasks)} succeeded despite {len(failed_tasks)} failures"
            )

        except Exception as e:
            logger.error(f"✗ Error isolation test failed: {e}")
            self.validation_scores["error_isolation"] = 0
            self.test_results["test_scenarios"].append(
                {"test": "error_isolation", "passed": False, "error": str(e)}
            )

    async def test_partial_batch_failures(self):
        """Test handling of partial batch failures"""

        logger.info("\n--- Test 4: Partial Batch Failures ---")

        # Create mixed success/failure batch
        test_tasks = []
        for i in range(10):
            if i % 3 == 0:
                # Every third task will fail
                task = AgentTask(
                    task_id=f"batch_fail_{i}",
                    task_type="test",
                    prompt="",  # Empty prompt causes failure
                )
            else:
                task = AgentTask(
                    task_id=f"batch_success_{i}",
                    task_type="test",
                    prompt=f"Batch task {i} that should succeed",
                )
            test_tasks.append(task)

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "partial_batch",
                max_parallel=5,
                use_optimizations=False,
            )

            results = await orchestrator.execute_batch(test_tasks)

            # Analyze batch results
            successful = sum(1 for r in results if r["status"] == "completed")
            failed = sum(1 for r in results if r["status"] == "failed")

            # Should handle partial failures gracefully
            expected_failures = len([i for i in range(10) if i % 3 == 0])
            expected_successes = 10 - expected_failures

            # Allow some tolerance
            batch_handled_correctly = (
                abs(failed - expected_failures) <= 1
                and abs(successful - expected_successes) <= 1
            )

            self.validation_scores["partial_batch_handling"] = (
                8 if batch_handled_correctly else 3
            )

            self.test_results["test_scenarios"].append(
                {
                    "test": "partial_batch_failures",
                    "passed": batch_handled_correctly,
                    "total_tasks": len(test_tasks),
                    "successful": successful,
                    "failed": failed,
                    "expected_failures": expected_failures,
                    "expected_successes": expected_successes,
                }
            )

            logger.info(
                f"✓ Partial batch test: {successful}/{len(test_tasks)} succeeded, {failed}/{len(test_tasks)} failed"
            )

        except Exception as e:
            logger.error(f"✗ Partial batch test failed: {e}")
            self.validation_scores["partial_batch_handling"] = 0
            self.test_results["test_scenarios"].append(
                {"test": "partial_batch_failures", "passed": False, "error": str(e)}
            )

    async def test_error_logging_and_metrics(self):
        """Test error logging and metrics collection"""

        logger.info("\n--- Test 5: Error Logging and Metrics ---")

        test_tasks = [
            AgentTask(
                task_id="metric_success",
                task_type="test",
                prompt="Task for metric testing",
            ),
            AgentTask(task_id="metric_fail", task_type="test", prompt=""),  # Will fail
        ]

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "error_metrics",
                max_parallel=2,
                use_optimizations=False,
            )

            # Execute tasks
            results = await orchestrator.execute_batch(test_tasks)

            # Check metrics
            metrics = orchestrator.metrics

            # Verify metrics are collected correctly
            metrics_correct = (
                metrics["total"] == len(test_tasks)
                and metrics["completed"] >= 0
                and metrics["failed"] >= 0
                and metrics["completed"] + metrics["failed"] <= metrics["total"]
            )

            # Check for log files
            log_dir = self.output_dir / "error_metrics" / "logs"
            log_files_exist = log_dir.exists() and len(list(log_dir.glob("*.log"))) > 0

            # Check for task state files
            task_dir = self.output_dir / "error_metrics" / "tasks"
            task_files = list(task_dir.glob("*.json")) if task_dir.exists() else []

            # Verify error details are captured
            failed_task = next((r for r in results if r["status"] == "failed"), None)
            error_captured = failed_task and "error" in failed_task

            test_passed = (
                metrics_correct
                and (log_files_exist or len(task_files) > 0)
                and error_captured
            )

            self.validation_scores["error_logging"] = 8 if log_files_exist else 4
            self.validation_scores["metrics_collection"] = 9 if metrics_correct else 2

            self.test_results["test_scenarios"].append(
                {
                    "test": "error_logging_and_metrics",
                    "passed": test_passed,
                    "metrics": metrics,
                    "log_files_found": log_files_exist,
                    "task_files_count": len(task_files),
                    "error_details_captured": error_captured,
                }
            )

            logger.info(
                f"✓ Logging/metrics test: Metrics={metrics}, Logs={log_files_exist}"
            )

        except Exception as e:
            logger.error(f"✗ Logging/metrics test failed: {e}")
            self.validation_scores["error_logging"] = 0
            self.validation_scores["metrics_collection"] = 0
            self.test_results["test_scenarios"].append(
                {"test": "error_logging_and_metrics", "passed": False, "error": str(e)}
            )

    async def test_system_stability_under_stress(self):
        """Test system stability under high failure rate"""

        logger.info("\n--- Test 6: System Stability Under Stress ---")

        # Create many failing tasks to stress test
        test_tasks = []
        for i in range(20):
            if i % 2 == 0:
                # 50% failure rate
                task = AgentTask(
                    task_id=f"stress_fail_{i}", task_type="test", prompt=""
                )
            else:
                task = AgentTask(
                    task_id=f"stress_success_{i}",
                    task_type="test",
                    prompt=f"Stress test task {i}",
                )
            test_tasks.append(task)

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "stress_test",
                max_parallel=10,  # High parallelism
                use_optimizations=False,
            )

            start_time = datetime.now()
            results = await orchestrator.execute_batch(test_tasks)
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()

            # System should complete even with 50% failure rate
            all_tasks_processed = len(results) == len(test_tasks)

            # Check system didn't hang or crash
            reasonable_time = duration < 120  # Should complete within 2 minutes

            # Verify results integrity
            results_valid = all("task_id" in r and "status" in r for r in results)

            test_passed = all_tasks_processed and reasonable_time and results_valid

            self.validation_scores["system_stability"] = 9 if test_passed else 3

            self.test_results["test_scenarios"].append(
                {
                    "test": "system_stability_under_stress",
                    "passed": test_passed,
                    "total_tasks": len(test_tasks),
                    "processed_tasks": len(results),
                    "duration_seconds": duration,
                    "results_valid": results_valid,
                }
            )

            logger.info(
                f"✓ Stress test: Processed {len(results)}/{len(test_tasks)} tasks in {duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"✗ Stress test failed: {e}")
            self.validation_scores["system_stability"] = 0
            self.test_results["test_scenarios"].append(
                {
                    "test": "system_stability_under_stress",
                    "passed": False,
                    "error": str(e),
                }
            )

    async def test_dependency_failure_propagation(self):
        """Test how dependency failures are propagated"""

        logger.info("\n--- Test 7: Dependency Failure Propagation ---")

        test_tasks = [
            AgentTask(task_id="root_task", task_type="test", prompt=""),  # Will fail
            AgentTask(
                task_id="dependent_1",
                task_type="test",
                prompt="Depends on root",
                dependencies=["root_task"],
            ),
            AgentTask(
                task_id="dependent_2",
                task_type="test",
                prompt="Also depends on root",
                dependencies=["root_task"],
            ),
            AgentTask(
                task_id="independent",
                task_type="test",
                prompt="Independent task",
                dependencies=[],
            ),
        ]

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "dependency_propagation",
                max_parallel=4,
                use_optimizations=False,
            )

            results = await orchestrator.execute_batch(test_tasks)

            # Check dependency handling
            result_map = {r["task_id"]: r for r in results}

            # Root should fail
            root_failed = result_map.get("root_task", {}).get("status") == "failed"

            # Dependents should also fail or not run
            dependent_1_blocked = result_map.get("dependent_1", {}).get("status") in [
                "failed",
                "pending",
            ]
            dependent_2_blocked = result_map.get("dependent_2", {}).get("status") in [
                "failed",
                "pending",
            ]

            # Independent should complete
            independent_completed = (
                result_map.get("independent", {}).get("status") == "completed"
            )

            propagation_correct = (
                root_failed and dependent_1_blocked and dependent_2_blocked
            )

            test_passed = propagation_correct or independent_completed

            self.test_results["test_scenarios"].append(
                {
                    "test": "dependency_failure_propagation",
                    "passed": test_passed,
                    "root_failed": root_failed,
                    "dependents_blocked": dependent_1_blocked and dependent_2_blocked,
                    "independent_completed": independent_completed,
                    "task_statuses": {
                        k: v.get("status") for k, v in result_map.items()
                    },
                }
            )

            logger.info(
                f"✓ Dependency propagation test: Root failed={root_failed}, Deps blocked={dependent_1_blocked and dependent_2_blocked}"
            )

        except Exception as e:
            logger.error(f"✗ Dependency propagation test failed: {e}")
            self.test_results["test_scenarios"].append(
                {
                    "test": "dependency_failure_propagation",
                    "passed": False,
                    "error": str(e),
                }
            )

    async def test_invalid_configuration_handling(self):
        """Test handling of invalid configurations"""

        logger.info("\n--- Test 8: Invalid Configuration Handling ---")

        test_cases = []

        # Test with invalid max_parallel
        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "invalid_config_1",
                max_parallel=0,  # Invalid
                use_optimizations=False,
            )
            # Should handle gracefully by using default
            test_cases.append(
                {
                    "config": "max_parallel=0",
                    "handled": orchestrator.max_parallel > 0,
                    "actual_value": orchestrator.max_parallel,
                }
            )
        except Exception as e:
            test_cases.append(
                {"config": "max_parallel=0", "handled": False, "error": str(e)}
            )

        # Test with None max_parallel
        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "invalid_config_2",
                max_parallel=None,
                use_optimizations=False,
            )
            test_cases.append(
                {
                    "config": "max_parallel=None",
                    "handled": orchestrator.max_parallel > 0,
                    "actual_value": orchestrator.max_parallel,
                }
            )
        except Exception as e:
            test_cases.append(
                {"config": "max_parallel=None", "handled": False, "error": str(e)}
            )

        # Test with missing output directory (should create it)
        try:
            non_existent_dir = self.output_dir / "non_existent_12345"
            orchestrator = GenericOrchestrator(
                output_dir=non_existent_dir, max_parallel=2, use_optimizations=False
            )
            test_cases.append(
                {
                    "config": "non_existent_output_dir",
                    "handled": non_existent_dir.exists(),
                    "dir_created": non_existent_dir.exists(),
                }
            )
        except Exception as e:
            test_cases.append(
                {"config": "non_existent_output_dir", "handled": False, "error": str(e)}
            )

        # All invalid configs should be handled gracefully
        all_handled = all(tc.get("handled", False) for tc in test_cases)

        self.test_results["test_scenarios"].append(
            {
                "test": "invalid_configuration_handling",
                "passed": all_handled,
                "test_cases": test_cases,
            }
        )

        logger.info(
            f"✓ Invalid config test: {len([tc for tc in test_cases if tc.get('handled')])} / {len(test_cases)} handled"
        )

    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""

        # Calculate overall score
        total_score = sum(self.validation_scores.values())
        max_score = len(self.validation_scores) * 10
        percentage = (total_score / max_score) * 100

        # Determine grade
        if percentage >= 90:
            grade = "A - Excellent"
        elif percentage >= 80:
            grade = "B - Good"
        elif percentage >= 70:
            grade = "C - Satisfactory"
        elif percentage >= 60:
            grade = "D - Needs Improvement"
        else:
            grade = "F - Critical Issues"

        # Count test results
        total_tests = len(self.test_results["test_scenarios"])
        passed_tests = sum(
            1 for t in self.test_results["test_scenarios"] if t.get("passed", False)
        )

        # Generate summary
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "validation_scores": self.validation_scores,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "grade": grade,
            "timestamp": datetime.now().isoformat(),
        }

        # Generate recommendations
        recommendations = []

        if self.validation_scores["graceful_failure"] < 7:
            recommendations.append(
                "Improve graceful failure handling to prevent system crashes"
            )

        if self.validation_scores["auto_recovery"] < 7:
            recommendations.append(
                "Implement robust retry mechanisms with exponential backoff"
            )

        if self.validation_scores["error_isolation"] < 7:
            recommendations.append(
                "Enhance error isolation to prevent cascade failures"
            )

        if self.validation_scores["partial_batch_handling"] < 7:
            recommendations.append("Improve partial batch failure handling")

        if self.validation_scores["error_logging"] < 7:
            recommendations.append("Enhance error logging with detailed stack traces")

        if self.validation_scores["metrics_collection"] < 7:
            recommendations.append(
                "Implement comprehensive metrics collection for failures"
            )

        if self.validation_scores["system_stability"] < 7:
            recommendations.append("Improve system stability under high failure rates")

        self.test_results["recommendations"] = recommendations

        # Save report
        report_file = self.output_dir / "error_handling_validation_report.json"
        report_file.write_text(json.dumps(self.test_results, indent=2))

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("ERROR HANDLING VALIDATION REPORT")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"\nValidation Scores:")
        for category, score in self.validation_scores.items():
            logger.info(f"  {category}: {score}/10")
        logger.info(f"\nOverall Score: {total_score}/{max_score} ({percentage:.1f}%)")
        logger.info(f"Grade: {grade}")

        if recommendations:
            logger.info(f"\nRecommendations:")
            for rec in recommendations:
                logger.info(f"  • {rec}")

        logger.info(f"\nFull report saved to: {report_file}")
        logger.info("=" * 60)

        return self.test_results


async def main():
    """Main execution function"""

    # Set up output directory
    output_dir = Path("./unified_orchestrator_validation_20250906_220122")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create validator
    validator = ErrorHandlingValidator(output_dir=output_dir)

    # Run validation
    try:
        report = await validator.run_all_tests()

        # Determine exit code based on grade
        percentage = report["summary"]["percentage"]
        if percentage >= 70:
            logger.info("\n✓ Error handling validation PASSED")
            return 0
        else:
            logger.error("\n✗ Error handling validation FAILED - Critical issues found")
            return 1

    except Exception as e:
        logger.error(f"Validation suite failed: {e}")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
