#!/usr/bin/env python3
"""
Resource Management Validation Suite
Tests token pool, resource allocation, and cleanup mechanisms
"""

import asyncio
import gc
import json
import logging
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.enhanced_orchestrator import EnhancedOrchestrator
from src.generic_orchestrator import AgentTask, GenericOrchestrator, TokenPool

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Track resource usage metrics"""

    timestamp: float
    memory_mb: float
    cpu_percent: float
    open_files: int
    threads: int
    tokens_in_use: int
    tasks_running: int
    tasks_completed: int
    tasks_failed: int


@dataclass
class ValidationReport:
    """Resource management validation report"""

    test_name: str
    passed: bool
    score: float  # 0-10
    metrics: List[ResourceMetrics] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    duration: float = 0.0
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    token_efficiency: float = 0.0  # % of time tokens were utilized
    resource_leaks: List[str] = field(default_factory=list)


class ResourceManagementValidator:
    """Validates resource management in orchestrator"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.process = psutil.Process()
        self.reports: List[ValidationReport] = []
        self.baseline_memory = None
        self.monitoring = True
        self.metrics_history: List[ResourceMetrics] = []

    def get_current_metrics(self, orchestrator=None) -> ResourceMetrics:
        """Capture current resource metrics"""
        mem_info = self.process.memory_info()

        tokens_in_use = 0
        if orchestrator and hasattr(orchestrator, "token_pool"):
            tokens_in_use = len(orchestrator.token_pool.in_use)

        tasks_running = 0
        tasks_completed = 0
        tasks_failed = 0
        if orchestrator and hasattr(orchestrator, "dep_manager"):
            tasks_running = len(orchestrator.dep_manager.running)
            tasks_completed = len(orchestrator.dep_manager.completed)
            tasks_failed = len(orchestrator.dep_manager.failed)

        return ResourceMetrics(
            timestamp=time.time(),
            memory_mb=mem_info.rss / 1024 / 1024,
            cpu_percent=self.process.cpu_percent(),
            open_files=len(self.process.open_files()),
            threads=self.process.num_threads(),
            tokens_in_use=tokens_in_use,
            tasks_running=tasks_running,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
        )

    async def monitor_resources(self, orchestrator, interval=0.5):
        """Background resource monitoring"""
        while self.monitoring:
            metrics = self.get_current_metrics(orchestrator)
            self.metrics_history.append(metrics)
            await asyncio.sleep(interval)

    def analyze_metrics(self, metrics: List[ResourceMetrics]) -> Dict[str, Any]:
        """Analyze collected metrics"""
        if not metrics:
            return {}

        memory_values = [m.memory_mb for m in metrics]
        cpu_values = [m.cpu_percent for m in metrics]
        token_values = [m.tokens_in_use for m in metrics]

        # Calculate token efficiency
        total_time = (
            metrics[-1].timestamp - metrics[0].timestamp if len(metrics) > 1 else 0
        )
        token_busy_time = (
            sum(1 for m in metrics if m.tokens_in_use > 0) * 0.5
        )  # monitoring interval
        token_efficiency = (token_busy_time / total_time * 100) if total_time > 0 else 0

        return {
            "peak_memory_mb": max(memory_values),
            "avg_memory_mb": sum(memory_values) / len(memory_values),
            "min_memory_mb": min(memory_values),
            "memory_growth_mb": memory_values[-1] - memory_values[0],
            "peak_cpu_percent": max(cpu_values),
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "max_tokens_used": max(token_values),
            "token_efficiency": token_efficiency,
            "total_duration": total_time,
        }

    async def test_token_pool_limits(self) -> ValidationReport:
        """Test token pool properly limits concurrent execution"""
        report = ValidationReport(
            test_name="Token Pool Limits", passed=True, score=10.0
        )
        start_time = time.time()

        try:
            # Create orchestrator with limited tokens
            test_tokens = ["token1", "token2", "token3"]  # Only 3 tokens
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "token_pool_test",
                max_parallel=10,  # Request more than available tokens
                tokens=test_tokens,
            )

            # Create 10 tasks that should execute with only 3 tokens
            tasks = []
            for i in range(10):
                tasks.append(
                    AgentTask(
                        task_id=f"token_test_{i}",
                        task_type="test",
                        prompt=f"Simple test task {i} - just respond with 'ok'",
                    )
                )

            # Monitor execution
            monitor_task = asyncio.create_task(self.monitor_resources(orchestrator))

            # Execute tasks
            results = await orchestrator.execute_batch(tasks)

            # Stop monitoring
            self.monitoring = False
            await monitor_task

            # Analyze token usage
            analysis = self.analyze_metrics(self.metrics_history)

            # Verify constraints
            if analysis["max_tokens_used"] > len(test_tokens):
                report.issues.append(
                    f"Token pool exceeded limit: {analysis['max_tokens_used']} > {len(test_tokens)}"
                )
                report.score -= 5.0
                report.passed = False

            # Check if all tasks completed
            completed = sum(1 for r in results if r["status"] == "completed")
            if completed < len(tasks):
                report.issues.append(
                    f"Not all tasks completed: {completed}/{len(tasks)}"
                )
                report.score -= 2.0

            report.token_efficiency = analysis["token_efficiency"]

            # Score based on efficiency
            if analysis["token_efficiency"] < 50:
                report.issues.append(
                    f"Low token efficiency: {analysis['token_efficiency']:.1f}%"
                )
                report.score -= 1.0

        except Exception as e:
            report.passed = False
            report.score = 0.0
            report.issues.append(f"Test failed with error: {str(e)}")

        report.duration = time.time() - start_time
        report.metrics = self.metrics_history.copy()
        self.metrics_history.clear()
        self.monitoring = True

        return report

    async def test_resource_cleanup(self) -> ValidationReport:
        """Test resource cleanup after task completion and failures"""
        report = ValidationReport(test_name="Resource Cleanup", passed=True, score=10.0)
        start_time = time.time()

        try:
            # Track memory before test
            gc.collect()
            baseline = self.get_current_metrics()

            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "cleanup_test", max_parallel=5
            )

            # Create tasks with some designed to fail
            tasks = []
            for i in range(10):
                if i % 3 == 0:
                    # This task will fail
                    prompt = (
                        "INTENTIONAL_FAILURE: This task should fail - exit with error"
                    )
                else:
                    prompt = f"Simple success task {i}"

                tasks.append(
                    AgentTask(
                        task_id=f"cleanup_test_{i}", task_type="test", prompt=prompt
                    )
                )

            # Execute tasks
            results = await orchestrator.execute_batch(tasks)

            # Force garbage collection
            gc.collect()
            await asyncio.sleep(1)  # Allow cleanup

            # Check memory after
            final = self.get_current_metrics()

            memory_growth = final.memory_mb - baseline.memory_mb

            # Check for leaks
            if memory_growth > 50:  # More than 50MB growth
                report.resource_leaks.append(
                    f"Memory leak detected: {memory_growth:.1f}MB growth"
                )
                report.score -= 3.0

            # Verify token pool is empty
            if len(orchestrator.token_pool.in_use) > 0:
                report.resource_leaks.append(
                    f"Tokens not released: {len(orchestrator.token_pool.in_use)} still in use"
                )
                report.score -= 2.0
                report.passed = False

            # Check dependency manager state
            if len(orchestrator.dep_manager.running) > 0:
                report.resource_leaks.append(
                    f"Tasks still marked as running: {len(orchestrator.dep_manager.running)}"
                )
                report.score -= 2.0

        except Exception as e:
            report.passed = False
            report.score = 0.0
            report.issues.append(f"Test failed: {str(e)}")

        report.duration = time.time() - start_time
        return report

    async def stress_test_concurrent_load(self) -> ValidationReport:
        """Stress test with 20+ concurrent tasks"""
        report = ValidationReport(
            test_name="Concurrent Load Stress Test", passed=True, score=10.0
        )
        start_time = time.time()

        # Start memory tracking
        tracemalloc.start()

        try:
            orchestrator = GenericOrchestrator(
                output_dir=self.output_dir / "stress_test",
                max_parallel=5,  # Limit to 5 parallel
            )

            # Create 20 heavy tasks
            tasks = []
            for i in range(20):
                tasks.append(
                    AgentTask(
                        task_id=f"stress_{i}",
                        task_type="analysis",
                        prompt=f"Analyze this text and provide a summary: Task {i} "
                        + "x" * 100,
                    )
                )

            # Monitor during execution
            self.metrics_history.clear()
            monitor_task = asyncio.create_task(self.monitor_resources(orchestrator))

            # Execute with timeout
            try:
                results = await asyncio.wait_for(
                    orchestrator.execute_batch(tasks), timeout=300  # 5 minute timeout
                )
            except asyncio.TimeoutError:
                report.issues.append("Stress test timed out after 5 minutes")
                report.score -= 3.0
                results = []

            # Stop monitoring
            self.monitoring = False
            await monitor_task
            self.monitoring = True

            # Analyze performance
            analysis = self.analyze_metrics(self.metrics_history)

            # Check memory usage
            if analysis.get("peak_memory_mb", 0) > 1000:  # Over 1GB
                report.issues.append(
                    f"Excessive memory usage: {analysis['peak_memory_mb']:.1f}MB"
                )
                report.score -= 2.0

            if analysis.get("memory_growth_mb", 0) > 200:  # Over 200MB growth
                report.issues.append(
                    f"Memory growth: {analysis['memory_growth_mb']:.1f}MB"
                )
                report.score -= 1.0

            # Check completion rate
            completed = sum(1 for r in results if r.get("status") == "completed")
            completion_rate = (completed / len(tasks)) * 100 if tasks else 0

            if completion_rate < 80:
                report.issues.append(f"Low completion rate: {completion_rate:.1f}%")
                report.score -= 2.0

            report.peak_memory_mb = analysis.get("peak_memory_mb", 0)
            report.avg_memory_mb = analysis.get("avg_memory_mb", 0)

            # Get memory snapshot
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")[:10]

            # Check for memory hotspots
            for stat in top_stats:
                if stat.size > 50 * 1024 * 1024:  # Over 50MB
                    report.recommendations.append(f"Memory hotspot: {stat}")

        except Exception as e:
            report.passed = False
            report.score = 0.0
            report.issues.append(f"Stress test failed: {str(e)}")
        finally:
            tracemalloc.stop()

        report.duration = time.time() - start_time
        report.metrics = self.metrics_history[-100:]  # Last 100 samples

        if report.score < 5:
            report.passed = False

        return report

    async def test_dynamic_allocation(self) -> ValidationReport:
        """Test dynamic token allocation under varying load"""
        report = ValidationReport(
            test_name="Dynamic Token Allocation", passed=True, score=10.0
        )
        start_time = time.time()

        try:
            orchestrator = EnhancedOrchestrator(
                output_dir=self.output_dir / "dynamic_test",
                max_parallel=5,
                enable_monitoring=True,
            )

            # Create tasks with dependencies creating varying load
            tasks = []

            # Phase 1: Light load (3 tasks)
            for i in range(3):
                tasks.append(
                    AgentTask(
                        task_id=f"light_{i}", task_type="test", prompt=f"Light task {i}"
                    )
                )

            # Phase 2: Heavy burst (10 tasks, all depend on phase 1)
            for i in range(10):
                tasks.append(
                    AgentTask(
                        task_id=f"heavy_{i}",
                        task_type="analysis",
                        prompt=f"Heavy analysis task {i}",
                        dependencies=[f"light_{j}" for j in range(3)],
                    )
                )

            # Phase 3: Gradual decrease (5 tasks)
            for i in range(5):
                tasks.append(
                    AgentTask(
                        task_id=f"final_{i}",
                        task_type="test",
                        prompt=f"Final task {i}",
                        dependencies=[f"heavy_{i*2}"],  # Staggered dependencies
                    )
                )

            # Monitor execution
            self.metrics_history.clear()
            monitor_task = asyncio.create_task(self.monitor_resources(orchestrator))

            # Execute
            results = await orchestrator.execute_batch(tasks)

            # Stop monitoring
            self.monitoring = False
            await monitor_task
            self.monitoring = True

            # Analyze allocation patterns
            token_usage = [m.tokens_in_use for m in self.metrics_history]

            # Check if allocation adapted to load
            phase1_avg = sum(token_usage[:10]) / 10 if len(token_usage) > 10 else 0
            phase2_avg = sum(token_usage[10:30]) / 20 if len(token_usage) > 30 else 0

            if phase2_avg <= phase1_avg:
                report.issues.append(
                    "Token allocation did not scale with increased load"
                )
                report.score -= 2.0

            # Check for efficient deallocation
            idle_periods = sum(1 for usage in token_usage if usage == 0)
            if idle_periods > len(token_usage) * 0.3:  # More than 30% idle
                report.recommendations.append(
                    "Consider optimizing task scheduling to reduce idle time"
                )
                report.score -= 1.0

        except Exception as e:
            report.passed = False
            report.score = 0.0
            report.issues.append(f"Dynamic allocation test failed: {str(e)}")

        report.duration = time.time() - start_time
        return report

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all resource management validation tests"""
        logger.info("Starting Resource Management Validation Suite")

        overall_start = time.time()

        # Run tests
        tests = [
            ("Token Pool Limits", self.test_token_pool_limits),
            ("Resource Cleanup", self.test_resource_cleanup),
            ("Concurrent Load", self.stress_test_concurrent_load),
            ("Dynamic Allocation", self.test_dynamic_allocation),
        ]

        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                report = await test_func()
                self.reports.append(report)
                logger.info(
                    f"Test {test_name}: {'PASSED' if report.passed else 'FAILED'} (Score: {report.score:.1f}/10)"
                )
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {str(e)}")
                self.reports.append(
                    ValidationReport(
                        test_name=test_name,
                        passed=False,
                        score=0.0,
                        issues=[f"Test crashed: {str(e)}"],
                    )
                )

        # Generate summary
        total_score = sum(r.score for r in self.reports) / len(self.reports)
        passed_tests = sum(1 for r in self.reports if r.passed)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - overall_start,
            "total_tests": len(self.reports),
            "passed_tests": passed_tests,
            "failed_tests": len(self.reports) - passed_tests,
            "overall_score": total_score,
            "status": "PASSED" if total_score >= 7.0 else "FAILED",
            "reports": [self._report_to_dict(r) for r in self.reports],
        }

        # Save detailed report
        report_file = (
            self.output_dir
            / f"resource_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.write_text(json.dumps(summary, indent=2, default=str))

        # Generate markdown report
        self.generate_markdown_report(summary)

        return summary

    def _report_to_dict(self, report: ValidationReport) -> Dict:
        """Convert report to dictionary"""
        return {
            "test_name": report.test_name,
            "passed": report.passed,
            "score": report.score,
            "duration": report.duration,
            "issues": report.issues,
            "recommendations": report.recommendations,
            "resource_leaks": report.resource_leaks,
            "peak_memory_mb": report.peak_memory_mb,
            "avg_memory_mb": report.avg_memory_mb,
            "token_efficiency": report.token_efficiency,
        }

    def generate_markdown_report(self, summary: Dict):
        """Generate markdown report"""
        md_file = self.output_dir / "RESOURCE_VALIDATION_REPORT.md"

        content = f"""# Resource Management Validation Report

**Date**: {summary['timestamp']}
**Duration**: {summary['duration']:.2f} seconds
**Overall Score**: {summary['overall_score']:.1f}/10
**Status**: {summary['status']}

## Test Summary

| Test | Status | Score | Duration | Issues |
|------|--------|-------|----------|--------|
"""

        for report in self.reports:
            status = "✅ PASS" if report.passed else "❌ FAIL"
            content += f"| {report.test_name} | {status} | {report.score:.1f}/10 | {report.duration:.2f}s | {len(report.issues)} |\n"

        content += f"""

## Detailed Results

"""

        for report in self.reports:
            content += f"""### {report.test_name}

**Score**: {report.score:.1f}/10
**Status**: {'PASSED' if report.passed else 'FAILED'}
**Duration**: {report.duration:.2f} seconds

"""

            if report.issues:
                content += "**Issues Found**:\n"
                for issue in report.issues:
                    content += f"- {issue}\n"
                content += "\n"

            if report.resource_leaks:
                content += "**Resource Leaks**:\n"
                for leak in report.resource_leaks:
                    content += f"- 🔴 {leak}\n"
                content += "\n"

            if report.recommendations:
                content += "**Recommendations**:\n"
                for rec in report.recommendations:
                    content += f"- 💡 {rec}\n"
                content += "\n"

            if report.peak_memory_mb > 0:
                content += f"""**Memory Statistics**:
- Peak Memory: {report.peak_memory_mb:.1f} MB
- Average Memory: {report.avg_memory_mb:.1f} MB
"""

            if report.token_efficiency > 0:
                content += f"- Token Efficiency: {report.token_efficiency:.1f}%\n"

            content += "\n---\n\n"

        content += f"""## Recommendations

Based on the validation results:

"""

        if summary["overall_score"] >= 8:
            content += """✅ **Excellent Resource Management**
- The orchestrator demonstrates robust resource management
- Token pool properly limits concurrent execution
- No significant resource leaks detected
- System maintains stability under load
"""
        elif summary["overall_score"] >= 6:
            content += """⚠️ **Good Resource Management with Minor Issues**
- Resource management is generally effective
- Some minor optimizations recommended
- Review specific test failures for improvements
"""
        else:
            content += """❌ **Resource Management Needs Improvement**
- Critical issues detected in resource management
- Immediate attention required for production readiness
- Review all failed tests and implement fixes
"""

        content += f"""

## Next Steps

1. Address any identified resource leaks
2. Optimize token allocation efficiency
3. Review memory usage patterns under load
4. Implement recommended improvements
5. Re-run validation after fixes

---
*Generated by Resource Management Validator*
"""

        md_file.write_text(content)
        logger.info(f"Markdown report saved to: {md_file}")


async def main():
    """Main entry point for validation"""
    output_dir = Path("resource_validation_results")

    validator = ResourceManagementValidator(output_dir)

    logger.info("=" * 60)
    logger.info("RESOURCE MANAGEMENT VALIDATION")
    logger.info("=" * 60)

    summary = await validator.run_all_tests()

    logger.info("=" * 60)
    logger.info(f"Validation Complete!")
    logger.info(f"Overall Score: {summary['overall_score']:.1f}/10")
    logger.info(f"Status: {summary['status']}")
    logger.info(f"Report saved to: {output_dir}")
    logger.info("=" * 60)

    return 0 if summary["status"] == "PASSED" else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
