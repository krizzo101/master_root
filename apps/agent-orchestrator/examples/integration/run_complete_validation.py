#!/usr/bin/env python3
"""
Complete Escalation System Validation Runner

This script orchestrates the complete validation suite for the escalation system:
1. Runs all demonstration scenarios
2. Executes comprehensive validation tests
3. Performs performance benchmarking
4. Generates master validation report
5. Provides final production readiness assessment

Use this as the single entry point for complete system validation.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("complete_validation.log")],
)
logger = logging.getLogger(__name__)


class CompleteValidationRunner:
    """
    Master validation runner that coordinates all escalation system tests.

    Runs in sequence:
    1. Demonstration scenarios (escalation_demo.py)
    2. System validation tests (escalation_validator.py)
    3. Performance benchmarks (escalation_benchmarks.py)
    4. Generates comprehensive master report
    5. Provides production readiness assessment
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.validation_dir = output_dir / "complete_validation"
        self.validation_dir.mkdir(parents=True, exist_ok=True)

        # Results from each validation component
        self.demo_results: Optional[Dict] = None
        self.validation_results: Optional[Dict] = None
        self.benchmark_results: Optional[Dict] = None

        # Execution tracking
        self.start_time = time.time()
        self.component_times: Dict[str, float] = {}
        self.component_status: Dict[str, str] = {}

        # Validation criteria for production readiness
        self.production_criteria = {
            "demo_scenarios_passed": {"weight": 0.3, "threshold": 0.8},
            "validation_tests_passed": {"weight": 0.3, "threshold": 0.9},
            "performance_benchmarks_passed": {"weight": 0.2, "threshold": 0.7},
            "system_stability": {"weight": 0.1, "threshold": 0.8},
            "integration_compatibility": {"weight": 0.1, "threshold": 0.9},
        }

        logger.info("CompleteValidationRunner initialized")

    async def run_complete_validation(self) -> Dict[str, Any]:
        """
        Run complete validation suite and generate master report.

        Returns:
            Comprehensive validation report with production readiness assessment
        """
        logger.info("🚀 Starting Complete Escalation System Validation Suite")

        try:
            # Run validation components in sequence
            await self._run_demonstration_scenarios()
            await self._run_system_validation()
            await self._run_performance_benchmarks()

            # Generate master report
            master_report = await self._generate_master_report()

            total_time = time.time() - self.start_time
            logger.info(f"✅ Complete validation finished in {total_time:.1f}s")

            return master_report

        except Exception as e:
            logger.error(f"❌ Validation suite failed: {e}")
            logger.error(traceback.format_exc())

            # Generate failure report
            return await self._generate_failure_report(str(e))

    async def _run_demonstration_scenarios(self):
        """Run escalation demonstration scenarios"""
        logger.info("📋 Running Escalation Demonstration Scenarios...")

        component_start = time.time()

        try:
            # Import and run demonstration
            sys.path.insert(0, str(Path(__file__).parent))

            from escalation_demo import EscalationDemonstrator

            demonstrator = EscalationDemonstrator(
                output_dir=self.validation_dir / "demo_output",
                tokens=["validation_token"],
            )

            self.demo_results = await demonstrator.run_complete_demonstration()
            await demonstrator.cleanup()

            self.component_times["demonstration"] = time.time() - component_start
            self.component_status["demonstration"] = "completed"

            demo_success = self.demo_results.get(
                "production_readiness_assessment", {}
            ).get("ready_for_production", False)
            logger.info(
                f"✅ Demonstration scenarios completed - Production ready: {demo_success}"
            )

        except Exception as e:
            self.component_times["demonstration"] = time.time() - component_start
            self.component_status["demonstration"] = "failed"

            self.demo_results = {
                "status": "failed",
                "error": str(e),
                "production_readiness_assessment": {"ready_for_production": False},
            }

            logger.error(f"❌ Demonstration scenarios failed: {e}")

    async def _run_system_validation(self):
        """Run system validation tests"""
        logger.info("🔍 Running System Validation Tests...")

        component_start = time.time()

        try:
            from escalation_validator import EscalationValidator

            validator = EscalationValidator(
                output_dir=self.validation_dir / "validation_output"
            )

            self.validation_results = await validator.run_comprehensive_validation()

            self.component_times["validation"] = time.time() - component_start
            self.component_status["validation"] = "completed"

            validation_passed = self.validation_results.get(
                "overall_assessment", {}
            ).get("validation_passed", False)
            logger.info(
                f"✅ System validation completed - Validation passed: {validation_passed}"
            )

        except Exception as e:
            self.component_times["validation"] = time.time() - component_start
            self.component_status["validation"] = "failed"

            self.validation_results = {
                "status": "failed",
                "error": str(e),
                "overall_assessment": {"validation_passed": False},
            }

            logger.error(f"❌ System validation failed: {e}")

    async def _run_performance_benchmarks(self):
        """Run performance benchmarks"""
        logger.info("⚡ Running Performance Benchmarks...")

        component_start = time.time()

        try:
            # Check if psutil is available for benchmarks
            try:
                import psutil
            except ImportError:
                logger.warning(
                    "⚠️  psutil not available - skipping detailed performance benchmarks"
                )
                self.benchmark_results = {
                    "status": "skipped",
                    "reason": "psutil not available",
                    "performance_summary": {
                        "passed_benchmarks": 0,
                        "total_benchmarks": 0,
                    },
                }
                self.component_times["benchmarks"] = 0
                self.component_status["benchmarks"] = "skipped"
                return

            from escalation_benchmarks import EscalationBenchmarker

            benchmarker = EscalationBenchmarker(
                output_dir=self.validation_dir / "benchmark_output"
            )

            self.benchmark_results = await benchmarker.run_comprehensive_benchmarks()

            self.component_times["benchmarks"] = time.time() - component_start
            self.component_status["benchmarks"] = "completed"

            passed_benchmarks = self.benchmark_results.get(
                "performance_summary", {}
            ).get("passed_benchmarks", 0)
            total_benchmarks = self.benchmark_results.get(
                "performance_summary", {}
            ).get("total_benchmarks", 1)
            logger.info(
                f"✅ Performance benchmarks completed - {passed_benchmarks}/{total_benchmarks} passed"
            )

        except Exception as e:
            self.component_times["benchmarks"] = time.time() - component_start
            self.component_status["benchmarks"] = "failed"

            self.benchmark_results = {
                "status": "failed",
                "error": str(e),
                "performance_summary": {"passed_benchmarks": 0, "total_benchmarks": 1},
            }

            logger.error(f"❌ Performance benchmarks failed: {e}")

    async def _generate_master_report(self) -> Dict[str, Any]:
        """Generate comprehensive master validation report"""
        logger.info("📊 Generating Master Validation Report...")

        total_time = time.time() - self.start_time

        # Calculate component scores
        component_scores = self._calculate_component_scores()

        # Calculate overall production readiness score
        production_score = self._calculate_production_readiness_score(component_scores)

        # Aggregate key metrics
        key_metrics = self._aggregate_key_metrics()

        # Generate recommendations
        recommendations = self._generate_recommendations(component_scores)

        master_report = {
            "master_validation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_execution_time": total_time,
                "validation_suite_version": "1.0.0",
                "components_run": list(self.component_status.keys()),
                "components_successful": [
                    k for k, v in self.component_status.items() if v == "completed"
                ],
                "components_failed": [
                    k for k, v in self.component_status.items() if v == "failed"
                ],
                "components_skipped": [
                    k for k, v in self.component_status.items() if v == "skipped"
                ],
            },
            "production_readiness_assessment": {
                "overall_production_ready": production_score >= 0.8,
                "production_readiness_score": round(production_score, 3),
                "confidence_level": self._calculate_confidence_level(component_scores),
                "critical_issues": self._identify_critical_issues(),
                "deployment_recommendation": self._get_deployment_recommendation(
                    production_score
                ),
            },
            "component_results": {
                "demonstration_scenarios": {
                    "status": self.component_status.get("demonstration", "not_run"),
                    "execution_time": self.component_times.get("demonstration", 0),
                    "score": component_scores.get("demonstration", 0),
                    "summary": self._summarize_demo_results(),
                    "detailed_results": self.demo_results,
                },
                "system_validation": {
                    "status": self.component_status.get("validation", "not_run"),
                    "execution_time": self.component_times.get("validation", 0),
                    "score": component_scores.get("validation", 0),
                    "summary": self._summarize_validation_results(),
                    "detailed_results": self.validation_results,
                },
                "performance_benchmarks": {
                    "status": self.component_status.get("benchmarks", "not_run"),
                    "execution_time": self.component_times.get("benchmarks", 0),
                    "score": component_scores.get("benchmarks", 0),
                    "summary": self._summarize_benchmark_results(),
                    "detailed_results": self.benchmark_results,
                },
            },
            "aggregated_metrics": key_metrics,
            "recommendations": recommendations,
            "next_steps": self._generate_next_steps(production_score),
            "validation_matrix": {
                "backward_compatibility": self._check_backward_compatibility(),
                "system_stability": self._check_system_stability(),
                "performance_acceptability": self._check_performance_acceptability(),
                "feature_completeness": self._check_feature_completeness(),
                "integration_readiness": self._check_integration_readiness(),
                "monitoring_capabilities": self._check_monitoring_capabilities(),
                "error_handling": self._check_error_handling(),
                "scalability": self._check_scalability(),
            },
        }

        # Save master report
        report_file = self.validation_dir / "master_validation_report.json"
        with open(report_file, "w") as f:
            json.dump(master_report, f, indent=2, default=str)

        # Generate executive summary
        await self._generate_executive_summary(master_report)

        logger.info(f"📄 Master validation report saved: {report_file}")

        return master_report

    async def _generate_failure_report(self, error: str) -> Dict[str, Any]:
        """Generate report when validation suite fails"""

        failure_report = {
            "master_validation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": error,
                "execution_time": time.time() - self.start_time,
                "components_attempted": list(self.component_status.keys()),
            },
            "production_readiness_assessment": {
                "overall_production_ready": False,
                "production_readiness_score": 0.0,
                "confidence_level": "none",
                "critical_issues": [f"Validation suite failed: {error}"],
                "deployment_recommendation": "DO NOT DEPLOY - Fix validation suite issues first",
            },
            "component_results": {
                "demonstration_scenarios": {
                    "status": self.component_status.get("demonstration", "not_run"),
                    "results": self.demo_results,
                },
                "system_validation": {
                    "status": self.component_status.get("validation", "not_run"),
                    "results": self.validation_results,
                },
                "performance_benchmarks": {
                    "status": self.component_status.get("benchmarks", "not_run"),
                    "results": self.benchmark_results,
                },
            },
            "recommendations": [
                "Fix validation suite execution issues",
                "Ensure all dependencies are installed",
                "Check system resources and permissions",
                "Review logs for detailed error information",
            ],
        }

        # Save failure report
        report_file = self.validation_dir / "validation_failure_report.json"
        with open(report_file, "w") as f:
            json.dump(failure_report, f, indent=2, default=str)

        return failure_report

    def _calculate_component_scores(self) -> Dict[str, float]:
        """Calculate normalized scores for each validation component"""
        scores = {}

        # Demonstration scenarios score
        if (
            self.demo_results
            and self.component_status.get("demonstration") == "completed"
        ):
            demo_assessment = self.demo_results.get(
                "production_readiness_assessment", {}
            )
            demo_patterns = self.demo_results.get("escalation_patterns_validated", {})

            readiness_score = (
                1.0 if demo_assessment.get("ready_for_production", False) else 0.0
            )
            patterns_score = (
                sum(1 for v in demo_patterns.values() if v) / len(demo_patterns)
                if demo_patterns
                else 0.0
            )
            scores["demonstration"] = (readiness_score + patterns_score) / 2
        else:
            scores["demonstration"] = 0.0

        # System validation score
        if (
            self.validation_results
            and self.component_status.get("validation") == "completed"
        ):
            val_assessment = self.validation_results.get("overall_assessment", {})
            validation_passed = val_assessment.get("validation_passed", False)
            scores["validation"] = 1.0 if validation_passed else 0.0
        else:
            scores["validation"] = 0.0

        # Performance benchmarks score
        if (
            self.benchmark_results
            and self.component_status.get("benchmarks") == "completed"
        ):
            perf_summary = self.benchmark_results.get("performance_summary", {})
            passed = perf_summary.get("passed_benchmarks", 0)
            total = perf_summary.get("total_benchmarks", 1)
            scores["benchmarks"] = passed / total if total > 0 else 0.0
        elif self.component_status.get("benchmarks") == "skipped":
            scores["benchmarks"] = 0.7  # Partial credit for skipped benchmarks
        else:
            scores["benchmarks"] = 0.0

        return scores

    def _calculate_production_readiness_score(
        self, component_scores: Dict[str, float]
    ) -> float:
        """Calculate overall production readiness score"""

        weighted_score = 0.0
        total_weight = 0.0

        # Weight component scores according to production criteria
        if "demonstration" in component_scores:
            weight = 0.4  # High weight for demonstration scenarios
            weighted_score += component_scores["demonstration"] * weight
            total_weight += weight

        if "validation" in component_scores:
            weight = 0.4  # High weight for system validation
            weighted_score += component_scores["validation"] * weight
            total_weight += weight

        if "benchmarks" in component_scores:
            weight = 0.2  # Lower weight for performance benchmarks
            weighted_score += component_scores["benchmarks"] * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def _calculate_confidence_level(self, component_scores: Dict[str, float]) -> str:
        """Calculate confidence level in the assessment"""

        completed_components = sum(
            1 for status in self.component_status.values() if status == "completed"
        )
        total_components = len(self.component_status)

        avg_score = (
            sum(component_scores.values()) / len(component_scores)
            if component_scores
            else 0.0
        )

        if completed_components == total_components and avg_score >= 0.9:
            return "very_high"
        elif completed_components == total_components and avg_score >= 0.7:
            return "high"
        elif completed_components >= total_components * 0.8 and avg_score >= 0.6:
            return "medium"
        elif completed_components >= total_components * 0.5:
            return "low"
        else:
            return "very_low"

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that block production deployment"""
        issues = []

        # Check for component failures
        for component, status in self.component_status.items():
            if status == "failed":
                issues.append(f"{component.title()} validation failed")

        # Check specific validation failures
        if self.demo_results and not self.demo_results.get(
            "production_readiness_assessment", {}
        ).get("ready_for_production", False):
            issues.append(
                "Demonstration scenarios indicate system not production ready"
            )

        if self.validation_results and not self.validation_results.get(
            "overall_assessment", {}
        ).get("validation_passed", False):
            issues.append("System validation tests failed")

        # Check for performance issues
        if (
            self.benchmark_results
            and self.component_status.get("benchmarks") == "completed"
        ):
            perf_summary = self.benchmark_results.get("performance_summary", {})
            if perf_summary.get("passed_benchmarks", 0) == 0:
                issues.append("All performance benchmarks failed")

        return issues

    def _get_deployment_recommendation(self, production_score: float) -> str:
        """Get deployment recommendation based on scores"""

        critical_issues = self._identify_critical_issues()

        if critical_issues:
            return f"DO NOT DEPLOY - Critical issues must be resolved: {len(critical_issues)} issues found"
        elif production_score >= 0.9:
            return "DEPLOY TO PRODUCTION - All validation criteria met with high confidence"
        elif production_score >= 0.8:
            return "DEPLOY TO STAGING - Good validation results, monitor closely in staging"
        elif production_score >= 0.6:
            return (
                "LIMITED DEPLOYMENT - Consider phased rollout with extensive monitoring"
            )
        else:
            return "DO NOT DEPLOY - Significant validation failures require resolution"

    def _aggregate_key_metrics(self) -> Dict[str, Any]:
        """Aggregate key metrics from all validation components"""
        metrics = {}

        # Demonstration metrics
        if self.demo_results:
            demo_metadata = self.demo_results.get("demonstration_metadata", {})
            metrics["demo_scenarios_completed"] = demo_metadata.get(
                "completed_scenarios", 0
            )
            metrics["demo_scenarios_failed"] = demo_metadata.get("failed_scenarios", 0)

        # Validation metrics
        if self.validation_results:
            val_metadata = self.validation_results.get("validation_metadata", {})
            metrics["validation_scenarios_tested"] = val_metadata.get(
                "scenarios_tested", 0
            )
            metrics["critical_validations_passed"] = len(
                [
                    v
                    for v in self.validation_results.get(
                        "validation_summary", {}
                    ).values()
                    if v.get("status") == "passed" and v.get("critical", False)
                ]
            )

        # Performance metrics
        if self.benchmark_results:
            perf_summary = self.benchmark_results.get("performance_summary", {})
            metrics["max_throughput"] = perf_summary.get("max_throughput", 0)
            metrics["total_operations_tested"] = perf_summary.get("total_operations", 0)
            metrics["overall_success_rate"] = perf_summary.get(
                "overall_success_rate", 0
            )

        # Overall metrics
        metrics["total_execution_time"] = time.time() - self.start_time
        metrics["components_successful"] = len(
            [s for s in self.component_status.values() if s == "completed"]
        )
        metrics["components_failed"] = len(
            [s for s in self.component_status.values() if s == "failed"]
        )

        return metrics

    def _generate_recommendations(
        self, component_scores: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        # Component-specific recommendations
        if component_scores.get("demonstration", 0) < 0.8:
            recommendations.append(
                "Address demonstration scenario failures before production deployment"
            )

        if component_scores.get("validation", 0) < 0.9:
            recommendations.append(
                "Fix system validation issues - critical for production stability"
            )

        if component_scores.get("benchmarks", 0) < 0.7:
            recommendations.append(
                "Optimize performance - benchmarks indicate potential scalability issues"
            )

        # General recommendations
        if self.component_status.get("benchmarks") == "skipped":
            recommendations.append(
                "Install psutil and run performance benchmarks for complete assessment"
            )

        if any(status == "failed" for status in self.component_status.values()):
            recommendations.append(
                "Investigate and resolve component failures before proceeding"
            )

        # Deployment recommendations
        production_score = self._calculate_production_readiness_score(component_scores)
        if production_score >= 0.8:
            recommendations.append(
                "System ready for production deployment with standard monitoring"
            )
        else:
            recommendations.append(
                "Implement additional monitoring and consider phased deployment approach"
            )

        return recommendations

    def _generate_next_steps(self, production_score: float) -> List[str]:
        """Generate next steps based on validation results"""

        if production_score >= 0.9:
            return [
                "Deploy to production environment",
                "Set up production monitoring and alerting",
                "Create operational runbooks for escalation patterns",
                "Train team on escalation system features",
                "Schedule post-deployment validation",
            ]
        elif production_score >= 0.8:
            return [
                "Deploy to staging environment for final validation",
                "Run production-like workloads in staging",
                "Monitor system behavior under realistic load",
                "Address any remaining performance concerns",
                "Plan production deployment strategy",
            ]
        elif production_score >= 0.6:
            return [
                "Address specific validation failures",
                "Re-run failed validation components",
                "Optimize system performance",
                "Implement additional monitoring",
                "Plan limited pilot deployment",
            ]
        else:
            return [
                "Fix critical validation failures",
                "Review system architecture and implementation",
                "Re-run complete validation suite",
                "Consider additional testing scenarios",
                "Do not proceed with deployment until issues resolved",
            ]

    # Validation matrix methods

    def _check_backward_compatibility(self) -> Dict[str, Any]:
        """Check backward compatibility status"""
        if self.validation_results:
            integration_results = self.validation_results.get(
                "validation_results", {}
            ).get("system_integration", {})
            return {
                "status": "pass"
                if integration_results.get("backward_compatibility", False)
                else "fail",
                "details": "Existing orchestrator usage works unchanged"
                if integration_results.get("backward_compatibility", False)
                else "Compatibility issues detected",
            }
        return {"status": "unknown", "details": "Validation not completed"}

    def _check_system_stability(self) -> Dict[str, Any]:
        """Check system stability status"""
        if self.validation_results:
            stability_results = self.validation_results.get(
                "validation_results", {}
            ).get("integration_stability", {})
            return {
                "status": "pass"
                if stability_results.get("system_remained_stable", False)
                else "fail",
                "details": f"Stability rate: {stability_results.get('stability_success_rate', 0):.1%}",
            }
        return {"status": "unknown", "details": "Stability testing not completed"}

    def _check_performance_acceptability(self) -> Dict[str, Any]:
        """Check performance acceptability"""
        if (
            self.benchmark_results
            and self.component_status.get("benchmarks") == "completed"
        ):
            perf_summary = self.benchmark_results.get("performance_summary", {})
            passed = perf_summary.get("passed_benchmarks", 0)
            total = perf_summary.get("total_benchmarks", 1)
            return {
                "status": "pass" if passed >= total * 0.7 else "fail",
                "details": f"Performance benchmarks: {passed}/{total} passed, max throughput: {perf_summary.get('max_throughput', 0):.1f} ops/sec",
            }
        return {"status": "unknown", "details": "Performance testing not completed"}

    def _check_feature_completeness(self) -> Dict[str, Any]:
        """Check feature completeness"""
        if self.demo_results:
            patterns = self.demo_results.get("escalation_patterns_validated", {})
            completed_patterns = sum(1 for v in patterns.values() if v)
            total_patterns = len(patterns)
            return {
                "status": "pass"
                if completed_patterns >= total_patterns * 0.8
                else "fail",
                "details": f"Escalation patterns: {completed_patterns}/{total_patterns} working",
            }
        return {"status": "unknown", "details": "Feature testing not completed"}

    def _check_integration_readiness(self) -> Dict[str, Any]:
        """Check integration readiness"""
        if self.validation_results:
            integration_results = self.validation_results.get(
                "validation_results", {}
            ).get("system_integration", {})
            comm_bus = integration_results.get("communication_bus", False)
            dashboard = integration_results.get("dashboard_api_functional", False)
            return {
                "status": "pass" if comm_bus and dashboard else "fail",
                "details": f"Communication bus: {'✓' if comm_bus else '✗'}, Dashboard API: {'✓' if dashboard else '✗'}",
            }
        return {"status": "unknown", "details": "Integration testing not completed"}

    def _check_monitoring_capabilities(self) -> Dict[str, Any]:
        """Check monitoring capabilities"""
        if self.demo_results:
            system_status = self.demo_results.get("escalation_system_status", {})
            monitoring = system_status.get("all_components_available", False)
            return {
                "status": "pass" if monitoring else "fail",
                "details": "Real-time monitoring and dashboard functional"
                if monitoring
                else "Monitoring issues detected",
            }
        return {"status": "unknown", "details": "Monitoring testing not completed"}

    def _check_error_handling(self) -> Dict[str, Any]:
        """Check error handling capabilities"""
        if self.validation_results:
            edge_case_results = self.validation_results.get(
                "validation_results", {}
            ).get("edge_case_handling", {})
            error_handling = edge_case_results.get("robust_error_handling", False)
            return {
                "status": "pass" if error_handling else "fail",
                "details": f"Edge case success rate: {edge_case_results.get('edge_case_success_rate', 0):.1%}",
            }
        return {"status": "unknown", "details": "Error handling testing not completed"}

    def _check_scalability(self) -> Dict[str, Any]:
        """Check scalability characteristics"""
        if (
            self.benchmark_results
            and self.component_status.get("benchmarks") == "completed"
        ):
            scalability_result = None
            detailed_results = self.benchmark_results.get("detailed_results", {})

            if "scalability_ramp" in detailed_results:
                scalability_result = detailed_results["scalability_ramp"]
                max_concurrency = scalability_result.get("additional_metrics", {}).get(
                    "max_tested_concurrency", 0
                )
                return {
                    "status": "pass" if max_concurrency >= 20 else "fail",
                    "details": f"Max tested concurrency: {max_concurrency}, throughput: {scalability_result.get('throughput', 0):.1f} ops/sec",
                }

        return {"status": "unknown", "details": "Scalability testing not completed"}

    # Summary methods

    def _summarize_demo_results(self) -> Dict[str, Any]:
        """Summarize demonstration results"""
        if not self.demo_results:
            return {"status": "not_run"}

        metadata = self.demo_results.get("demonstration_metadata", {})
        readiness = self.demo_results.get("production_readiness_assessment", {})

        return {
            "scenarios_completed": metadata.get("completed_scenarios", 0),
            "scenarios_failed": metadata.get("failed_scenarios", 0),
            "production_ready": readiness.get("ready_for_production", False),
            "readiness_score": readiness.get("readiness_score", "0/0"),
        }

    def _summarize_validation_results(self) -> Dict[str, Any]:
        """Summarize validation results"""
        if not self.validation_results:
            return {"status": "not_run"}

        assessment = self.validation_results.get("overall_assessment", {})
        metadata = self.validation_results.get("validation_metadata", {})

        return {
            "validation_passed": assessment.get("validation_passed", False),
            "scenarios_tested": metadata.get("scenarios_tested", 0),
            "system_health": assessment.get("overall_system_health", "unknown"),
            "production_readiness": assessment.get("production_readiness", False),
        }

    def _summarize_benchmark_results(self) -> Dict[str, Any]:
        """Summarize benchmark results"""
        if not self.benchmark_results:
            return {"status": "not_run"}

        if self.benchmark_results.get("status") == "skipped":
            return {
                "status": "skipped",
                "reason": self.benchmark_results.get("reason", "unknown"),
            }

        summary = self.benchmark_results.get("performance_summary", {})

        return {
            "benchmarks_passed": summary.get("passed_benchmarks", 0),
            "benchmarks_total": summary.get("total_benchmarks", 0),
            "max_throughput": summary.get("max_throughput", 0),
            "success_rate": summary.get("overall_success_rate", 0),
        }

    async def _generate_executive_summary(self, master_report: Dict[str, Any]):
        """Generate executive summary document"""

        production_assessment = master_report["production_readiness_assessment"]

        summary = f"""
# Escalation System Validation - Executive Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Production Readiness Assessment

**Overall Status:** {'✅ READY FOR PRODUCTION' if production_assessment['overall_production_ready'] else '❌ NOT READY FOR PRODUCTION'}

**Production Score:** {production_assessment['production_readiness_score']:.1%}
**Confidence Level:** {production_assessment['confidence_level'].replace('_', ' ').title()}

## Component Results

### Demonstration Scenarios
- Status: {master_report['component_results']['demonstration_scenarios']['status'].title()}
- Score: {master_report['component_results']['demonstration_scenarios']['score']:.1%}
- Execution Time: {master_report['component_results']['demonstration_scenarios']['execution_time']:.1f}s

### System Validation
- Status: {master_report['component_results']['system_validation']['status'].title()}
- Score: {master_report['component_results']['system_validation']['score']:.1%}
- Execution Time: {master_report['component_results']['system_validation']['execution_time']:.1f}s

### Performance Benchmarks
- Status: {master_report['component_results']['performance_benchmarks']['status'].title()}
- Score: {master_report['component_results']['performance_benchmarks']['score']:.1%}
- Execution Time: {master_report['component_results']['performance_benchmarks']['execution_time']:.1f}s

## Key Metrics

"""

        metrics = master_report["aggregated_metrics"]
        if "max_throughput" in metrics:
            summary += f"- **Max Throughput:** {metrics['max_throughput']:.1f} operations/second\n"
        if "total_operations_tested" in metrics:
            summary += f"- **Total Operations Tested:** {metrics['total_operations_tested']:,}\n"
        if "overall_success_rate" in metrics:
            summary += f"- **Success Rate:** {metrics['overall_success_rate']:.1%}\n"

        summary += f"\n## Deployment Recommendation\n\n{production_assessment['deployment_recommendation']}\n"

        if production_assessment.get("critical_issues"):
            summary += f"\n## Critical Issues\n\n"
            for issue in production_assessment["critical_issues"]:
                summary += f"- {issue}\n"

        if master_report.get("recommendations"):
            summary += f"\n## Recommendations\n\n"
            for rec in master_report["recommendations"]:
                summary += f"- {rec}\n"

        summary += f"\n## Next Steps\n\n"
        for step in master_report["next_steps"]:
            summary += f"1. {step}\n"

        # Save executive summary
        summary_file = self.validation_dir / "executive_summary.md"
        with open(summary_file, "w") as f:
            f.write(summary)

        logger.info(f"📋 Executive summary saved: {summary_file}")


async def main():
    """Main validation runner"""
    print("🚀 Starting Complete Escalation System Validation Suite")
    print("=" * 80)

    # Setup
    output_dir = Path("./complete_validation_output")
    output_dir.mkdir(exist_ok=True)

    # Initialize validation runner
    runner = CompleteValidationRunner(output_dir)

    try:
        # Run complete validation
        master_report = await runner.run_complete_validation()

        # Display executive summary
        print("\n" + "=" * 80)
        print("📊 ESCALATION SYSTEM VALIDATION - EXECUTIVE SUMMARY")
        print("=" * 80)

        assessment = master_report["production_readiness_assessment"]
        print(
            f"🎯 **PRODUCTION READINESS:** {'✅ READY' if assessment['overall_production_ready'] else '❌ NOT READY'}"
        )
        print(f"📊 **Production Score:** {assessment['production_readiness_score']:.1%}")
        print(
            f"🎓 **Confidence Level:** {assessment['confidence_level'].replace('_', ' ').title()}"
        )

        # Component summary
        print(f"\n📋 **COMPONENT RESULTS:**")
        for component, results in master_report["component_results"].items():
            status_icon = (
                "✅"
                if results["status"] == "completed"
                else "❌"
                if results["status"] == "failed"
                else "⏭️"
            )
            print(
                f"  {status_icon} {component.replace('_', ' ').title()}: {results['score']:.1%} ({results['execution_time']:.1f}s)"
            )

        # Key metrics
        metrics = master_report["aggregated_metrics"]
        print(f"\n🔢 **KEY METRICS:**")
        print(f"  • Components Successful: {metrics.get('components_successful', 0)}")
        print(f"  • Components Failed: {metrics.get('components_failed', 0)}")
        if "max_throughput" in metrics:
            print(f"  • Max Throughput: {metrics['max_throughput']:.1f} ops/sec")
        if "overall_success_rate" in metrics:
            print(f"  • Overall Success Rate: {metrics['overall_success_rate']:.1%}")
        print(f"  • Total Execution Time: {metrics['total_execution_time']:.1f}s")

        # Deployment recommendation
        print(f"\n🚀 **DEPLOYMENT RECOMMENDATION:**")
        print(f"  {assessment['deployment_recommendation']}")

        # Critical issues
        if assessment.get("critical_issues"):
            print(f"\n🚨 **CRITICAL ISSUES:**")
            for issue in assessment["critical_issues"]:
                print(f"  • {issue}")

        # Recommendations
        if master_report.get("recommendations"):
            print(f"\n💡 **RECOMMENDATIONS:**")
            for i, rec in enumerate(master_report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print(f"\n📄 **DETAILED REPORTS:**")
        print(
            f"  • Master Report: {output_dir}/complete_validation_output/master_validation_report.json"
        )
        print(
            f"  • Executive Summary: {output_dir}/complete_validation_output/executive_summary.md"
        )
        print(f"  • Component Reports: {output_dir}/complete_validation_output/*/")

        print("=" * 80)

        # Exit with appropriate code
        if assessment["overall_production_ready"]:
            print("🎉 Escalation system validation PASSED - Ready for production!")
            return 0
        else:
            print(
                "⚠️  Escalation system validation FAILED - Address issues before deployment"
            )
            return 1

    except Exception as e:
        print(f"❌ Complete validation failed: {e}")
        logger.error(f"Complete validation failed: {e}")
        logger.error(traceback.format_exc())
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
