#!/usr/bin/env python3
"""
Comprehensive Agent Orchestrator Validation Suite
Tests core orchestration functionality including token management,
parallel execution, dependencies, and metrics collection.
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.generic_orchestrator import AgentTask, TokenPool
from src.unified.unified_orchestrator import (
    EnhancedAgentTask,
    FeatureFlag,
    UnifiedConfig,
    UnifiedOrchestrator,
    create_minimal_orchestrator,
    create_standard_orchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationTestSuite:
    """Comprehensive validation test suite for orchestrator"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.results = {"tests": {}, "metrics": {}, "errors": [], "summary": {}}
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self) -> Dict:
        """Run all validation tests"""
        self.start_time = datetime.now()

        print("\n" + "=" * 80)
        print("AGENT ORCHESTRATOR VALIDATION SUITE")
        print("=" * 80)

        # Test 1: Simple task execution with token management
        await self.test_simple_task_execution()

        # Test 2: Parallel execution with max_parallel limits
        await self.test_parallel_execution()

        # Test 3: Task dependencies (A→B→C chain)
        await self.test_task_dependencies()

        # Test 4: Token pool management
        await self.test_token_management()

        # Test 5: Metrics collection
        await self.test_metrics_collection()

        # Test 6: Output directory structure
        await self.test_output_structure()

        # Test 7: Error handling and recovery
        await self.test_error_handling()

        # Test 8: Mixed execution modes
        await self.test_mixed_execution()

        self.end_time = datetime.now()

        # Generate summary
        self.generate_summary()

        # Save report
        self.save_report()

        return self.results

    async def test_simple_task_execution(self):
        """Test 1: Simple task execution with token management"""
        test_name = "simple_task_execution"
        print(f"\n[TEST 1] Testing {test_name}...")

        try:
            # Create orchestrator with minimal config
            orchestrator = create_minimal_orchestrator(
                output_dir=self.output_dir / test_name,
                max_parallel=3,
                tokens=["token1", "token2", "token3"],
            )

            # Create simple tasks
            def generate_tasks():
                tasks = []
                for i in range(3):
                    task = AgentTask(
                        task_id=f"simple_task_{i}",
                        task_type="test",
                        prompt=f"Execute simple task {i}",
                        context={"test": True, "index": i},
                    )
                    tasks.append(task)
                return tasks

            # Execute tasks
            start = time.time()
            result = await orchestrator.run(task_generator=generate_tasks)
            duration = time.time() - start

            # Validate results
            passed = (
                result["metrics"]["total"] == 3
                and result["metrics"]["completed"] == 3
                and result["metrics"]["failed"] == 0
            )

            self.results["tests"][test_name] = {
                "passed": passed,
                "duration": duration,
                "details": {
                    "total_tasks": result["metrics"]["total"],
                    "completed": result["metrics"]["completed"],
                    "failed": result["metrics"]["failed"],
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_parallel_execution(self):
        """Test 2: Parallel execution with max_parallel limits"""
        test_name = "parallel_execution"
        print(f"\n[TEST 2] Testing {test_name}...")

        try:
            max_parallel = 2
            num_tasks = 6

            # Create orchestrator with parallel limit
            orchestrator = create_minimal_orchestrator(
                output_dir=self.output_dir / test_name,
                max_parallel=max_parallel,
                tokens=["token1", "token2"],
            )

            # Track concurrent executions
            concurrent_count = 0
            max_concurrent = 0
            lock = asyncio.Lock()

            # Create tasks that track concurrency
            def generate_tasks():
                tasks = []
                for i in range(num_tasks):
                    task = AgentTask(
                        task_id=f"parallel_task_{i}",
                        task_type="parallel_test",
                        prompt=f"Parallel task {i}",
                        context={"delay": 0.1},  # Small delay to test concurrency
                    )
                    tasks.append(task)
                return tasks

            # Monkey-patch execute to track concurrency
            original_execute = orchestrator.execute_agent

            async def tracked_execute(task):
                nonlocal concurrent_count, max_concurrent

                async with lock:
                    concurrent_count += 1
                    max_concurrent = max(max_concurrent, concurrent_count)

                # Simulate work
                await asyncio.sleep(0.1)
                result = await original_execute(task)

                async with lock:
                    concurrent_count -= 1

                return result

            orchestrator.execute_agent = tracked_execute

            # Execute tasks
            start = time.time()
            result = await orchestrator.run(task_generator=generate_tasks)
            duration = time.time() - start

            # Validate results
            passed = (
                max_concurrent <= max_parallel
                and result["metrics"]["completed"] == num_tasks
            )

            self.results["tests"][test_name] = {
                "passed": passed,
                "duration": duration,
                "details": {
                    "max_parallel_limit": max_parallel,
                    "max_concurrent_observed": max_concurrent,
                    "total_tasks": num_tasks,
                    "completed": result["metrics"]["completed"],
                },
            }

            print(
                f"✓ Test passed (max concurrent: {max_concurrent}/{max_parallel})"
                if passed
                else f"✗ Test failed"
            )

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_task_dependencies(self):
        """Test 3: Task dependencies (A→B→C chain)"""
        test_name = "task_dependencies"
        print(f"\n[TEST 3] Testing {test_name}...")

        try:
            # Create orchestrator
            orchestrator = create_minimal_orchestrator(
                output_dir=self.output_dir / test_name, max_parallel=3
            )

            # Track execution order
            execution_order = []

            # Create tasks with dependencies
            def generate_tasks():
                tasks = [
                    AgentTask(
                        task_id="task_A",
                        task_type="dependency_test",
                        prompt="Task A (no dependencies)",
                        dependencies=[],
                    ),
                    AgentTask(
                        task_id="task_B",
                        task_type="dependency_test",
                        prompt="Task B (depends on A)",
                        dependencies=["task_A"],
                    ),
                    AgentTask(
                        task_id="task_C",
                        task_type="dependency_test",
                        prompt="Task C (depends on B)",
                        dependencies=["task_B"],
                    ),
                ]
                return tasks

            # Monkey-patch to track execution order
            original_execute = orchestrator.execute_agent

            async def tracked_execute(task):
                execution_order.append(task.task_id)
                return await original_execute(task)

            orchestrator.execute_agent = tracked_execute

            # Execute tasks
            start = time.time()
            result = await orchestrator.run(task_generator=generate_tasks)
            duration = time.time() - start

            # Validate execution order
            expected_order = ["task_A", "task_B", "task_C"]
            order_correct = execution_order == expected_order

            passed = order_correct and result["metrics"]["completed"] == 3

            self.results["tests"][test_name] = {
                "passed": passed,
                "duration": duration,
                "details": {
                    "expected_order": expected_order,
                    "actual_order": execution_order,
                    "order_correct": order_correct,
                    "completed": result["metrics"]["completed"],
                },
            }

            print(
                f"✓ Test passed (order: {' → '.join(execution_order)})"
                if passed
                else f"✗ Test failed"
            )

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_token_management(self):
        """Test 4: Token pool management"""
        test_name = "token_management"
        print(f"\n[TEST 4] Testing {test_name}...")

        try:
            tokens = ["token_alpha", "token_beta", "token_gamma"]

            # Create orchestrator with specific tokens
            orchestrator = create_minimal_orchestrator(
                output_dir=self.output_dir / test_name, max_parallel=3, tokens=tokens
            )

            # Track token usage
            token_usage = {}

            # Create tasks
            def generate_tasks():
                tasks = []
                for i in range(6):
                    task = AgentTask(
                        task_id=f"token_task_{i}",
                        task_type="token_test",
                        prompt=f"Task using token {i}",
                    )
                    tasks.append(task)
                return tasks

            # Monkey-patch to track token usage
            original_acquire = orchestrator.token_pool.acquire

            async def tracked_acquire():
                token = await original_acquire()
                if token not in token_usage:
                    token_usage[token] = 0
                token_usage[token] += 1
                return token

            orchestrator.token_pool.acquire = tracked_acquire

            # Execute tasks
            result = await orchestrator.run(task_generator=generate_tasks)

            # Validate token management
            all_tokens_used = all(t in token_usage for t in tokens)
            no_oversubscription = orchestrator.token_pool.available <= len(tokens)

            passed = (
                all_tokens_used
                and no_oversubscription
                and result["metrics"]["completed"] == 6
            )

            self.results["tests"][test_name] = {
                "passed": passed,
                "details": {
                    "tokens_provided": tokens,
                    "token_usage": token_usage,
                    "all_tokens_used": all_tokens_used,
                    "no_oversubscription": no_oversubscription,
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_metrics_collection(self):
        """Test 5: Metrics collection"""
        test_name = "metrics_collection"
        print(f"\n[TEST 5] Testing {test_name}...")

        try:
            # Create orchestrator with enhanced metrics
            config = UnifiedConfig(
                output_dir=self.output_dir / test_name,
                max_parallel=3,
                enabled_features={FeatureFlag.ENHANCED_METRICS},
            )
            orchestrator = UnifiedOrchestrator(config)

            # Create tasks with different types
            def generate_tasks():
                tasks = []
                task_types = ["analysis", "generation", "validation"]

                for i in range(9):
                    task = EnhancedAgentTask(
                        task_id=f"metrics_task_{i}",
                        task_type=task_types[i % 3],
                        prompt=f"Task for metrics {i}",
                        priority=i % 3,
                    )
                    tasks.append(task)
                return tasks

            # Execute tasks
            result = await orchestrator.run(task_generator=generate_tasks)

            # Validate metrics
            has_basic_metrics = all(
                k in result["metrics"]
                for k in ["total", "completed", "failed", "duration"]
            )

            has_enhanced_metrics = "enhanced_metrics" in result

            if has_enhanced_metrics:
                em = result["enhanced_metrics"]
                has_type_breakdown = "tasks_by_type" in em
                has_status_breakdown = "tasks_by_status" in em
            else:
                has_type_breakdown = False
                has_status_breakdown = False

            passed = (
                has_basic_metrics
                and has_enhanced_metrics
                and has_type_breakdown
                and has_status_breakdown
            )

            self.results["tests"][test_name] = {
                "passed": passed,
                "details": {
                    "has_basic_metrics": has_basic_metrics,
                    "has_enhanced_metrics": has_enhanced_metrics,
                    "has_type_breakdown": has_type_breakdown,
                    "has_status_breakdown": has_status_breakdown,
                    "metrics": result.get("metrics", {}),
                    "enhanced_metrics": result.get("enhanced_metrics", {}),
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_output_structure(self):
        """Test 6: Output directory structure"""
        test_name = "output_structure"
        print(f"\n[TEST 6] Testing {test_name}...")

        try:
            test_dir = self.output_dir / test_name

            # Create orchestrator
            orchestrator = create_standard_orchestrator(
                output_dir=test_dir, max_parallel=2
            )

            # Create a simple task
            def generate_tasks():
                return [
                    AgentTask(
                        task_id="output_test",
                        task_type="test",
                        prompt="Test output structure",
                    )
                ]

            # Execute
            await orchestrator.run(task_generator=generate_tasks)

            # Check expected directories
            expected_dirs = ["tasks", "logs", "metrics"]
            dirs_exist = {}

            for dir_name in expected_dirs:
                dir_path = test_dir / dir_name
                dirs_exist[dir_name] = dir_path.exists() and dir_path.is_dir()

            # Check for output files
            has_task_files = len(list((test_dir / "tasks").glob("*.json"))) > 0
            has_report_files = len(list(test_dir.glob("*.json"))) > 0

            passed = all(dirs_exist.values()) and has_task_files and has_report_files

            self.results["tests"][test_name] = {
                "passed": passed,
                "details": {
                    "directories_exist": dirs_exist,
                    "has_task_files": has_task_files,
                    "has_report_files": has_report_files,
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_error_handling(self):
        """Test 7: Error handling and recovery"""
        test_name = "error_handling"
        print(f"\n[TEST 7] Testing {test_name}...")

        try:
            # Create orchestrator with auto-recovery
            config = UnifiedConfig(
                output_dir=self.output_dir / test_name,
                max_parallel=2,
                enabled_features={FeatureFlag.AUTO_RECOVERY},
                enable_auto_recovery=True,
                max_retries=2,
                retry_delay=0.1,
            )
            orchestrator = UnifiedOrchestrator(config)

            # Track retry attempts
            attempt_counts = {}

            # Create tasks that fail initially
            def generate_tasks():
                tasks = []
                for i in range(3):
                    task = AgentTask(
                        task_id=f"error_task_{i}",
                        task_type="error_test",
                        prompt=f"Task that may fail {i}",
                        context={"fail_count": 1 if i == 1 else 0},  # Task 1 fails once
                    )
                    tasks.append(task)
                return tasks

            # Monkey-patch to simulate failures
            original_execute = orchestrator.execute_agent

            async def failing_execute(task):
                task_id = task.task_id

                if task_id not in attempt_counts:
                    attempt_counts[task_id] = 0
                attempt_counts[task_id] += 1

                # Simulate failure for specific task on first attempt
                if task_id == "error_task_1" and attempt_counts[task_id] == 1:
                    task.status = "failed"
                    task.error = "Simulated failure"
                    return task.to_dict()

                return await original_execute(task)

            orchestrator.execute_agent = failing_execute

            # Execute tasks
            result = await orchestrator.run(task_generator=generate_tasks)

            # Validate error handling
            recovery_occurred = attempt_counts.get("error_task_1", 0) > 1
            all_completed = result["metrics"]["completed"] == 3

            passed = recovery_occurred and all_completed

            self.results["tests"][test_name] = {
                "passed": passed,
                "details": {
                    "attempt_counts": attempt_counts,
                    "recovery_occurred": recovery_occurred,
                    "all_completed": all_completed,
                    "final_metrics": result["metrics"],
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    async def test_mixed_execution(self):
        """Test 8: Mixed execution modes (parallel + sequential)"""
        test_name = "mixed_execution"
        print(f"\n[TEST 8] Testing {test_name}...")

        try:
            # Create orchestrator
            orchestrator = create_standard_orchestrator(
                output_dir=self.output_dir / test_name, max_parallel=3
            )

            # Track execution timing
            task_timings = {}

            # Create mixed tasks
            def generate_tasks():
                tasks = []

                # Group 1: Can run in parallel
                for i in range(3):
                    task = EnhancedAgentTask(
                        task_id=f"parallel_group_{i}",
                        task_type="parallel",
                        prompt=f"Parallel task {i}",
                        execution_mode="parallel",
                    )
                    tasks.append(task)

                # Group 2: Sequential chain
                tasks.append(
                    EnhancedAgentTask(
                        task_id="sequential_1",
                        task_type="sequential",
                        prompt="Sequential task 1",
                        dependencies=[
                            "parallel_group_0",
                            "parallel_group_1",
                            "parallel_group_2",
                        ],
                        execution_mode="sequential",
                    )
                )

                tasks.append(
                    EnhancedAgentTask(
                        task_id="sequential_2",
                        task_type="sequential",
                        prompt="Sequential task 2",
                        dependencies=["sequential_1"],
                        execution_mode="sequential",
                    )
                )

                return tasks

            # Monkey-patch to track timing
            original_execute = orchestrator.execute_agent

            async def timed_execute(task):
                start = time.time()
                result = await original_execute(task)
                task_timings[task.task_id] = {
                    "start": start,
                    "duration": time.time() - start,
                }
                return result

            orchestrator.execute_agent = timed_execute

            # Execute tasks
            result = await orchestrator.run(task_generator=generate_tasks)

            # Validate mixed execution
            parallel_completed = all(
                f"parallel_group_{i}" in task_timings for i in range(3)
            )

            sequential_completed = all(
                f"sequential_{i}" in task_timings for i in range(1, 3)
            )

            passed = (
                parallel_completed
                and sequential_completed
                and result["metrics"]["completed"] == 5
            )

            self.results["tests"][test_name] = {
                "passed": passed,
                "details": {
                    "parallel_tasks_completed": parallel_completed,
                    "sequential_tasks_completed": sequential_completed,
                    "total_completed": result["metrics"]["completed"],
                    "task_count": len(task_timings),
                },
            }

            print(f"✓ Test passed" if passed else f"✗ Test failed")

        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            self.results["tests"][test_name] = {"passed": False, "error": str(e)}
            self.results["errors"].append(f"{test_name}: {e}")

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results["tests"])
        passed_tests = sum(
            1 for t in self.results["tests"].values() if t.get("passed", False)
        )
        failed_tests = total_tests - passed_tests

        # Calculate score
        score = round((passed_tests / total_tests) * 10) if total_tests > 0 else 0

        # Performance metrics
        total_duration = (self.end_time - self.start_time).total_seconds()

        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
            if total_tests > 0
            else "0%",
            "functionality_score": score,
            "total_duration": total_duration,
            "errors_count": len(self.results["errors"]),
            "timestamp": datetime.now().isoformat(),
        }

        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {self.results['summary']['success_rate']}")
        print(f"Functionality Score: {score}/10")
        print(f"Total Duration: {total_duration:.2f} seconds")

        if self.results["errors"]:
            print(f"\nErrors ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"  - {error}")

        # Print failed tests
        failed = [
            name
            for name, result in self.results["tests"].items()
            if not result.get("passed", False)
        ]
        if failed:
            print(f"\nFailed Tests:")
            for test_name in failed:
                print(f"  - {test_name}")

    def save_report(self):
        """Save validation report"""
        report_file = (
            self.output_dir
            / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\nReport saved to: {report_file}")

        # Also save a summary file
        summary_file = self.output_dir / "validation_summary.txt"
        with open(summary_file, "w") as f:
            f.write("AGENT ORCHESTRATOR VALIDATION REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total Tests: {self.results['summary']['total_tests']}\n")
            f.write(f"Passed: {self.results['summary']['passed']}\n")
            f.write(f"Failed: {self.results['summary']['failed']}\n")
            f.write(f"Success Rate: {self.results['summary']['success_rate']}\n")
            f.write(
                f"Functionality Score: {self.results['summary']['functionality_score']}/10\n"
            )
            f.write(
                f"Duration: {self.results['summary']['total_duration']:.2f} seconds\n"
            )

            f.write("\n\nTest Results:\n")
            f.write("-" * 40 + "\n")
            for test_name, result in self.results["tests"].items():
                status = "PASS" if result.get("passed", False) else "FAIL"
                f.write(f"{test_name}: {status}\n")

            if self.results["errors"]:
                f.write("\n\nErrors:\n")
                f.write("-" * 40 + "\n")
                for error in self.results["errors"]:
                    f.write(f"- {error}\n")


async def main():
    """Main validation function"""
    # Create output directory for validation
    output_dir = Path("validation_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run validation suite
    suite = ValidationTestSuite(output_dir)
    results = await suite.run_all_tests()

    # Return score for external use
    return results["summary"]["functionality_score"]


if __name__ == "__main__":
    score = asyncio.run(main())
    sys.exit(0 if score >= 7 else 1)  # Exit with error if score < 7
